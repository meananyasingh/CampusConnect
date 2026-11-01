from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User
from .serializers import (
    AuthResponseSerializer,
    LoginSerializer,
    LogoutSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RegistrationSerializer,
    RecruiterRegistrationSerializer,
    StudentRegistrationSerializer,
    UserSerializer,
)


class RegistrationView(generics.CreateAPIView):
    permission_classes = (AllowAny,)
    serializer_class = RegistrationSerializer
    registration_role = None

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["registration_role"] = self.registration_role
        return context

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class StudentRegistrationView(RegistrationView):
    serializer_class = StudentRegistrationSerializer
    registration_role = User.Role.STUDENT


class RecruiterRegistrationView(RegistrationView):
    serializer_class = RecruiterRegistrationSerializer
    registration_role = User.Role.RECRUITER


class RoleLoginView(APIView):
    permission_classes = (AllowAny,)
    serializer_class = LoginSerializer
    required_role = None

    @extend_schema(request=LoginSerializer, responses={200: AuthResponseSerializer})
    def post(self, request):
        serializer = self.serializer_class(
            data=request.data,
            context={"request": request, "required_role": self.required_role},
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": UserSerializer(user).data,
            }
        )


class StudentLoginView(RoleLoginView):
    required_role = User.Role.STUDENT


class RecruiterLoginView(RoleLoginView):
    required_role = User.Role.RECRUITER


class AdminLoginView(RoleLoginView):
    required_role = User.Role.ADMIN


class CurrentUserView(generics.RetrieveAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user


class LogoutView(APIView):
    permission_classes = (AllowAny,)
    serializer_class = LogoutSerializer

    @extend_schema(request=LogoutSerializer, responses={204: None})
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class PasswordResetRequestView(APIView):
    permission_classes = (AllowAny,)
    serializer_class = PasswordResetRequestSerializer

    @extend_schema(request=PasswordResetRequestSerializer, responses={200: None})
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {
                "message": (
                    "If an active account exists for this email, password reset "
                    "instructions have been sent."
                )
            }
        )


class PasswordResetConfirmView(APIView):
    permission_classes = (AllowAny,)
    serializer_class = PasswordResetConfirmSerializer

    @extend_schema(request=PasswordResetConfirmSerializer, responses={200: None})
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "Your password has been reset successfully."})
