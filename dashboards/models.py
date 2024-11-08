# from django.db import models
# from django.conf import settings

# class Dashboard(models.Model):
#     user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
#     name = models.CharField(max_length=100)
#     state = models.TextField()  # Store JSON-encoded state here
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     def __str__(self):
#         return self.name



from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
import json

class Dashboard(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    state = models.TextField()  # Store JSON-encoded state here
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'name']
        ordering = ['-updated_at']

    def clean(self):
        # Validate that state is valid JSON
        try:
            if self.state:
                json.loads(self.state)
        except json.JSONDecodeError:
            raise ValidationError('Dashboard state must be valid JSON')

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} - {self.user.username}"



