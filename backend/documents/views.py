"""Vues CRUD pour les documents et leur ingestion."""

import hashlib
import os

from django.db.models import Sum
from rest_framework import permissions, status, viewsets
from rest_framework.response import Response

from .models import Document
from .serializers import DocumentSerializer, DocumentUploadSerializer
from .storage import delete_file, upload_file


# Point d'entrée temporaire pour lancer l'ingestion en arrière-plan.
def trigger_document_ingestion(document: Document) -> None:
    # Import local pour éviter une dépendance circulaire au chargement du module.
    from .ingestion import process_document

    process_document(document.id)


# API CRUD des documents, filtrée selon le rôle de l'utilisateur.
class DocumentViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = Document.objects.select_related("user")
        if getattr(user, "role", None) == "ADMINISTRATEUR" or user.is_superuser:
            return queryset
        return queryset.filter(user=user)

    def get_serializer_class(self):
        if self.action == "create":
            return DocumentUploadSerializer
        return DocumentSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = DocumentSerializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        document = self.get_object()
        serializer = DocumentSerializer(document)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = DocumentUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        upload_file_obj = serializer.validated_data["file"]
        title = serializer.validated_data["title"]

        file_bytes = upload_file_obj.read()
        file_hash = hashlib.md5(file_bytes).hexdigest()
        file_size = len(file_bytes)
        upload_file_obj.seek(0)

        user = request.user
        documents_count = Document.objects.filter(user=user).count()
        total_storage = Document.objects.filter(user=user).aggregate(total=Sum("file_size"))["total"] or 0

        if documents_count >= getattr(user, "quota_docs", 0):
            return Response({"detail": "Quota de documents atteinte."}, status=status.HTTP_400_BAD_REQUEST)
        if total_storage + file_size > getattr(user, "quota_storage", 0):
            return Response({"detail": "Quota de stockage atteint."}, status=status.HTTP_400_BAD_REQUEST)
        if Document.objects.filter(user=user, file_hash=file_hash).exists():
            return Response({"detail": "Ce PDF a déjà été uploadé."}, status=status.HTTP_400_BAD_REQUEST)

        file_extension = os.path.splitext(upload_file_obj.name)[1].lower() or ".pdf"
        file_key = f"documents/{user.id}/{file_hash}{file_extension}"
        upload_file(upload_file_obj, file_key)

        document = Document.objects.create(
            user=user,
            title=title,
            file_key=file_key,
            file_hash=file_hash,
            file_size=file_size,
            page_count=0,
            status=Document.Status.UPLOADED,
        )

        trigger_document_ingestion(document)
        output = DocumentSerializer(document)
        return Response(output.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        document = self.get_object()
        delete_file(document.file_key)
        document.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
