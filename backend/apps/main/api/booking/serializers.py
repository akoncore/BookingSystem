
from rest_framework.serializers import (
    Serializer,
    ModelSerializer,
    SerializerMethodField,
    CharField,
    ListField,
    IntegerField,
    ValidationError,
)
from django.conf import settings

from apps.main.models import (
    Service,
    Booking,
)

User = settings.AUTH_USER_MODEL

# ─── Booking Serializers ─────────────────────────────────────────────────────

class BookingSerializer(ModelSerializer):
    """Booking толық сериализаторы (read)"""
    client_info = SerializerMethodField()
    master_info = SerializerMethodField()
    service_info = SerializerMethodField()
    total_price = SerializerMethodField()
    status_info = SerializerMethodField()

    class Meta:
        model = Booking
        fields = [
            'id', 'booking_code',
            'client_info', 'master_info', 'service_info',
            'appointment_date', 'appointment_time',
            'status', 'status_info', 'total_price',
            'notes', 'created_at', 'updated_at',
        ]

    def get_client_info(self, obj):
        c = obj.client
        return {'id': c.id, 'full_name': c.full_name, 'email': c.email, 'phone': c.phone}

    def get_master_info(self, obj):
        m = obj.master
        profile = getattr(m, 'master_profile', None)
        return {
            'id': m.id,
            'full_name': m.full_name,
            'email': m.email,
            'specialization': profile.specialization if profile else None,
            'salon': profile.salon.name if profile else None,
        }

    def get_service_info(self, obj):
        return [
            {
                'id': s.id,
                'name': s.name,
                'price': s.price,
                'duration_minutes': int(s.duration.total_seconds() // 60),
            }
            for s in obj.services.all()
        ]

    def get_total_price(self, obj):
        return obj.calculate_total_price()

    def get_status_info(self, obj):
        status_map = {
            'pending': {
                'label': 'Pending',
                'message': 'Waiting for master confirmation',
                'can_cancel': True,
                'available_actions': ['confirm', 'cancel'],
            },
            'confirmed': {
                'label': 'Confirmed',
                'message': 'Booking confirmed by master',
                'can_cancel': True,
                'available_actions': ['complete', 'cancel'],
            },
            'completed': {
                'label': 'Completed',
                'message': 'Service completed successfully',
                'can_cancel': False,
                'available_actions': [],
            },
            'cancelled': {
                'label': 'Cancelled',
                'message': 'Booking was cancelled',
                'can_cancel': False,
                'available_actions': [],
            },
        }
        return status_map.get(obj.status, {})


class BookingCreateSerializer(ModelSerializer):
    """
    Client booking жасайды.
    service_ids — write-only, мастерді автоматты анықтайды.
    """
    service_ids = ListField(
        child=IntegerField(),
        write_only=True,
        min_length=1,
        help_text="List of service IDs to book"
    )

    class Meta:
        model = Booking
        fields = [
            'id', 'master',
            'appointment_date', 'appointment_time',
            'notes', 'service_ids',
        ]
        read_only_fields = ['id']

    def validate_master(self, value):
        """Master жұмыс жасай ма тексеру"""
        if not value.is_master:
            raise ValidationError('Selected user is not a master.')
        # Master профилі бар па?
        if not hasattr(value, 'master_profile') or not value.master_profile.is_approved:
            raise ValidationError('This master is not approved yet.')
        return value

    def validate_service_ids(self, value):
        """Қызметтер бар ма тексеру"""
        services = Service.objects.filter(id__in=value, is_active=True)
        if services.count() != len(value):
            raise ValidationError('One or more services not found or inactive.')
        return value

    def validate(self, attrs):
        """Master + services бірдей салонда ма тексеру"""
        master = attrs.get('master')
        service_ids = attrs.get('service_ids', [])

        if master and service_ids:
            master_salon = master.master_profile.salon
            services = Service.objects.filter(id__in=service_ids, is_active=True)
            for service in services:
                if service.salon_id != master_salon.id:
                    raise ValidationError(
                        f"Service '{service.name}' does not belong to master's salon."
                    )

        return attrs

    def create(self, validated_data):
        service_ids = validated_data.pop('service_ids')
        request = self.context.get('request')

        # Salon автоматты анықтау
        master = validated_data['master']
        salon = master.master_profile.salon

        booking = Booking.objects.create(
            client=request.user,
            salon=salon,
            **validated_data
        )
        services = Service.objects.filter(id__in=service_ids, is_active=True)
        booking.services.set(services)
        booking.calculate_total_price()
        booking.save()
        return booking


# --- Booking Status Serializers ---

class BookingConfirmSerializer(Serializer):
    """pending → confirmed"""
    def validate(self, attrs):
        if self.instance.status != 'pending':
            raise ValidationError(
                f'Cannot confirm. Current status: "{self.instance.status}". '
                'Only "pending" can be confirmed.'
            )
        return attrs

    def update(self, instance, validated_data):
        instance.status = 'confirmed'
        instance.save()
        return instance


class BookingCompleteSerializer(Serializer):
    """confirmed → completed"""
    def validate(self, attrs):
        if self.instance.status != 'confirmed':
            raise ValidationError(
                f'Cannot complete. Current status: "{self.instance.status}". '
                'Only "confirmed" can be completed.'
            )
        return attrs

    def update(self, instance, validated_data):
        instance.status = 'completed'
        instance.save()
        return instance


class BookingCancelSerializer(Serializer):
    """pending / confirmed → cancelled"""
    reason = CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        if self.instance.status not in ['pending', 'confirmed']:
            raise ValidationError(
                f'Cannot cancel. Current status: "{self.instance.status}". '
                'Only "pending" or "confirmed" can be cancelled.'
            )
        return attrs

    def update(self, instance, validated_data):
        reason = validated_data.get('reason', '')
        instance.status = 'cancelled'
        if reason:
            instance.notes = reason
        instance.save()
        return instance


class BookingBulkSerializer(Serializer):
    """Bulk confirm / complete / cancel"""
    booking_ids = ListField(child=IntegerField(), min_length=1)

    def validate_booking_ids(self, value):
        existing = set(
            Booking.objects.filter(id__in=value).values_list('id', flat=True)
        )
        missing = set(value) - existing
        if missing:
            raise ValidationError(f'Bookings not found: {list(missing)}')
        return value

