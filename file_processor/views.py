from django.shortcuts import render

# Create your views here.
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
import csv
import logging

logger = logging.getLogger(__name__)

@csrf_exempt
def upload_file(request):
    if request.method == 'POST':
        logger.info(f"Request files: {request.FILES}")  #this is to debug what's in the request
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