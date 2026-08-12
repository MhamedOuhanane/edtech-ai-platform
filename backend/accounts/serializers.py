"""Sérializers pour l'inscription et le profil utilisateur."""

from django.contrib.auth import get_user_model
from rest_framework import serializers


User = get_user_model()


# Sérializer public pour exposer les données utiles du profil.
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "role",
            "quota_docs",
            "quota_storage",
            "is_active",
        ]
        read_only_fields = ["id", "role", "quota_docs", "quota_storage", "is_active"]


# Sérializer dédié à l'inscription avec mot de passe écrit uniquement.
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["email", "password", "first_name", "last_name"]

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user