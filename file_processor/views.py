import csv
import config
import logging
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import FileSystemStorage
from pathlib import Path
from google.oauth2 import pandas as pd
from django.service_account
from googleapiconf import settinglient.discoery import build
from googleapiclient.http import MediaFileUpload
from .models import ProcessedFileData
from django.conf import settings  # Import settings module to access settings attributes
import os

logger = logging.getLogger(__name__)

upload_directory = Path(settings.MEDIA_ROOT) / 'uploads'
file_storage = FileSystemStorage(location=upload_directory, base_url='/media/uploads/')

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
                # Get the uploaded file from the request
                uploaded_file = request.FILES['file']
                logger.info(f"Received file: {uploaded_file.name}")

                # Save the file temporarily in the server's filesystem
                file_path = default_storage.save(uploaded_file.name, uploaded_file)
                logger.info(f"File saved at: {file_path}")

                # Open the file for processing (assuming it's a CSV)
                with default_storage.open(file_path) as file:
                    logger.info("Attempting to read the CSV file")
                    reader = csv.reader(file.read().decode('utf-8').splitlines())
                    
                    # Logging rows for debugging
                    for row in reader:
                        logger.info(f"Processing row: {row}")
                        # You can store rows in the database or process them as needed

                # Clean up: remove the file after processing
                default_storage.delete(file_path)
                logger.info(f"File deleted: {file_path}")

                # Send a success response back to the frontend with HTTP status 200
                return JsonResponse({'status': 'success', 'message': 'File uploaded and processed successfully'}, status=200)

            except Exception as e:
                logger.error(f"Error during file processing: {str(e)}")
                # Send an error response with HTTP status 500
                return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
        else:
            logger.error("No file provided in the request")
            # Send an error response with HTTP status 400
            return JsonResponse({'status': 'error', 'message': 'No file provided'}, status=400)