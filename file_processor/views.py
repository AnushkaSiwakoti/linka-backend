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
import xml.etree.ElementTree as ET
import config
import requests

# Configure logging
logger = logging.getLogger(__name__)

# Set up Google Drive credentials
SERVICE_ACCOUNT_FILE = config.GOOGLE_CREDENTIALS_PATH

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE,
    scopes=['https://www.googleapis.com/auth/drive.file']
)
drive_service = build('drive', 'v3', credentials=credentials)

def process_file_content(file_path, file_extension):
    """Process file content based on file type."""
    try:
        if file_extension == 'csv':
            with open(file_path, 'r') as file:
                reader = csv.reader(file)
                return list(reader), 'csv_content'
        
        elif file_extension == 'xml':
            tree = ET.parse(file_path)
            root = tree.getroot()
            content = []
            for child in root:
                row = {}
                for elem in child:
                    row[elem.tag] = elem.text
                content.append(row)
            return content, 'xml_content'
        
        elif file_extension == 'json':
            with open(file_path, 'r') as file:
                return json.load(file), 'json_content'
        
        elif file_extension == 'txt':
            with open(file_path, 'r') as file:
                return file.read(), 'text_content'
        
        elif file_extension == 'svg':
            with open(file_path, 'r') as file:
                return file.read(), 'svg_content'
        
        else:
            raise ValueError(f'Unsupported file type: {file_extension}')
    
    except Exception as e:
        logger.error(f"Error processing {file_extension} file: {str(e)}")
        raise

@csrf_exempt
def upload_file(request):
    """Handle file upload and processing."""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)

    if not request.FILES.get('file'):
        return JsonResponse({'status': 'error', 'message': 'No file provided'}, status=400)

    try:
        uploaded_file = request.FILES['file']
        logger.info(f"Received file: {uploaded_file.name}")

        # Get file extension and validate
        file_extension = Path(uploaded_file.name).suffix.lower()[1:]
        if file_extension not in ['csv', 'xml', 'json', 'txt', 'svg']:
            return JsonResponse({
                'status': 'error', 
                'message': f'Unsupported file type: {file_extension}'
            }, status=400)

        # Save file temporarily
        file_path = os.path.join('/tmp', uploaded_file.name)
        with open(file_path, 'wb+') as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)

        logger.info(f"File saved at: {file_path}")

        # Process file content
        content, response_key = process_file_content(file_path, file_extension)

        # Upload to Google Drive
        file_metadata = {'name': uploaded_file.name}
        media = MediaFileUpload(file_path, resumable=True)
        file = drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink'
        ).execute()

        # Clean up temporary file
        os.remove(file_path)
        logger.info(f"Temporary file deleted: {file_path}")

        # Return response with processed content and file URL
        return JsonResponse({
            'status': 'success',
            response_key: content,
            'file_url': file.get('webViewLink')
        }, status=200)

    except Exception as e:
        logger.error(f"Error during file upload or processing: {str(e)}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@csrf_exempt
def fetch_file(request):
    """Fetch and process stored files."""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)

    try:
        body = json.loads(request.body)
        file_url = body.get('file_url')
        file_type = body.get('file_type')

        if not file_url:
            raise ValueError('No file_url provided')
        if not file_type:
            raise ValueError('No file_type provided')

        response = requests.get(file_url)
        if response.status_code != 200:
            return JsonResponse({
                'status': 'error', 
                'message': 'Failed to fetch file'
            }, status=400)

        content = response.text
        response_key = f'{file_type}_content'

        # Handle specific file type processing if needed
        if file_type == 'json':
            content = json.loads(content)
        elif file_type == 'xml':
            root = ET.fromstring(content)
            content = []
            for child in root:
                row = {}
                for elem in child:
                    row[elem.tag] = elem.text
                content.append(row)

        return JsonResponse({
            'status': 'success',
            response_key: content
        }, status=200)

    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error', 
            'message': 'Invalid JSON payload'
        }, status=400)
    except Exception as e:
        logger.error(f"Error fetching file: {str(e)}")
        return JsonResponse({
            'status': 'error', 
            'message': str(e)
        }, status=500)