from logging import getLogger
from datetime import timedelta, date as dt_date

from django.shortcuts import get_object_or_404
from django.db.models import Q, Sum
from django.utils import timezone

from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_204_NO_CONTENT,
    HTTP_403_FORBIDDEN,
)

from drf_spectacular.utils import (
    extend_schema,
    OpenApiParameter,
    OpenApiResponse,
)
from drf_spectacular.types import OpenApiTypes

from main.models import  Master, MasterJobRequest
from api.master.serializers import (
    MasterSerializer,
    MasterJobRequestSerializer,
    MasterJobRequestCreateSerializer,
)
from main.permissions import (
    IsAdmin,
)
from apps.services.notifications import NotificationService
from main.models import Booking


logger = getLogger(__name__)

# Ставки комиссии: мастер получает 70%, салон — 30%
MASTER_SHARE = 0.70
SALON_SHARE = 0.30


# ══════════════════════════════════════════════════════════════════════════════
#  MasterViewSet  —  публичные эндпоинты + личный кабинет мастера
# ══════════════════════════════════════════════════════════════════════════════

class MasterViewSet(ViewSet):
    """
    Эндпоинты для мастеров и публичного просмотра.

    Публичные (без авторизации):
      GET  /api/v2/master/          — список подтверждённых мастеров
      GET  /api/v2/master/{id}/     — профиль мастера

    Только для мастеров (role=master):
      POST /api/v2/master/send-job-request/ — отправить заявку в салон
      GET  /api/v2/master/my-requests/      — мои заявки в салоны
      GET  /api/v2/master/my-earnings/      — мой заработок за период
    """

    def get_permissions(self):
        """Определяет права доступа в зависимости от выполняемого действия."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdmin()]
        return [IsAuthenticated()]

    # ── Публичный CRUD ────────────────────────────────────────────────────────

    @extend_schema(
        summary="Список подтверждённых мастеров",
        description="Возвращает всех мастеров со статусом is_approved=True. "
                    "Доступно без авторизации. Фильтрация по салону и специализации.",
        parameters=[
            OpenApiParameter('salon_id', OpenApiTypes.INT, OpenApiParameter.QUERY,
                             description='Фильтр по ID салона', required=False),
            OpenApiParameter('specialization', OpenApiTypes.STR, OpenApiParameter.QUERY,
                             description='Фильтр по специализации (частичное совпадение)',
                             required=False),
        ],
        responses={200: MasterSerializer(many=True)},
        tags=['Мастера'],
    )
    def list(self, request):
        """Возвращает список всех подтверждённых мастеров с возможностью фильтрации."""
        queryset = Master.objects.filter(
            is_approved=True
        ).select_related('salon', 'user')

        # Фильтр по салону
        salon_id = request.query_params.get('salon_id')
        if salon_id:
            queryset = queryset.filter(salon_id=salon_id)

        # Фильтр по специализации (регистронезависимый поиск)
        specialization = request.query_params.get('specialization')
        if specialization:
            queryset = queryset.filter(specialization__icontains=specialization)

        serializer = MasterSerializer(queryset, many=True)
        return Response({
            'status': 'success',
            'count': queryset.count(),
            'data': serializer.data,
        }, status=HTTP_200_OK)

    @extend_schema(
        summary="Профиль мастера по ID",
        description="Возвращает подробную информацию об одном подтверждённом мастере.",
        responses={
            200: MasterSerializer,
            404: OpenApiResponse(description="Мастер не найден или не подтверждён"),
        },
        tags=['Мастера'],
    )
    def retrieve(self, request, pk=None):
        """Возвращает профиль конкретного мастера. Доступно без авторизации."""
        master = get_object_or_404(
            Master.objects.select_related('salon', 'user'),
            pk=pk,
            is_approved=True,
        )
        serializer = MasterSerializer(master)
        return Response({'status': 'success', 'data': serializer.data})

    @extend_schema(
        summary="Удалить мастера [Admin]",
        description="Удаляет профиль мастера и связанный аккаунт пользователя. Только для Admin.",
        responses={
            204: OpenApiResponse(description="Мастер успешно удалён"),
            403: OpenApiResponse(description="Нет прав доступа"),
            404: OpenApiResponse(description="Мастер не найден"),
        },
        tags=['Мастера'],
    )
    def destroy(self, request, pk=None):
        """Удаляет мастера и его пользовательский аккаунт. Действие необратимо."""
        master = get_object_or_404(Master, pk=pk)
        user = master.user
        master.delete()
        user.delete()
        logger.warning(
            "Мастер удалён: master_id=%s, выполнил admin=%s", pk, request.user.email
        )
        return Response(
            {'status': 'success', 'message': 'Мастер удалён'},
            status=HTTP_204_NO_CONTENT,
        )

    # ── Заявки в салон ────────────────────────────────────────────────────────

    @extend_schema(
        summary="Отправить заявку в салон [Master]",
        description=(
            "Мастер отправляет заявку на работу в выбранный салон вместе с резюме. "
            "Обязательно: `salon_id` и хотя бы одно из полей: `specialization` или `offered_services`. "
            "После отправки администратор салона получает email-уведомление. "
            "Если предыдущая заявка в этот салон была отклонена — она автоматически удаляется."
        ),
        request=MasterJobRequestCreateSerializer,
        responses={
            201: MasterJobRequestSerializer,
            400: OpenApiResponse(description="Ошибка валидации данных"),
            403: OpenApiResponse(description="Только для пользователей с ролью master"),
        },
        tags=['Мастера — заявки'],
    )
    @action(
        detail=False,
        methods=['post'],
        url_path='send-job-request',
        permission_classes=[IsAuthenticated],
    )
    def send_job_request(self, request):
        """Создаёт заявку на работу в салон и отправляет уведомление администратору."""
        serializer = MasterJobRequestCreateSerializer(
            data=request.data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        job_request = serializer.save()

        # Отправляем email администратору салона о новой заявке
        NotificationService.send_job_request_to_admin(job_request)

        logger.info(
            "Создана заявка: мастер=%s → салон=%s (id=%s)",
            request.user.email, job_request.salon.name, job_request.id,
        )
        return Response(
            {
                'status': 'success',
                'message': (
                    f'Ваша заявка отправлена в салон «{job_request.salon.name}». '
                    'Администратор рассмотрит её в ближайшее время.'
                ),
                'data': MasterJobRequestSerializer(job_request).data,
            },
            status=HTTP_201_CREATED,
        )

    @extend_schema(
        summary="Мои заявки в салоны [Master]",
        description="Возвращает список всех заявок текущего мастера. "
                    "Можно фильтровать по статусу: pending, approved, rejected.",
        parameters=[
            OpenApiParameter(
                'status', OpenApiTypes.STR, OpenApiParameter.QUERY,
                description='Фильтр по статусу заявки',
                required=False,
                enum=['pending', 'approved', 'rejected'],
            ),
        ],
        responses={
            200: MasterJobRequestSerializer(many=True),
            403: OpenApiResponse(description="Только для пользователей с ролью master"),
        },
        tags=['Мастера — заявки'],
    )
    @action(
        detail=False,
        methods=['get'],
        url_path='my-requests',
        permission_classes=[IsAuthenticated],
    )
    def my_requests(self, request):
        """Возвращает все заявки текущего мастера с возможной фильтрацией по статусу."""
        if not request.user.is_master:
            return Response(
                {'status': 'error', 'message': 'Доступно только для мастеров'},
                status=HTTP_403_FORBIDDEN,
            )

        requests_qs = MasterJobRequest.objects.filter(
            master=request.user
        ).select_related('salon', 'reviewed_by')

        # Необязательный фильтр по статусу заявки
        status_filter = request.query_params.get('status')
        if status_filter:
            requests_qs = requests_qs.filter(status=status_filter)

        serializer = MasterJobRequestSerializer(requests_qs, many=True)
        return Response({
            'status': 'success',
            'count': requests_qs.count(),
            'data': serializer.data,
        })

    # ── Личный кабинет мастера — заработок ───────────────────────────────────

    @extend_schema(
        summary="Мой заработок [Master]",
        description=(
            "Возвращает статистику заработка текущего мастера за выбранный период. "
            "Мастер получает **70%** от суммы каждого завершённого бронирования.\n\n"
            "**Параметр `period`:**\n"
            "- `today` — только сегодня\n"
            "- `week` — последние 7 дней\n"
            "- `month` — текущий месяц *(по умолчанию)*\n\n"
            "Ответ содержит: сводку (`summary`), разбивку по дням (`daily_breakdown`) "
            "и последние 10 бронирований (`recent_bookings`)."
        ),
        parameters=[
            OpenApiParameter(
                'period', OpenApiTypes.STR, OpenApiParameter.QUERY,
                description='Период статистики (по умолчанию: month)',
                required=False,
                enum=['today', 'week', 'month'],
            ),
        ],
        responses={
            200: OpenApiResponse(description="Статистика заработка мастера"),
            403: OpenApiResponse(description="Только для пользователей с ролью master"),
        },
        tags=['Мастера — заработок'],
    )
    @action(
        detail=False,
        methods=['get'],
        url_path='my-earnings',
        permission_classes=[IsAuthenticated],
    )
    def my_earnings(self, request):
        """Возвращает детальную статистику заработка текущего мастера за выбранный период."""
        if not request.user.is_master:
            return Response(
                {'status': 'error', 'message': 'Доступно только для мастеров'},
                status=HTTP_403_FORBIDDEN,
            )

        # Получаем профиль мастера для отображения информации о салоне
        master_profile = getattr(request.user, 'master_profile', None)

        today = timezone.now().date()
        period = request.query_params.get('period', 'month')

        # Определяем начальную дату диапазона по переданному периоду
        if period == 'today':
            date_from = today
            period_label = 'Сегодня'
        elif period == 'week':
            date_from = today - timedelta(days=6)
            period_label = 'Последние 7 дней'
        else:  # month — значение по умолчанию
            date_from = today.replace(day=1)
            period_label = 'Текущий месяц'

        # Выбираем только завершённые бронирования мастера за период
        bookings = Booking.objects.filter(
            master=request.user,
            appointment_date__gte=date_from,
            status='completed',
        ).prefetch_related('services').order_by('-appointment_date', '-appointment_time')

        # Считаем итоговую выручку и долю мастера
        total_revenue = bookings.aggregate(total=Sum('total_price'))['total'] or 0
        total_earnings = round(float(total_revenue) * MASTER_SHARE, 2)
        salon_share = round(float(total_revenue) * SALON_SHARE, 2)

        # Группируем статистику по дням для построения графика
        daily_breakdown = {}
        for booking in bookings:
            day_str = booking.appointment_date.strftime('%Y-%m-%d')
            if day_str not in daily_breakdown:
                daily_breakdown[day_str] = {
                    'date': day_str,
                    'bookings': 0,
                    'revenue_kzt': 0.0,
                    'earnings_kzt': 0.0,
                }
            daily_breakdown[day_str]['bookings'] += 1
            daily_breakdown[day_str]['revenue_kzt'] += float(booking.total_price)
            daily_breakdown[day_str]['earnings_kzt'] += round(
                float(booking.total_price) * MASTER_SHARE, 2
            )

        # Формируем последние 10 бронирований для отображения в истории
        recent_bookings = [
            {
                'booking_code': b.booking_code,
                'date': b.appointment_date.strftime('%Y-%m-%d'),
                'time': b.appointment_time.strftime('%H:%M'),
                'client': b.client.full_name,
                'services': [s.name for s in b.services.all()],
                'total_kzt': float(b.total_price),
                'my_earnings_kzt': round(float(b.total_price) * MASTER_SHARE, 2),
            }
            for b in bookings[:10]
        ]

        return Response({
            'status': 'success',
            'master': {
                'id': request.user.id,
                'full_name': request.user.full_name,
                'salon': master_profile.salon.name if master_profile else None,
                'specialization': master_profile.specialization if master_profile else None,
            },
            'period': period_label,
            'date_from': date_from.strftime('%Y-%m-%d'),
            'date_to': today.strftime('%Y-%m-%d'),
            'commission_rate': f'{int(MASTER_SHARE * 100)}%',
            'summary': {
                'total_bookings': bookings.count(),
                'total_revenue_kzt': float(total_revenue),
                'my_earnings_kzt': total_earnings,
                'salon_share_kzt': salon_share,
            },
            'daily_breakdown': list(daily_breakdown.values()),
            'recent_bookings': recent_bookings,
        })
