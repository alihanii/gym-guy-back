from django.contrib.auth import authenticate
from rest_framework import generics, permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Measurement
from .serializers import MeasurementSerializer, RegisterSerializer, UserSerializer, normalize_phone, tokens_for


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        ser = RegisterSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user = ser.save()
        return Response({"user": UserSerializer(user).data, **tokens_for(user)}, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        phone = normalize_phone(request.data.get("phone", ""))
        user = authenticate(request, phone=phone, password=request.data.get("password", ""))
        if not user:
            return Response({"detail": "شماره یا رمز عبور درست نیست."}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"user": UserSerializer(user).data, **tokens_for(user)})


class MeView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user


class MeasurementViewSet(viewsets.ModelViewSet):
    serializer_class = MeasurementSerializer

    def get_queryset(self):
        return Measurement.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
