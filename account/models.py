from django.db import models
from django.contrib.auth.models import AbstractUser, Permission


class BaseModel(models.Model):
    """
    Abstract base model providing timestamp fields for all models.
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Role(BaseModel):
    """
    Role model for managing user permissions and access levels.
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, default='')
    permissions = models.ManyToManyField(Permission, blank=True, related_name='roles')

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class User(AbstractUser, BaseModel):
    """
    Custom user model extending Django's AbstractUser.
    """
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True, related_name='users')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.email or self.username
