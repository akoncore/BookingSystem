# main/serializers.py

from rest_framework.serializers import (
    Serializer,
    ModelSerializer,
    SerializerMethodField,
    CharField,
    ListField,
    IntegerField,
    ValidationError,
)

from .models import (
    Salon,
    Master,
    Service,
    Booking,
    WorkSchedule,
)


# MasterSerializer
class MasterSerializer(ModelSerializer):
    """MasterSerializer"""

    user_info = SerializerMethodField()
    salon_info = SerializerMethodField()

    class Meta:
        model = Master
        fields = [
            'id',
            'user_info',
            'salon_info',
            'specialization',
            'experience_years',
            'bio',
            'is_approved',
            'created_at',
            'updated_at',
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


class MasterRequestSerializer(Serializer):
    """
    Master sends job request to salon
    """

    salon_id = IntegerField()
    specialization = CharField(max_length=255, required=False, allow_blank=True)
    experience_years = IntegerField(default=0, required=False)
    bio = CharField(required=False, allow_blank=True)

    def validate_salon_id(self, value):
        """Check if salon exists"""
        if not Salon.objects.filter(id=value, is_active=True).exists():
            raise ValidationError('Salon not found or inactive')
        return value

    def validate(self, attrs):
        request = self.context.get('request')

        # Check if user is authenticated and has master role
        if not request or not request.user.is_authenticated:
            raise ValidationError('Authentication required')

        if not request.user.is_master:
            raise ValidationError('Only users with master role can send job requests')

        # Check if user already has master profile
        if hasattr(request.user, 'master_profile'):
            raise ValidationError('You already have a master profile')

        return attrs

    def create(self, validated_data):
        """Create Master profile (pending approval)"""
        from django.db import transaction

        request = self.context.get('request')
        user = request.user

        salon_id = validated_data['salon_id']
        specialization = validated_data.get('specialization', '')
        experience_years = validated_data.get('experience_years', 0)
        bio = validated_data.get('bio', '')

        with transaction.atomic():
            salon = Salon.objects.get(id=salon_id)
            master = Master.objects.create(
                user=user,
                salon=salon,
                specialization=specialization,
                experience_years=experience_years,
                bio=bio,
                is_approved=False  # Waiting for Admin approval
            )

            return master


# ServiceSerializer
class ServiceSerializer(ModelSerializer):
    """ServiceSerializer"""

    salon_info = SerializerMethodField()

    class Meta:
        model = Service
        fields = [
            'id',
            'name',
            'description',
            'price',
            'duration',
            'salon_info',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'is_active', 'created_at', 'updated_at']

    def get_salon_info(self, obj):
        salon = obj.salon
        return {
            'id': salon.id,
            'name': salon.name,
            'address': salon.address,
        }


# SalonSerializer
class SalonSerializer(ModelSerializer):
    """SalonSerializer"""

    masters = MasterSerializer(many=True, read_only=True)
    services = ServiceSerializer(many=True, read_only=True)
    master_count = SerializerMethodField()
    service_count = SerializerMethodField()

    class Meta:
        model = Salon
        fields = [
            'id',
            'salon_code',
            'name',
            'address',
            'phone',
            'description',
            'is_active',
            'masters',
            'services',
            'master_count',
            'service_count',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id','salon_code',
            'is_active',
            'created_at',
            'updated_at'
        ]

    def get_master_count(self, obj):
        return obj.masters.filter(is_approved=True).count()

    def get_service_count(self, obj):
        return obj.services.filter(is_active=True).count()


# BookingSerializer
class BookingSerializer(ModelSerializer):
    """BookingSerializer"""

    client_info = SerializerMethodField()
    master_info = SerializerMethodField()
    service_info = SerializerMethodField()
    total_price = SerializerMethodField()
    status_info = SerializerMethodField()

    class Meta:
        model = Booking
        fields = [
            'id',
            'booking_code',
            'client_info',
            'master_info',
            'service_info',
            'appointment_date',
            'appointment_time',
            'status',
            'status_info',
            'total_price',
            'notes',
            'created_at',
            'updated_at',
        ]

    def get_client_info(self, obj):
        client = obj.client
        return {
            'id': client.id,
            'full_name': client.full_name,
            'email': client.email,
            'phone': client.phone,
        }

    def get_master_info(self, obj):
        master = obj.master
        master_profile = getattr(master, 'master_profile', None)
        return {
            'id': master.id,
            'full_name': master.full_name,
            'email': master.email,
            'specialization': master_profile.specialization if master_profile else None,
            'salon': master_profile.salon.name if master_profile else None,
        }

    def get_service_info(self, obj):
        services = obj.services.all()
        return [
            {
                'id': service.id,
                'name': service.name,
                'price': service.price,
                'duration': str(service.duration),
            }
            for service in services
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


# Booking Status Serializers
class BookingConfirmSerializer(Serializer):
    """pending → confirmed"""

    def validate(self, attrs):
        if self.instance.status != 'pending':
            raise Exception(
                f'Cannot confirm. Current status: "{self.instance.status}". '
                f'Only "pending" can be confirmed.'
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
            raise Exception(
                f'Cannot complete. Current status: "{self.instance.status}". '
                f'Only "confirmed" can be completed.'
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
            raise Exception(
                f'Cannot cancel. Current status: "{self.instance.status}". '
                f'Only "pending" or "confirmed" can be cancelled.'
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

    booking_ids = ListField(
        child=IntegerField(),
        min_length=1,
    )

    def validate_booking_ids(self, value):
        existing = set(
            Booking.objects.filter(id__in=value).values_list('id', flat=True)
        )
        missing = set(value) - existing
        if missing:
            raise Exception(f'Bookings not found: {list(missing)}')
        return value


# WorkScheduleSerializer
class WorkScheduleSerializer(ModelSerializer):
    """WorkScheduleSerializer"""

    weekday_display = SerializerMethodField()

    class Meta:
        model = WorkSchedule
        fields = [
            'id',
            'master',
            'weekday',
            'weekday_display',
            'start_time',
            'end_time',
            'is_working',
        ]
        read_only_fields = ['id']

    def get_weekday_display(self, obj):
        return obj.get_weekday_display()