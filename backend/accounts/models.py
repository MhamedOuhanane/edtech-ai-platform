"""Modèles du compte utilisateur."""

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class CustomUserManager(BaseUserManager):
    """Manager personnalisé pour gérer la création des utilisateurs via l'email."""
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("L'email est obligatoire")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', User.Role.ADMINISTRATEUR)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Le superuser doit avoir is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Le superuser doit avoir is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


# Utilisateur custom centré sur l'email et les règles métier de quotas.
class User(AbstractUser):
    class Role(models.TextChoices):
        APPRENANT = "APPRENANT", "Apprenant"
        ADMINISTRATEUR = "ADMINISTRATEUR", "Administrateur"

    username = None
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.APPRENANT)
    quota_docs = models.PositiveIntegerField(default=10)
    quota_storage = models.PositiveBigIntegerField(default=104857600)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = CustomUserManager() 

    def __str__(self) -> str:
        return self.email