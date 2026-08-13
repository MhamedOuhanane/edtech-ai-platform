"""Routes de l'app documents."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import DocumentViewSet


# Routeur DRF pour exposer le CRUD des documents.
router = DefaultRouter()
router.register(r"", DocumentViewSet, basename="document")

urlpatterns = [
    path("", include(router.urls)),
]