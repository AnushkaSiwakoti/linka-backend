# recommit
import json
import csv
import config
import requests
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

                # Save the file temporarily
                file_path = default_storage.save(file_name, uploaded_file)
                logger.info(f"File saved at: {file_path}")

                try:
                    # Upload to Google Drive with retry logic
                    for attempt in range(MAX_RETRIES):
                        try:
                            file_metadata = {'name': file_name}
                            media = MediaFileUpload(file_path, resumable=True)
                            
                            drive_file = drive_service.files().create(
                                body=file_metadata,
                                media_body=media,
                                fields='id, webViewLink'
                            ).execute()

                            # Break loop if successful
                            break
                        except Exception as e:
                            if attempt == MAX_RETRIES - 1:  # Last attempt
                                raise e
                            time.sleep(2 ** attempt)  # Exponential backoff

                    file_id = drive_file.get('id')
                    file_url = drive_file.get('webViewLink')
                    logger.info(f"File uploaded to Google Drive: {file_url}")

                    # Save metadata to database
                    file_data = ProcessedFileData.objects.create(
                        file_id=file_id,
                        file_name=file_name,
                        file_url=file_url,
                        processed=True
                    )
                    logger.info(f"File metadata saved to database with ID: {file_data.id}")

                    # Clean up temporary file
                    default_storage.delete(file_path)
                    logger.info(f"Temporary file deleted: {file_path}")

                    return JsonResponse({
                        'status': 'success',
                        'message': 'File uploaded successfully',
                        'file_id': file_id,
                        'file_url': file_url
                    })

                except Exception as e:
                    logger.error(f"Upload error: {str(e)}")
                    default_storage.delete(file_path)
                    raise e

            except Exception as e:
                logger.error(f"Error during file processing: {str(e)}")
                return JsonResponse({
                    'status': 'error',
                    'message': str(e)
                }, status=500)

        return JsonResponse({
            'status': 'error',
            'message': 'No file provided'
        }, status=400)

    return JsonResponse({
        'status': 'error',
        'message': 'Method not allowed'
    }, status=405)

@csrf_exempt
def fetch_files(request):
    if request.method == 'POST':
        try:
            logger.info(f"Fetch request body: {request.body.decode('utf-8')}")
            body = json.loads(request.body)
            file_url = body.get('file_url')
            file_type = body.get('file_type')
            
            if not file_url or not file_type:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Missing required parameters'
                }, status=400)

            # Get file from database
            try:
                file_data = ProcessedFileData.objects.get(file_url=file_url)
                logger.info(f"Found file in database: {file_data.file_id}")
            except ProcessedFileData.DoesNotExist:
                return JsonResponse({
                    'status': 'error',
                    'message': 'File not found in database'
                }, status=404)

            # Get file content from Google Drive with retry logic
            for attempt in range(MAX_RETRIES):
                try:
                    request = drive_service.files().get_media(fileId=file_data.file_id)
                    file_content = request.execute()
                    content = file_content.decode('utf-8')
                    logger.info("Successfully retrieved file content from Drive")
                    break
                except Exception as e:
                    if attempt == MAX_RETRIES - 1:  # Last attempt
                        raise e
                    time.sleep(2 ** attempt)  # Exponential backoff
                    logger.warning(f"Retry {attempt + 1} for file fetch")

            # Process based on file type
            if file_type == 'csv':
                csv_data = []
                lines = content.strip().split('\n')
                reader = csv.reader(lines)
                for row in reader:
                    csv_data.append(row)
                
                return JsonResponse({
                    'status': 'success',
                    'csv_content': csv_data
                })
                
            elif file_type == 'json':
                json_data = json.loads(content)
                return JsonResponse({
                    'status': 'success',
                    'json_content': json_data
                })
                
            elif file_type == 'xml':
                return JsonResponse({
                    'status': 'success',
                    'xml_content': content
                })
                
            else:
                return JsonResponse({
                    'status': 'success',
                    'text_content': content
                })

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