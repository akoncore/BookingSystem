
from rest_framework.serializers import (
    ModelSerializer,
    SerializerMethodField,
    ValidationError,
)
from django.conf import settings

from apps.main.models import (
    WorkSchedule,
)

User = settings.AUTH_USER_MODEL


# ─── WorkSchedule Serializers ────────────────────────────────────────────────

class WorkScheduleSerializer(ModelSerializer):
    """WorkSchedule толық сериализаторы"""
    weekday_display = SerializerMethodField()

    class Meta:
        model = WorkSchedule
        fields = [
            'id', 'master', 'weekday', 'weekday_display',
            'start_time', 'end_time', 'is_working',
        ]
        read_only_fields = ['id']

    def get_weekday_display(self, obj):
        return obj.get_weekday_display()


class WorkScheduleUpdateSerializer(ModelSerializer):
    """WorkSchedule жаңарту сериализаторы"""
    class Meta:
        model = WorkSchedule
        fields = ['start_time', 'end_time', 'is_working']

    def validate(self, attrs):
        start_time = attrs.get('start_time')
        end_time = attrs.get('end_time')
        if start_time and end_time and start_time >= end_time:
            raise ValidationError('Start time must be before end time.')
        return attrs

    def update(self, instance, validated_data):
        instance.start_time = validated_data.get('start_time', instance.start_time)
        instance.end_time = validated_data.get('end_time', instance.end_time)
        instance.is_working = validated_data.get('is_working', instance.is_working)
        instance.save()
        return instance

    def create(self, validated_data):
        return WorkSchedule.objects.create(**validated_data)