"""Routing principal du projet."""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    # Routes d'authentification exposées sous /api/auth/.
    path('api/auth/', include('accounts.urls')),
    # Routes des documents exposées sous /api/documents/.
    path('api/documents/', include('documents.urls')),
]
