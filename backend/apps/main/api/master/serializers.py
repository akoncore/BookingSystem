from rest_framework.serializers import (
    ModelSerializer,
    SerializerMethodField,
)
from django.conf import settings

from apps.main.models import (
    Master
)

User = settings.AUTH_USER_MODEL


# ─── Master Serializers ──────────────────────────────────────────────────────

class MasterSerializer(ModelSerializer):
    """Master толық сериализаторы"""
    user_info = SerializerMethodField()
    salon_info = SerializerMethodField()

    class Meta:
        model = Master
        fields = [
            'id', 'user_info', 'salon_info',
            'specialization', 'experience_years', 'bio',
            'is_approved', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'is_approved', 'created_at', 'updated_at']

    def get_user_info(self, obj):
        user = obj.user
        return {
            'id': user.id,
            'full_name': user.full_name,
            'email': user.email,
            'phone': user.phone,
            'role': user.role,
        }

    def get_salon_info(self, obj):
        salon = obj.salon
        return {
            'id': salon.id,
            'name': salon.name,
            'address': salon.address,
        }


class MasterIngoSerializer(ModelSerializer):
    """Master қысқа ақпаратты сериализаторы"""
    user_info = SerializerMethodField()

    class Meta:
        model = Master
        fields = ['user_info', 'specialization', 'experience_years']

    def get_user_info(self, obj):
        return {'id': obj.user.id, 'full_name': obj.user.full_name}
