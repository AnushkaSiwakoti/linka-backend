from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager

class CustomUserManager(BaseUserManager):
    def create_user(self, email, username, password):
        if not email:
            raise ValueError('An email is required')
        if not username:
            raise ValueError('A username is required')

        # Ensure email and username are unique by using the built-in constraints
        user = self.model(
            email=self.normalize_email(email),
            username=username,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def verify_user(self, username, password):
        try:
            user = self.get(username=username)
        except self.model.DoesNotExist:
            raise ValueError('User does not exist')

        if not user.check_password(password):
            raise ValueError('Incorrect password')

        return user

class BaseUser(AbstractBaseUser):
    email = models.EmailField(max_length=255, unique=True)
    username = models.CharField(max_length=30, unique=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    objects = CustomUserManager()

    def __str__(self):
        return self.email
