import os
import time
import logging
import json
import csv
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from .models import ProcessedFileData
import config  # assuming this contains your GOOGLE_CREDENTIALS_PATH

logger = logging.getLogger(__name__)

# Load Google Service Account credentials
SERVICE_ACCOUNT_FILE = config.GOOGLE_CREDENTIALS_PATH  # Adjust to your credentials file path
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE,
    scopes=['https://www.googleapis.com/auth/drive.file']
)
drive_service = build('drive', 'v3', credentials=credentials)

MAX_RETRIES = 3

@csrf_exempt
def upload_file(request):
    if request.method == 'POST':
        if request.FILES.get('file'):
            try:
                # Extract username from request
                username = request.POST.get('username', None)
                if not username:
                    return JsonResponse({'status': 'error', 'message': 'Username is required'}, status=400)

                logger.info(f"Username provided: {username}")

                # Get the uploaded file
                uploaded_file = request.FILES['file']
                file_name = uploaded_file.name
                logger.info(f"Received file: {file_name}")

                # Save the file to /tmp directory manually
                file_path = os.path.join('/tmp', file_name)
                with open(file_path, 'wb+') as destination:
                    for chunk in uploaded_file.chunks():
                        destination.write(chunk)
                logger.info(f"File saved at: {file_path}")

                # (Optional) Open the file for processing if needed
                # with open(file_path, 'r', encoding='utf-8') as file:
                #     logger.info("Attempting to read the CSV file")
                #     content = file.read()  # if processing is needed

                # Retry logic for uploading to Google Drive
                for attempt in range(MAX_RETRIES):
                    try:
                        file_metadata = {'name': file_name}
                        media = MediaFileUpload(file_path, mimetype='text/csv')
                        uploaded_drive_file = drive_service.files().create(
                            body=file_metadata,
                            media_body=media,
                            fields='id, webViewLink'
                        ).execute()
                        # Successful upload; break out of the retry loop
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
                    processed=False,
                    username=username
                )
                file_data.save()

                # Clean up: remove the file from the local filesystem after uploading
                os.remove(file_path)
                logger.info(f"Local file deleted: {file_path}")

                # Send a success response back to the frontend
                return JsonResponse({
                    'status': 'success',
                    'message': 'File uploaded and processed successfully',
                    'file_id': file_id,
                    'file_url': file_url
                }, status=200)

            except Exception as e:
                logger.error(f"Error during file processing: {str(e)}")
                return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
        else:
            logger.error("No file provided in the request")
            return JsonResponse({'status': 'error', 'message': 'No file provided'}, status=400)


   
@csrf_exempt
def fetch_files(request):
    if request.method == 'POST':
        try:
            # Decode the request body
            logger.info(f"Fetch request body: {request.body.decode('utf-8')}")
            body = json.loads(request.body)
            file_url = body.get('file_url')
            file_type = body.get('file_type')

            if not file_url or not file_type:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Missing required parameters'
                }, status=400)

            # Fetch file from the database
            try:
                file_data = ProcessedFileData.objects.get(file_url=file_url)
                logger.info(f"Found file in database: {file_data.file_id}")
            except ProcessedFileData.DoesNotExist:
                return JsonResponse({
                    'status': 'error',
                    'message': 'File not found in database'
                }, status=404)

            # Attempt to fetch file from Google Drive once
            try:
                request = drive_service.files().get_media(fileId=file_data.file_id)
                file_content = request.execute()
                content = file_content.decode('utf-8')
                logger.info("Successfully retrieved file content from Drive")
            except HttpError as e:
                logger.warning(f"Google Drive API error: {e}. Retrying once...")
                time.sleep(2)  # Small delay before retrying

                # Retry once if the first attempt failed
                try:
                    request = drive_service.files().get_media(fileId=file_data.file_id)
                    file_content = request.execute()
                    content = file_content.decode('utf-8')
                    logger.info("Successfully retrieved file content from Drive on retry")
                except HttpError as retry_e:
                    logger.error(f"Google Drive API failed again: {retry_e}")
                    return JsonResponse({
                        'status': 'error',
                        'message': f'Failed to fetch file from Drive: {retry_e}'
                    }, status=500)
            except Exception as e:
                logger.error(f"Unexpected error while fetching file: {e}")
                return JsonResponse({
                    'status': 'error',
                    'message': f'Unexpected error: {e}'
                }, status=500)

            # Process file based on file type
            if file_type == 'csv':
                csv_data = []
                lines = content.strip().split('\n')
                reader = csv.reader(lines)
                for row in reader:
                    csv_data.append(row)
                return JsonResponse({'status': 'success', 'csv_content': csv_data})

            elif file_type == 'json':
                json_data = json.loads(content)
                return JsonResponse({'status': 'success', 'json_content': json_data})

            elif file_type == 'xml':
                return JsonResponse({'status': 'success', 'xml_content': content})

            else:
                return JsonResponse({'status': 'success', 'text_content': content})

        except Exception as e:
            logger.error(f"Error processing file: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': f'Failed to process file: {str(e)}'
            }, status=500)

    return JsonResponse({
        'status': 'error',
        'message': 'Method not allowed'
    }, status=405)
