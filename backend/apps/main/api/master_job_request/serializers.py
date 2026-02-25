from rest_framework.serializers import (
    Serializer,
    CharField,
    IntegerField,
    FloatField,
    ModelSerializer,
    SerializerMethodField,
)
from django.conf import settings

from apps.main.models import (
    Salon,
    MasterJobRequest,
)
from django.core.exceptions import ValidationError

User = settings.AUTH_USER_MODEL


class MasterJobRequestCreateSerializer(Serializer):
    """
    Master салонға жұмыс сұрауын жіберу (резюмемен).

    Мастер міндетті түрде:
    - salon_id  жіберуі керек
    - specialization  немесе  offered_services  толтыруы керек

    Қосымша:
    - experience_years, bio, expected_salary, answers
    """

    salon_id = IntegerField()
    specialization = CharField(max_length=255, required=False, allow_blank=True, default='')
    experience_years = IntegerField(default=0, required=False, min_value=0)
    bio = CharField(required=False, allow_blank=True, default='')
    offered_services = CharField(
        required=False,
        allow_blank=True,
        default='',
        help_text="Comma-separated: Haircut, Beard Trim, Coloring"
    )
    expected_salary = FloatField(required=False, allow_null=True, default=None, min_value=0)
    answers = CharField(
        required=False,
        allow_blank=True,
        default='',
        help_text="JSON string of {question: answer} pairs from salon requirements"
    )

    def validate_salon_id(self, value):
        if not Salon.objects.filter(id=value, is_active=True).exists():
            raise ValidationError('Salon not found or inactive.')
        return value

    def validate(self, attrs):
        request = self.context.get('request')

        if not request or not request.user.is_authenticated:
            raise ValidationError('Authentication required.')

        if not request.user.is_master:
            raise ValidationError(
                'Only users with master role can send job requests. '
                'Register/login as master first.'
            )

        salon_id = attrs.get('salon_id')
        if salon_id:
            # Бұрын жіберілген сұрау бар ма?
            existing = MasterJobRequest.objects.filter(
                master=request.user,
                salon_id=salon_id
            ).first()
            if existing:
                if existing.status == 'pending':
                    raise ValidationError(
                        'You already have a pending request to this salon.'
                    )
                if existing.status == 'approved':
                    raise ValidationError(
                        'You are already working at this salon.'
                    )
                # rejected болса қайта жіберуге болады (жоюды жаңа object жасауды)

        # specialization немесе offered_services міндетті
        specialization = attrs.get('specialization', '').strip()
        offered_services = attrs.get('offered_services', '').strip()
        if not specialization and not offered_services:
            raise ValidationError(
                'Please provide at least specialization or offered_services.'
            )

        return attrs

    def create(self, validated_data):
        import json
        request = self.context.get('request')
        user = request.user

        salon_id = validated_data['salon_id']
        salon = Salon.objects.get(id=salon_id)

        # Rejected болса ескісін жойып жаңасын жасаймыз
        MasterJobRequest.objects.filter(
            master=user, salon=salon, status='rejected'
        ).delete()

        # answers — JSON string немесе dict
        raw_answers = validated_data.get('answers', '')
        if isinstance(raw_answers, str) and raw_answers.strip():
            try:
                answers = json.loads(raw_answers)
            except Exception:
                # Дұрыс JSON болмаса бос dict
                answers = {}
        elif isinstance(raw_answers, dict):
            answers = raw_answers
        else:
            answers = {}

        job_request = MasterJobRequest.objects.create(
            master=user,
            salon=salon,
            specialization=validated_data.get('specialization', ''),
            experience_years=validated_data.get('experience_years', 0),
            bio=validated_data.get('bio', ''),
            offered_services=validated_data.get('offered_services', ''),
            expected_salary=validated_data.get('expected_salary'),
            answers=answers,
            status='pending',
        )
        return job_request


class JobRequestReviewSerializer(Serializer):
    """Admin job request-ті қарайды: approve немесе reject"""
    action = CharField()   # 'approve' | 'reject'
    rejection_reason = CharField(required=False, allow_blank=True, default='')

    def validate_action(self, value):
        if value not in ('approve', 'reject'):
            raise ValidationError("action must be 'approve' or 'reject'.")
        return value

    def validate(self, attrs):
        if attrs['action'] == 'reject' and not attrs.get('rejection_reason', '').strip():
            raise ValidationError(
                {'rejection_reason': 'Rejection reason is required when rejecting.'}
            )
        return attrs


class MasterJobRequestSerializer(ModelSerializer):
    """Serializer for displaying MasterJobRequest instances (admin views)."""
    master = SerializerMethodField()
    salon = SerializerMethodField()

    class Meta:
        model = MasterJobRequest
        fields = [
            'id', 'master', 'salon', 'specialization', 'experience_years',
            'bio', 'offered_services', 'expected_salary', 'answers',
            'status', 'rejection_reason', 'created_at', 'updated_at',
            'reviewed_at', 'reviewed_by',
        ]

    def get_master(self, obj):
        u = obj.master
        return {
            'id': getattr(u, 'id', None),
            'full_name': getattr(u, 'full_name', ''),
            'email': getattr(u, 'email', ''),
            'phone': getattr(u, 'phone', ''),
        }

    def get_salon(self, obj):
        s = obj.salon
        return {
            'id': getattr(s, 'id', None),
            'name': getattr(s, 'name', ''),
        }


