"""Sérializers pour les conversations et les messages."""

from rest_framework import serializers

from .models import Conversation, Message


# Sérializer des messages avec citations JSON prêtes pour le front.
class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ["id", "conversation", "role", "content", "citations", "created_at"]
        read_only_fields = fields


# Sérializer de conversation exposant les métadonnées principales.
class ConversationSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True, read_only=True)

    class Meta:
        model = Conversation
        fields = ["id", "user", "document", "title", "created_at", "messages"]
        read_only_fields = ["id", "user", "created_at", "messages"]