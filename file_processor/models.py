from django.db import models

class ProcessedFileData(models.Model):
    file_id = models.CharField(max_length=100)  # To store the Google Drive file ID
    file_name = models.CharField(max_length=255)  # Original file name
    timestamp = models.DateTimeField(auto_now_add=True)  # Timestamp when the file was uploaded
    file_url = models.URLField()  # To store the Google Drive file URL
    processed = models.BooleanField(default=False)  # To indicate whether the file is processed or not

    def __str__(self):
        return f'{self.file_name} - {self.file_id}'
