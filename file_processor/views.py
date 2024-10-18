import csv
import config
import logging
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from .models import ProcessedFileData
from django.conf import settings  # Import settings module to access settings attributes
import os

logger = logging.getLogger(__name__)

# Load Google Service Account credentials
SERVICE_ACCOUNT_FILE = config.GOOGLE_CREDENTIALS_PATH  # Change to your credentials file path

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE,
    scopes=['https://www.googleapis.com/auth/drive.file']
)
drive_service = build('drive', 'v3', credentials=credentials)

import time

MAX_RETRIES = 3

@csrf_exempt
def upload_file(request):
    if request.method == 'POST':
        if request.FILES.get('file'):
            try:
                # Get the uploaded file
                uploaded_file = request.FILES['file']
                file_name = uploaded_file.name
                logger.info(f"Received file: {file_name}")

                # Save the file temporarily in the server's filesystem
                file_path = f"/tmp/{file_name}"  # Save to /tmp directory which usually has appropriate permissions in Docker
                with open(file_path, 'wb+') as destination:
                    for chunk in uploaded_file.chunks():
                        destination.write(chunk)

                # Retry logic for uploading to Google Drive
                for attempt in range(MAX_RETRIES):
                    try:
                        # Upload the file to Google Drive
                        file_metadata = {'name': file_name}
                        media = MediaFileUpload(file_path, mimetype='text/csv')  # Adjust the mimetype if needed
                        uploaded_drive_file = drive_service.files().create(
                            body=file_metadata,
                            media_body=media,
                            fields='id, webViewLink'
                        ).execute()

                        # If successful, break out of the retry loop
                        break
                    except Exception as retry_exception:
                        logger.warning(f"Attempt {attempt + 1} failed with error: {retry_exception}")
                        if attempt < MAX_RETRIES - 1:
                            time.sleep(2 ** attempt)  # Exponential backoff
                        else:
                            raise retry_exception

                # Google Drive File ID and URL
                file_id = uploaded_drive_file.get('id')
                file_url = uploaded_drive_file.get('webViewLink')
                logger.info(f"File uploaded to Google Drive: {file_url}")

                # Save metadata in MySQL
                file_data = ProcessedFileData(
                    file_id=file_id,
                    file_name=file_name,
                    file_url=file_url,
                    processed=False  # Set this to True once the file is processed
                )
                file_data.save()

                # Clean up: remove the file from the server after uploading
                os.remove(file_path)
                logger.info(f"Local file deleted: {file_path}")

                # Send a success response back to the frontend
                return JsonResponse({'status': 'success', 'message': 'File uploaded and processed successfully', 'file_id': file_id, 'file_url': file_url}, status=200)

            except Exception as e:
                logger.error(f"Error during file processing: {str(e)}")
                return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
        else:
            logger.error("No file provided in the request")
            return JsonResponse({'status': 'error', 'message': 'No file provided'}, status=400)
