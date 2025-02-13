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

logger = logging.getLogger(__name__)


# Load Google Service Account credentials
SERVICE_ACCOUNT_FILE = config.GOOGLE_CREDENTIALS_PATH # Change to your credentials file path


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
                file_path = default_storage.save(file_name, uploaded_file)
                logger.info(f"File saved at: {file_path}")

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
                default_storage.delete(file_path)
                logger.info(f"Local file deleted: {file_path}")

                # Send a success response back to the frontend
                return JsonResponse({'status': 'success', 'message': 'File uploaded and processed successfully', 'file_id': file_id, 'file_url': file_url}, status=200)

            except Exception as e:
                logger.error(f"Error during file processing: {str(e)}")
                return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
        else:
            logger.error("No file provided in the request")
            return JsonResponse({'status': 'error', 'message': 'No file provided'}, status=400)
        

@csrf_exempt
def fetch_csv(request):
    if request.method == 'POST':
        try:
            # Log the request body to troubleshoot
            logger.info(f"Request body: {request.body}")

            # Parse JSON body
            body = json.loads(request.body)
            file_url = body.get('file_url')

            # Check if file_url is provided
            if not file_url:
                raise ValueError('No file_url provided')

            # Fetch the file from the provided URL
            response = requests.get(file_url)
            if response.status_code == 200:
                # Attempt to parse the CSV content
                try:
                    csv_content = []
                    decoded_content = response.content.decode('utf-8')
                    csv_reader = csv.reader(decoded_content.splitlines())
                    for row in csv_reader:
                        csv_content.append(row)
                    return JsonResponse({'status': 'success', 'csv_content': csv_content}, status=200)
                except Exception as csv_error:
                    logger.error(f"Error parsing CSV: {csv_error}")
                    return JsonResponse({'status': 'error', 'message': 'Failed to parse CSV content'}, status=400)
            else:
                return JsonResponse({'status': 'error', 'message': f'Failed to fetch CSV, HTTP status: {response.status_code}'}, status=400)
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON payload'}, status=400)
        except requests.exceptions.RequestException as req_error:
            logger.error(f"Error fetching the file: {req_error}")
            return JsonResponse({'status': 'error', 'message': 'Error fetching the file'}, status=500)
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)
