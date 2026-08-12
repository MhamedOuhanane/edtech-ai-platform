"""Vues d'authentification et de profil."""

from rest_framework import permissions, status
from rest_framework.generics import RetrieveUpdateAPIView, CreateAPIView
from rest_framework.response import Response

from .serializers import RegisterSerializer, UserSerializer


# Inscription ouverte à tous les visiteurs.
class RegisterView(CreateAPIView):
	serializer_class = RegisterSerializer
	permission_classes = [permissions.AllowAny]

	def create(self, request, *args, **kwargs):
		serializer = self.get_serializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		user = serializer.save()
		output = UserSerializer(user, context=self.get_serializer_context())
		return Response(output.data, status=status.HTTP_201_CREATED)


# Consultation et mise à jour partielle du profil connecté.
class ProfileView(RetrieveUpdateAPIView):
	serializer_class = UserSerializer
	permission_classes = [permissions.IsAuthenticated]

	def get_object(self):
		return self.request.user
