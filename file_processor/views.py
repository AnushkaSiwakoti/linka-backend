import logging
import os
from pathlib import Path
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import json
import csv
import config
import requests

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
                username = request.POST.get('username')

                if not username:
                    return JsonResponse({'status': 'error', 'message': 'Username is required'}, status=400)

                logger.info(f"Received file: {uploaded_file.name} from user: {username}")

                # Save the file temporarily
                file_path = os.path.join('/tmp', uploaded_file.name)
                with open(file_path, 'wb+') as destination:
                    for chunk in uploaded_file.chunks():
                        destination.write(chunk)

                logger.info(f"File saved at: {file_path}")

                # Read and process the CSV file
                with open(file_path, 'r') as file:
                    reader = csv.reader(file)
                    csv_data = list(reader)

                logger.info(f"CSV content: {csv_data}")

                # Upload the file to Google Drive
                file_metadata = {'name': uploaded_file.name}
                media = MediaFileUpload(file_path, mimetype='text/csv')
                drive_file = drive_service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id, webViewLink'
                ).execute()

                file_id = drive_file.get('id')
                file_url = drive_file.get('webViewLink')

                # Remove the file from the temporary location
                os.remove(file_path)
                logger.info(f"Temporary file deleted: {file_path}")

                # Save metadata to the database
                ProcessedFileData.objects.create(
                    file_id=file_id,
                    file_name=uploaded_file.name,
                    file_url=file_url,
                    processed=False,
                    username=username
                )

                # Return the CSV content to the frontend
                return JsonResponse({'status': 'success', 'csv_content': csv_data, 'file_url': file_url}, status=200)

            except Exception as e:
                logger.error(f"Error during file upload or processing: {str(e)}")
                return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
        else:
            return JsonResponse({'status': 'error', 'message': 'No file provided'}, status=400)

@csrf_exempt
def fetch_csv(request):
    if request.method == 'POST':
        try:
            # Log the request body to troubleshoot
            logger.info(f"Request body: {request.body}")
            
            body = json.loads(request.body)  # Parse JSON body
            file_url = body.get('file_url')

            # If file_url is missing or empty, raise an error
            if not file_url:
                raise ValueError('No file_url provided')

            response = requests.get(file_url)
            if response.status_code == 200:
                csv_content = response.text
                return JsonResponse({'status': 'success', 'csv_content': csv_content}, status=200)
            else:
                return JsonResponse({'status': 'error', 'message': 'Failed to fetch CSV'}, status=400)
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON payload'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)
