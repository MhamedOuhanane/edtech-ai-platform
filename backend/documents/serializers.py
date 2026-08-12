"""Sérializers pour la lecture et l'upload de documents."""

from rest_framework import serializers

from .models import Chunk, Document


# Sérializer de lecture pour exposer les métadonnées documentaires.
class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = [
            "id",
            "user",
            "title",
            "file_key",
            "file_hash",
            "file_size",
            "page_count",
            "status",
            "error_message",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


# Sérializer d'écriture pour recevoir le fichier et le titre.
class DocumentUploadSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255)
    file = serializers.FileField()


# Sérializer de lecture pour les chunks indexés.
class ChunkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chunk
        fields = [
            "id",
            "document",
            "content",
            "page_number",
            "chunk_index",
            "embedding",
        ]
        read_only_fields = fields