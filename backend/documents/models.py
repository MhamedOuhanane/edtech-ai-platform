"""Modèles liés aux documents et aux fragments indexables."""

from django.conf import settings
from django.db import models
from pgvector.django import VectorField


# Document source importé par un utilisateur et préparé pour le RAG.
class Document(models.Model):
	class Status(models.TextChoices):
		UPLOADED = "UPLOADED", "Uploaded"
		PROCESSING = "PROCESSING", "Processing"
		READY = "READY", "Ready"
		FAILED = "FAILED", "Failed"

	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="documents")
	title = models.CharField(max_length=255)
	file_key = models.CharField(max_length=512)
	file_hash = models.CharField(max_length=64)
	file_size = models.PositiveBigIntegerField()
	page_count = models.PositiveIntegerField(default=0)
	status = models.CharField(max_length=20, choices=Status.choices, default=Status.UPLOADED)
	error_message = models.TextField(null=True, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		unique_together = ["user", "file_hash"]
		ordering = ["-created_at"]

	def __str__(self) -> str:
		return self.title


# Fragment vectorisé utilisé par la recherche sémantique.
class Chunk(models.Model):
	document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="chunks")
	content = models.TextField()
	page_number = models.IntegerField()
	chunk_index = models.IntegerField()
	embedding = VectorField(dimensions=384, null=True, blank=True)

	class Meta:
		unique_together = ["document", "chunk_index"]
		ordering = ["document_id", "chunk_index"]

	def __str__(self) -> str:
		return f"{self.document_id}#{self.chunk_index}"
