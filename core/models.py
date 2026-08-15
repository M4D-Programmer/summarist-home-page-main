from django.conf import settings
from django.db import models


class LibraryBook(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    book_id = models.CharField(max_length=100)
    title = models.CharField(max_length=200)
    finished = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'book_id')


class Subscription(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    plan = models.CharField(max_length=20, default='basic')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
