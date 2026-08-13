"""Routes de l'app chat."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ChatView, ConversationViewSet


# Routeur pour le CRUD des conversations.
router = DefaultRouter()
router.register(r"conversations", ConversationViewSet, basename="conversation")

urlpatterns = [
    path("", include(router.urls)),
    path("chat/", ChatView.as_view(), name="chat"),
]