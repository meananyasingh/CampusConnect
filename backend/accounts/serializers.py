from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.password_validation import validate_password
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework import serializers
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from rest_framework_simplejwt.tokens import RefreshToken, TokenError

from colleges.models import AcademicProgram, College
from companies.models import Company, RecruiterProfile
from students.models import enrollment_number_validator

from .models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "email", "first_name", "last_name", "role")
        read_only_fields = fields


class RegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, style={"input_type": "password"})
    password_confirm = serializers.CharField(
        write_only=True,
        style={"input_type": "password"},
    )

    class Meta:
        model = User
        fields = ("id", "email", "first_name", "last_name", "password", "password_confirm")
        read_only_fields = ("id",)
        extra_kwargs = {
            "first_name": {"required": True, "allow_blank": False},
            "last_name": {"required": True, "allow_blank": False},
        }

    def validate_email(self, value):
        email = value.strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return email

    def validate(self, attrs):
        if attrs["password"] != attrs.pop("password_confirm"):
            raise serializers.ValidationError(
                {"password_confirm": "The passwords do not match."}
            )

        candidate = User(
            email=attrs.get("email", ""),
            first_name=attrs.get("first_name", ""),
            last_name=attrs.get("last_name", ""),
        )
        validate_password(attrs["password"], user=candidate)
        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password")
        role = self.context["registration_role"]
        return User.objects.create_user(password=password, role=role, **validated_data)


class StudentRegistrationSerializer(RegistrationSerializer):
    college = serializers.PrimaryKeyRelatedField(
        queryset=College.objects.filter(is_active=True),
        write_only=True,
    )
    program = serializers.PrimaryKeyRelatedField(
        queryset=AcademicProgram.objects.filter(is_active=True, college__is_active=True),
        write_only=True,
    )
    enrollment_number = serializers.CharField(
        max_length=40,
        validators=(enrollment_number_validator,),
        write_only=True,
    )
    graduation_year = serializers.IntegerField(min_value=2000, max_value=2100, write_only=True)

    class Meta(RegistrationSerializer.Meta):
        fields = RegistrationSerializer.Meta.fields + (
            "college",
            "program",
            "enrollment_number",
            "graduation_year",
        )

    def validate(self, attrs):
        attrs = super().validate(attrs)
        college = attrs["college"]
        program = attrs["program"]
        enrollment_number = attrs["enrollment_number"].strip().upper()

        if program.college_id != college.id:
            raise serializers.ValidationError(
                {"program": "The selected program does not belong to this college."}
            )

        from students.models import StudentProfile

        if StudentProfile.objects.filter(
            college=college,
            enrollment_number__iexact=enrollment_number,
        ).exists():
            raise serializers.ValidationError(
                {"enrollment_number": "This enrollment number is already registered."}
            )

        attrs["enrollment_number"] = enrollment_number
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        from students.models import StudentProfile

        profile_data = {
            "college": validated_data.pop("college"),
            "program": validated_data.pop("program"),
            "enrollment_number": validated_data.pop("enrollment_number"),
            "graduation_year": validated_data.pop("graduation_year"),
        }
        user = super().create(validated_data)
        StudentProfile.objects.create(user=user, **profile_data)
        return user


class RecruiterRegistrationSerializer(RegistrationSerializer):
    company_name = serializers.CharField(max_length=200, write_only=True)
    company_industry = serializers.CharField(max_length=120, write_only=True)
    company_website = serializers.URLField(write_only=True)
    company_email = serializers.EmailField(write_only=True)
    designation = serializers.CharField(max_length=120, write_only=True)
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True, write_only=True)

    class Meta(RegistrationSerializer.Meta):
        fields = RegistrationSerializer.Meta.fields + (
            "company_name",
            "company_industry",
            "company_website",
            "company_email",
            "designation",
            "phone",
        )

    def validate_company_name(self, value):
        name = " ".join(value.split())
        if Company.objects.filter(name__iexact=name).exists():
            raise serializers.ValidationError(
                "This company is already registered. Ask its owner or the college administrator to add you."
            )
        return name

    @transaction.atomic
    def create(self, validated_data):
        company_data = {
            "name": validated_data.pop("company_name"),
            "industry": validated_data.pop("company_industry"),
            "website": validated_data.pop("company_website"),
            "contact_email": validated_data.pop("company_email"),
        }
        recruiter_data = {
            "designation": validated_data.pop("designation"),
            "phone": validated_data.pop("phone", ""),
        }
        user = super().create(validated_data)
        company = Company.objects.create(**company_data)
        RecruiterProfile.objects.create(
            user=user,
            company=company,
            is_company_owner=True,
            **recruiter_data,
        )
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(write_only=True)
    password = serializers.CharField(write_only=True, style={"input_type": "password"})

    def validate(self, attrs):
        email = attrs["email"].strip().lower()
        user = authenticate(
            request=self.context.get("request"),
            email=email,
            password=attrs["password"],
        )
        if user is None:
            raise serializers.ValidationError("Invalid email or password.")

        required_role = self.context["required_role"]
        if user.role != required_role:
            raise serializers.ValidationError(
                "This account is not authorized for the selected portal."
            )
        if required_role == User.Role.ADMIN and not user.is_staff:
            raise serializers.ValidationError("This administrator account is not active.")

        attrs["user"] = user
        return attrs


class AuthResponseSerializer(serializers.Serializer):
    access = serializers.CharField(read_only=True)
    refresh = serializers.CharField(read_only=True)
    user = UserSerializer(read_only=True)


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField(write_only=True)

    def save(self, **kwargs):
        try:
            RefreshToken(self.validated_data["refresh"]).blacklist()
        except TokenError as error:
            raise serializers.ValidationError(
                {"refresh": "The refresh token is invalid or expired."}
            ) from error


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(write_only=True)

    def save(self, **kwargs):
        email = self.validated_data["email"].strip().lower()
        user = User.objects.filter(email__iexact=email, is_active=True).first()
        if user is None:
            return

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        reset_url = f"{settings.FRONTEND_URL.rstrip('/')}/reset-password/{uid}/{token}"
        send_mail(
            subject="Reset your CampusConnect password",
            message=(
                "A password reset was requested for your CampusConnect account.\n\n"
                f"Use this link to choose a new password:\n{reset_url}\n\n"
                "If you did not request this, you can ignore this message."
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
        )


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField(write_only=True)
    token = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True, style={"input_type": "password"})
    password_confirm = serializers.CharField(
        write_only=True,
        style={"input_type": "password"},
    )

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError(
                {"password_confirm": "The passwords do not match."}
            )

        try:
            user_id = force_str(urlsafe_base64_decode(attrs["uid"]))
            user = User.objects.get(pk=user_id, is_active=True)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist) as error:
            raise serializers.ValidationError("This password reset link is invalid.") from error

        if not default_token_generator.check_token(user, attrs["token"]):
            raise serializers.ValidationError("This password reset link is invalid or expired.")

        validate_password(attrs["password"], user=user)
        attrs["user"] = user
        return attrs

    def save(self, **kwargs):
        user = self.validated_data["user"]
        user.set_password(self.validated_data["password"])
        update_fields = ["password"]
        if user.activated_at is None:
            user.activated_at = timezone.now()
            update_fields.append("activated_at")
        user.save(update_fields=update_fields)

        for outstanding_token in OutstandingToken.objects.filter(user=user):
            BlacklistedToken.objects.get_or_create(token=outstanding_token)

        return user
