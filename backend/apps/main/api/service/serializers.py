from rest_framework.serializers import (
    ModelSerializer,
    SerializerMethodField,
    IntegerField,
    ValidationError,
)
from django.conf import settings

from apps.main.models import (
    Service,
)

User = settings.AUTH_USER_MODEL


# ─── Service Serializers ─────────────────────────────────────────────────────

class ServiceSerializer(ModelSerializer):
    """Service толық сериализаторы"""
    salon_info = SerializerMethodField()
    duration_minutes = SerializerMethodField()

    class Meta:
        model = Service
        fields = [
            'id', 'name', 'description', 'price',
            'duration', 'duration_minutes',
            'salon_info', 'is_active', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_salon_info(self, obj):
        return {
            'id': obj.salon.id,
            'name': obj.salon.name,
            'address': obj.salon.address,
        }

    def get_duration_minutes(self, obj):
        """Duration-ны минутпен қайтару (клиент үшін ыңғайлы)"""
        if obj.duration:
            return int(obj.duration.total_seconds() // 60)
        return None


class ServiceCreateSerializer(ModelSerializer):
    """Service жасау сериализаторы (admin)"""
    duration_minutes = IntegerField(
        write_only=True,
        min_value=5,
        help_text="Duration in minutes"
    )

    class Meta:
        model = Service
        fields = ['name', 'description', 'price', 'duration_minutes', 'salon', 'is_active']

    def validate_price(self, value):
        if value <= 0:
            raise ValidationError('Price must be greater than 0.')
        return value

    def create(self, validated_data):
        from datetime import timedelta
        minutes = validated_data.pop('duration_minutes')
        validated_data['duration'] = timedelta(minutes=minutes)
        return Service.objects.create(**validated_data)

    def update(self, instance, validated_data):
        from datetime import timedelta
        if 'duration_minutes' in validated_data:
            minutes = validated_data.pop('duration_minutes')
            validated_data['duration'] = timedelta(minutes=minutes)
        return super().update(instance, validated_data)


class ServiceUpdateSerializer(ModelSerializer):
    """Service бағасын ғана жаңарту"""
    class Meta:
        model = Service
        fields = ['price']

