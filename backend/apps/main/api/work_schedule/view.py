
from logging import getLogger
from datetime import datetime, timedelta, date as dt_date

from django.shortcuts import get_object_or_404


from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import  AllowAny
from rest_framework.status import (
    HTTP_201_CREATED,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
)

from drf_spectacular.utils import (
    extend_schema,
    OpenApiParameter,
    OpenApiResponse,
)
from drf_spectacular.types import OpenApiTypes

from apps.main.models import Booking, WorkSchedule
from .serializers import (
    WorkScheduleSerializer,
    WorkScheduleUpdateSerializer,
)
from apps.main.permissions import (
    CanManageWorkSchedule,
)

logger = getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════════════
#  WorkScheduleViewSet  —  рабочее расписание мастеров
# ══════════════════════════════════════════════════════════════════════════════

class WorkScheduleViewSet(ViewSet):
    """
    Управление рабочим расписанием.
    Admin видит все расписания, мастер — только своё.
    """

    permission_classes = [CanManageWorkSchedule]

    @extend_schema(
        summary="Список расписаний",
        description="Admin получает все расписания. Мастер — только своё.",
        responses={200: WorkScheduleSerializer(many=True)},
        tags=['Расписание'],
    )
    def list(self, request):
        """Возвращает расписания: все — для Admin, только своё — для Master."""
        if request.user.is_admin:
            queryset = WorkSchedule.objects.all()
        else:
            queryset = WorkSchedule.objects.filter(master=request.user)
        serializer = WorkScheduleSerializer(queryset.select_related('master'), many=True)
        return Response({
            'status': 'success',
            'count': queryset.count(),
            'data': serializer.data,
        })

    @extend_schema(
        summary="Детали расписания на день",
        responses={200: WorkScheduleSerializer},
        tags=['Расписание'],
    )
    def retrieve(self, request, pk=None):
        """Возвращает расписание на конкретный день. Проверяет права доступа."""
        schedule = get_object_or_404(WorkSchedule, pk=pk)
        self.check_object_permissions(request, schedule)
        return Response({'status': 'success', 'data': WorkScheduleSerializer(schedule).data})

    @extend_schema(
        summary="Создать расписание на день",
        request=WorkScheduleUpdateSerializer,
        responses={201: WorkScheduleSerializer},
        tags=['Расписание'],
    )
    def create(self, request):
        """Создаёт запись расписания для мастера на указанный день недели."""
        serializer = WorkScheduleUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        schedule = serializer.save()
        return Response({
            'status': 'success',
            'message': 'Расписание создано',
            'data': WorkScheduleSerializer(schedule).data,
        }, status=HTTP_201_CREATED)

    @extend_schema(
        summary="Обновить расписание",
        request=WorkScheduleUpdateSerializer,
        responses={200: WorkScheduleSerializer},
        tags=['Расписание'],
    )
    def update(self, request, pk=None):
        """Полностью обновляет расписание на день (PUT)."""
        schedule = get_object_or_404(WorkSchedule, pk=pk)
        self.check_object_permissions(request, schedule)
        serializer = WorkScheduleUpdateSerializer(schedule, data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)
        schedule = serializer.save()
        return Response({'status': 'success', 'data': WorkScheduleSerializer(schedule).data})

    @extend_schema(
        summary="Частично обновить расписание",
        description="Обновляет отдельные поля расписания, например флаг is_working (PATCH).",
        request=WorkScheduleUpdateSerializer,
        responses={200: WorkScheduleSerializer},
        tags=['Расписание'],
    )
    def partial_update(self, request, pk=None):
        """Частично обновляет расписание (PATCH). Удобно для включения/выключения рабочего дня."""
        schedule = get_object_or_404(WorkSchedule, pk=pk)
        self.check_object_permissions(request, schedule)
        serializer = WorkScheduleUpdateSerializer(schedule, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        schedule = serializer.save()
        return Response({'status': 'success', 'data': WorkScheduleSerializer(schedule).data})

    @extend_schema(
        summary="Удалить расписание",
        responses={204: OpenApiResponse(description="Расписание удалено")},
        tags=['Расписание'],
    )
    def destroy(self, request, pk=None):
        """Удаляет запись расписания для указанного дня."""
        schedule = get_object_or_404(WorkSchedule, pk=pk)
        self.check_object_permissions(request, schedule)
        schedule.delete()
        return Response(
            {'status': 'success', 'message': 'Расписание удалено'},
            status=HTTP_204_NO_CONTENT,
        )

    @extend_schema(
        summary="Расписание мастера по его ID",
        description="Возвращает полное недельное расписание мастера, отсортированное по дням.",
        responses={200: WorkScheduleSerializer(many=True)},
        tags=['Расписание'],
    )
    @action(detail=False, methods=['get'], url_path='master/(?P<master_id>[^/.]+)')
    def by_master(self, request, master_id=None):
        """Возвращает все записи расписания мастера, упорядоченные по дням недели."""
        schedules = WorkSchedule.objects.filter(master_id=master_id).order_by('weekday')
        if not schedules.exists():
            return Response(
                {'status': 'error', 'message': 'Расписание для этого мастера не найдено'},
                status=HTTP_400_BAD_REQUEST,
            )
        return Response({
            'status': 'success',
            'master_id': int(master_id),
            'count': schedules.count(),
            'data': WorkScheduleSerializer(schedules, many=True).data,
        })

    @extend_schema(
        summary="Свободные слоты мастера на дату",
        description=(
            "Возвращает список свободных и занятых временных слотов мастера на конкретную дату. "
            "Слоты генерируются с интервалом 30 минут в пределах рабочего времени."
        ),
        parameters=[
            OpenApiParameter('master_id', OpenApiTypes.INT, OpenApiParameter.QUERY,
                             description='ID пользователя-мастера', required=True),
            OpenApiParameter('date', OpenApiTypes.DATE, OpenApiParameter.QUERY,
                             description='Дата в формате YYYY-MM-DD', required=True),
        ],
        responses={200: OpenApiResponse(description="Свободные и занятые слоты")},
        tags=['Расписание'],
    )
    @action(detail=False, methods=['get'], url_path='available-slots')
    def available_slots(self, request):
        """Возвращает свободные временные слоты мастера на указанную дату."""
        master_id = request.query_params.get('master_id')
        date_str = request.query_params.get('date')

        if not master_id or not date_str:
            return Response(
                {'status': 'error', 'message': 'Необходимо указать master_id и date'},
                status=HTTP_400_BAD_REQUEST,
            )
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            weekday = date_obj.weekday()

            schedule = WorkSchedule.objects.filter(
                master_id=master_id, weekday=weekday
            ).first()

            # Если мастер не работает в этот день — возвращаем соответствующий ответ
            if not schedule or not schedule.is_working:
                return Response({
                    'status': 'success',
                    'master_id': int(master_id),
                    'date': date_str,
                    'weekday': date_obj.strftime('%A'),
                    'working': False,
                    'message': 'Мастер не работает в этот день',
                })

            # Генерируем все возможные слоты в рамках рабочего дня
            all_slots = self._generate_time_slots(schedule.start_time, schedule.end_time)

            # Получаем уже занятые слоты (pending и confirmed бронирования)
            booked_times = Booking.objects.filter(
                master_id=master_id,
                appointment_date=date_obj,
                status__in=['pending', 'confirmed'],
            ).values_list('appointment_time', flat=True)
            booked_slots = [t.strftime('%H:%M') for t in booked_times]

            # Вычитаем занятые слоты из всех возможных
            available_slots = [s for s in all_slots if s not in booked_slots]

            return Response({
                'status': 'success',
                'master_id': int(master_id),
                'date': date_str,
                'weekday': date_obj.strftime('%A'),
                'working': True,
                'work_hours': {
                    'start': schedule.start_time.strftime('%H:%M'),
                    'end': schedule.end_time.strftime('%H:%M'),
                },
                'total_slots': len(all_slots),
                'available_slots': available_slots,
                'booked_slots': booked_slots,
            })

        except ValueError:
            return Response(
                {'status': 'error', 'message': 'Неверный формат даты. Используйте YYYY-MM-DD'},
                status=HTTP_400_BAD_REQUEST,
            )

    def _generate_time_slots(self, start_time, end_time, interval_minutes=30):
        """Генерирует список временных меток с заданным интервалом между start_time и end_time."""
        slots = []
        current = datetime.combine(datetime.today(), start_time)
        end = datetime.combine(datetime.today(), end_time)
        while current < end:
            slots.append(current.strftime('%H:%M'))
            current += timedelta(minutes=interval_minutes)
        return slots
