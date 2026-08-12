"""Pipeline d'ingestion RAG pour transformer un PDF en chunks vectorisés."""

import os
import tempfile

import pdfplumber
import pytesseract
from sentence_transformers import SentenceTransformer
from PIL import Image
from django.db import transaction

from .models import Chunk, Document
from .storage import get_bucket_name, get_s3_client


# Le modèle d'embedding est chargé une seule fois au niveau du module.
EMBEDDING_MODEL = SentenceTransformer("all-MiniLM-L6-v2")


def _split_text_into_chunks(text: str, chunk_size: int = 800, overlap: int = 200) -> list[str]:
    # Découpe simple avec chevauchement pour conserver le contexte.
    cleaned_text = text.strip()
    if not cleaned_text:
        return []

    chunks: list[str] = []
    start = 0
    while start < len(cleaned_text):
        end = min(start + chunk_size, len(cleaned_text))
        chunk = cleaned_text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(cleaned_text):
            break
        start = max(end - overlap, start + 1)
    return chunks


def _extract_page_text(page) -> str:
    # On tente d'abord l'extraction textuelle native de pdfplumber.
    text = page.extract_text() or ""
    if text.strip():
        return text

    # Si la page ne contient pas de texte exploitable, on bascule sur l'OCR.
    page_image = page.to_image(resolution=200).original
    if not isinstance(page_image, Image.Image):
        page_image = Image.fromarray(page_image)
    return pytesseract.image_to_string(page_image)


def process_document(document_id):
    """Traite un document: téléchargement, extraction, chunking, embeddings et sauvegarde."""
    temp_pdf_path = None
    document = None

    try:
        document = Document.objects.get(pk=document_id)
        document.status = Document.Status.PROCESSING
        document.error_message = None
        document.save(update_fields=["status", "error_message", "updated_at"])

        # Téléchargement du fichier dans un emplacement temporaire local.
        client = get_s3_client()
        bucket_name = get_bucket_name()
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_pdf_path = temp_file.name
        client.download_file(bucket_name, document.file_key, temp_pdf_path)

        # Extraction page par page avec pdfplumber, puis OCR en fallback si besoin.
        page_payloads: list[tuple[int, str]] = []
        with pdfplumber.open(temp_pdf_path) as pdf:
            document.page_count = len(pdf.pages)
            document.save(update_fields=["page_count", "updated_at"])

            for page_number, page in enumerate(pdf.pages, start=1):
                page_text = _extract_page_text(page)
                if page_text.strip():
                    page_payloads.append((page_number, page_text))

        # Construction des chunks en gardant le numéro de page d'origine.
        chunk_payloads: list[dict] = []
        chunk_texts: list[str] = []
        chunk_index = 0

        for page_number, page_text in page_payloads:
            for chunk_text in _split_text_into_chunks(page_text):
                chunk_payloads.append(
                    {
                        "document": document,
                        "content": chunk_text,
                        "page_number": page_number,
                        "chunk_index": chunk_index,
                    }
                )
                chunk_texts.append(chunk_text)
                chunk_index += 1

        # Encodage des chunks en lot pour limiter le coût de calcul.
        if chunk_payloads:
            embeddings = EMBEDDING_MODEL.encode(chunk_texts, batch_size=32, convert_to_numpy=True)
            chunks_to_create = []
            for payload, embedding in zip(chunk_payloads, embeddings, strict=False):
                chunks_to_create.append(
                    Chunk(
                        document=payload["document"],
                        content=payload["content"],
                        page_number=payload["page_number"],
                        chunk_index=payload["chunk_index"],
                        embedding=embedding.tolist(),
                    )
                )

            # On remplace les fragments existants si le pipeline est relancé.
            with transaction.atomic():
                Chunk.objects.filter(document=document).delete()
                Chunk.objects.bulk_create(chunks_to_create)

        document.status = Document.Status.READY
        document.error_message = None
        document.save(update_fields=["status", "error_message", "updated_at"])
        return document

    except Exception as exc:
        if document is not None:
            document.status = Document.Status.FAILED
            document.error_message = str(exc)
            document.save(update_fields=["status", "error_message", "updated_at"])
        return None

    finally:
        if temp_pdf_path and os.path.exists(temp_pdf_path):
            try:
                os.remove(temp_pdf_path)
            except OSError:
                pass