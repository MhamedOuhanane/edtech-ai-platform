"""Routes d'authentification des comptes."""

from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import ProfileView, RegisterView


urlpatterns = [
    # Inscription d'un nouvel utilisateur.
    path("register/", RegisterView.as_view(), name="register"),
    # Consultation et mise à jour du profil courant.
    path("profile/", ProfileView.as_view(), name="profile"),
    # Obtention et renouvellement des jetons JWT.
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]