import re

from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Measurement

User = get_user_model()
_FA_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")


def normalize_phone(raw: str) -> str:
    digits = re.sub(r"\D", "", (raw or "").translate(_FA_DIGITS))
    if digits.startswith("98") and len(digits) == 12:
        digits = "0" + digits[2:]
    elif len(digits) == 10 and digits.startswith("9"):
        digits = "0" + digits
    return digits


class UserSerializer(serializers.ModelSerializer):
    is_coach = serializers.BooleanField(read_only=True)

    class Meta:
        model = User
        fields = ["id", "phone", "name", "role", "metrics", "unit", "is_private", "is_coach", "created_at"]
        read_only_fields = ["id", "phone", "created_at"]


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = ["phone", "name", "password", "role"]

    def validate_phone(self, value):
        phone = normalize_phone(value)
        if not re.fullmatch(r"09\d{9}", phone):
            raise serializers.ValidationError("شماره موبایل معتبر نیست. مثال: ۰۹۱۲۱۲۳۴۵۶۷")
        if User.objects.filter(phone=phone).exists():
            raise serializers.ValidationError("با این شماره قبلاً حساب ساخته شده است. وارد شوید.")
        return phone

    def create(self, validated):
        return User.objects.create_user(**validated)


def tokens_for(user) -> dict:
    refresh = RefreshToken.for_user(user)
    return {"access": str(refresh.access_token), "refresh": str(refresh)}


class MeasurementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Measurement
        fields = ["id", "date", "weight_kg", "body_fat", "waist_cm", "chest_cm", "arm_cm", "thigh_cm", "hip_cm", "notes"]

    def validate(self, attrs):
        keys = ["weight_kg", "body_fat", "waist_cm", "chest_cm", "arm_cm", "thigh_cm", "hip_cm"]
        if not any(attrs.get(k) is not None for k in keys) and not self.instance:
            raise serializers.ValidationError("حداقل یک اندازه را وارد کنید.")
        return attrs
