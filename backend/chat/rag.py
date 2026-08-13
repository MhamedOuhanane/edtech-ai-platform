"""Logique RAG: recherche vectorielle, construction du prompt et génération Gemini."""

import os

from google import genai
from pgvector.django import L2Distance
from sentence_transformers import SentenceTransformer

from documents.models import Chunk


# Modèle d'embedding chargé une seule fois au niveau du module.
EMBEDDING_MODEL = SentenceTransformer("all-MiniLM-L6-v2")

# Client Gemini partagé pour éviter de le recréer à chaque requête.
GEMINI_CLIENT = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def search_similar_chunks(query, document_ids, top_k=5):
    """Recherche les chunks les plus proches sémantiquement."""
    if not document_ids:
        return []

    query_vector = EMBEDDING_MODEL.encode([query], convert_to_numpy=True)[0].tolist()

    return list(
        Chunk.objects.annotate(distance=L2Distance("embedding", query_vector))
        .filter(document_id__in=document_ids, document__status="READY")
        .order_by("distance")[:top_k]
    )


def build_prompt(question, chunks, conversation_history=None):
    """Construit le prompt final envoyé à Gemini."""
    if conversation_history is None:
        conversation_history = []

    system_prompt = (
        "Tu es un assistant pédagogique. Réponds uniquement à partir des passages fournis. "
        "Cite tes sources avec [1], [2]... Si tu ne trouves pas la réponse dans les passages, dis-le clairement."
    )

    recent_history = list(conversation_history)[-6:]

    context_lines = [
        system_prompt,
        "",
        f"Question: {question}",
        "",
        "Passages:"
    ]

    for index, chunk in enumerate(chunks, start=1):
        context_lines.append(
            f"[{index}] (page {getattr(chunk, 'page_number', '?')}) {chunk.content}"
        )

    if recent_history:
        context_lines.extend(["", "Historique récent:"])
        for message in recent_history:
            context_lines.append(f"{message.role}: {message.content}")

    return "\n".join(context_lines)


def generate_response_stream(prompt):
    """Génère la réponse Gemini en streaming."""
    response = GEMINI_CLIENT.models.generate_content_stream(
        model=os.getenv("GEMINI_MODEL", "gemini-flash-latest"),
        contents=prompt,
    )

    for chunk in response:
        text = getattr(chunk, "text", None)
        if text:
            yield text