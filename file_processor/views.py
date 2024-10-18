import csv
import logging
import os
from pathlib import Path
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from .models import ProcessedFileData
import config

logger = logging.getLogger(__name__)

# Set up Google Drive credentials
SERVICE_ACCOUNT_FILE = config.GOOGLE_CREDENTIALS_PATH

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE,
    scopes=['https://www.googleapis.com/auth/drive.file']
)
drive_service = build('drive', 'v3', credentials=credentials)

@csrf_exempt
def upload_file(request):
    if request.method == 'POST':
        if request.FILES.get('file'):
            try:
                uploaded_file = request.FILES['file']
                logger.info(f"Received file: {uploaded_file.name}")

                # Save the file temporarily
                file_path = os.path.join('/tmp', uploaded_file.name)
                with open(file_path, 'wb+') as destination:
                    for chunk in uploaded_file.chunks():
                        destination.write(chunk)
                logger.info(f"File saved at: {file_path}")

                # Upload to Google Drive
                file_metadata = {'name': uploaded_file.name}
                media = MediaFileUpload(file_path, mimetype=uploaded_file.content_type, resumable=True)

                drive_file = drive_service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id'
                ).execute()

                file_id = drive_file.get('id')
                file_url = f'https://drive.google.com/uc?id={file_id}&export=download'

                logger.info(f"File uploaded to Google Drive with ID: {file_id}")

                # Remove the file from the temporary location
                os.remove(file_path)
                logger.info(f"Temporary file deleted: {file_path}")

                # Return the file URL to the frontend
                return JsonResponse({'status': 'success', 'file_url': file_url}, status=200)

            except Exception as e:
                logger.error(f"Error during file upload or processing: {str(e)}")
                return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
        else:
            return JsonResponse({'status': 'error', 'message': 'No file provided'}, status=400)
