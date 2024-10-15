from django.db import models

class ProcessedFileData(models.Model):
    field1 = models.CharField(max_length=100)  #to store string data from the CSV
    field2 = models.IntegerField()  #to store integer data from the CSV
    uploaded_at = models.DateTimeField(auto_now_add=True)  # this automatically adds the timestamp of upload

    def __str__(self):
        return f'{self.field1} - {self.field2}'