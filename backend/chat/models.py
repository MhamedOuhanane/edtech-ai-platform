"""Modèles de conversation et de messages pour le chat RAG."""

from django.conf import settings
from django.db import models

from documents.models import Document


# Conversation liée à un utilisateur et éventuellement à un document.
class Conversation(models.Model):
	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="conversations")
	document = models.ForeignKey(Document, on_delete=models.SET_NULL, null=True, blank=True, related_name="conversations")
	title = models.CharField(max_length=255)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ["-created_at"]

	def __str__(self) -> str:
		return self.title


# Message échangé dans une conversation avec citations structurées.
class Message(models.Model):
	class Role(models.TextChoices):
		USER = "user", "User"
		ASSISTANT = "assistant", "Assistant"

	conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
	role = models.CharField(max_length=20, choices=Role.choices)
	content = models.TextField()
	citations = models.JSONField(default=list, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ["created_at"]

	def __str__(self) -> str:
		return f"{self.role} - {self.conversation_id}"
