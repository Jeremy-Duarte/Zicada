from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    phone = models.CharField(max_length=20, blank=True)
    is_delivery = models.BooleanField(default=False)

    def __str__(self):
        return self.email or self.username