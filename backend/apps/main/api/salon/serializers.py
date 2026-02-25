from rest_framework.serializers import (
    ModelSerializer,
    SerializerMethodField,
    ValidationError,
)

from apps.main.models import (
    Salon
)
from main.api.master.serializers import (
    MasterSerializer
)
from main.api.service.serializers import(
    ServiceSerializer
)
# ─── Salon Serializers ───────────────────────────────────────────────────────

class SalonListSerializer(ModelSerializer):
    """Салондар тізімі (client қарайды — жылдам)"""
    master_count = SerializerMethodField()
    service_count = SerializerMethodField()
    owner_name = SerializerMethodField()

    class Meta:
        model = Salon
        fields = [
            'id', 'salon_code', 'name', 'address',
            'phone', 'description', 'is_active',
            'master_count', 'service_count', 'owner_name',
            'created_at',
        ]

    def get_master_count(self, obj):
        return obj.masters.filter(is_approved=True).count()

    def get_service_count(self, obj):
        return obj.services.filter(is_active=True).count()

    def get_owner_name(self, obj):
        return obj.owner.full_name if obj.owner else None


class SalonSerializer(ModelSerializer):
    """Salon толық сериализаторы"""
    masters = MasterSerializer(many=True, read_only=True)
    services = ServiceSerializer(many=True, read_only=True)
    master_count = SerializerMethodField()
    service_count = SerializerMethodField()

    class Meta:
        model = Salon
        fields = [
            'id', 'salon_code', 'name', 'address', 'phone', 'description',
            'is_active', 'masters', 'services',
            'master_count', 'service_count',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'salon_code', 'created_at', 'updated_at']

    def get_master_count(self, obj):
        return obj.masters.filter(is_approved=True).count()

    def get_service_count(self, obj):
        return obj.services.filter(is_active=True).count()

    def validate(self, attrs):
        """Salon жасаушы admin болуы керек"""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            owner = attrs.get('owner', getattr(self.instance, 'owner', None))
            if owner and not owner.is_admin:
                raise ValidationError({'owner': 'Salon owner must have admin role.'})
        return attrs
