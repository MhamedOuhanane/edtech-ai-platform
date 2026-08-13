"""Vues de conversation et de chat streaming SSE."""

import json

from django.db import transaction
from django.http import StreamingHttpResponse
from rest_framework import permissions, status, viewsets
from rest_framework.parsers import JSONParser
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import render

from documents.models import Document

from .models import Conversation, Message
from .rag import build_prompt, generate_response_stream, search_similar_chunks
from .serializers import ConversationSerializer


# CRUD des conversations limité aux conversations de l'utilisateur connecté.
class ConversationViewSet(viewsets.ModelViewSet):
    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Conversation.objects.select_related("user", "document").prefetch_related("messages").filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


# Endpoint SSE qui orchestre la recherche RAG et la génération Gemini.
class ChatView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [JSONParser]

    def post(self, request, *args, **kwargs):
        conversation_id = request.data.get("conversation_id")
        document_ids = request.data.get("document_ids", [])
        message_text = request.data.get("message", "").strip()

        if not message_text:
            return Response({"detail": "Le message est obligatoire."}, status=status.HTTP_400_BAD_REQUEST)

        documents = Document.objects.filter(id__in=document_ids, status=Document.Status.READY)
        if not document_ids or documents.count() != len(document_ids):
            return Response({"detail": "Tous les documents doivent être au statut READY."}, status=status.HTTP_400_BAD_REQUEST)

        conversation = None
        if conversation_id:
            conversation = Conversation.objects.filter(id=conversation_id, user=request.user).first()
            if conversation is None:
                return Response({"detail": "Conversation introuvable."}, status=status.HTTP_404_NOT_FOUND)
        else:
            title = message_text[:50]
            conversation = Conversation.objects.create(user=request.user, title=title, document=documents.first() if documents.count() == 1 else None)

        Message.objects.create(conversation=conversation, role=Message.Role.USER, content=message_text, citations=[])

        history = list(conversation.messages.all().order_by("created_at"))
        chunks = search_similar_chunks(message_text, document_ids=document_ids, top_k=5)
        prompt = build_prompt(message_text, chunks, conversation_history=history)

        citations = [
            {"chunk_id": chunk.id, "page": chunk.page_number, "text": chunk.content[:300]}
            for chunk in chunks
        ]

        def event_stream():
            assistant_parts = []
            try:
                for text_piece in generate_response_stream(prompt):
                    assistant_parts.append(text_piece)
                    yield f"data: {json.dumps({'type': 'chunk', 'text': text_piece}, ensure_ascii=False)}\n\n"

                full_answer = "".join(assistant_parts)
                with transaction.atomic():
                    Message.objects.create(
                        conversation=conversation,
                        role=Message.Role.ASSISTANT,
                        content=full_answer,
                        citations=citations,
                    )
                yield f"data: {json.dumps({'type': 'done'}, ensure_ascii=False)}\n\n"
            except Exception as exc:
                with transaction.atomic():
                    Message.objects.create(
                        conversation=conversation,
                        role=Message.Role.ASSISTANT,
                        content=str(exc),
                        citations=citations,
                    )
                yield f"data: {json.dumps({'type': 'error', 'detail': str(exc)}, ensure_ascii=False)}\n\n"

        response = StreamingHttpResponse(event_stream(), content_type="text/event-stream")
        response["Cache-Control"] = "no-cache"
        response["X-Accel-Buffering"] = "no"
        return response

# Create your views here.
