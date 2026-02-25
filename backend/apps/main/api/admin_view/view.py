
from logging import getLogger
from datetime import  date as dt_date

from django.shortcuts import get_object_or_404
from django.db.models import Q, Sum
from django.utils import timezone

from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import  AllowAny
from rest_framework.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_403_FORBIDDEN,
)

from drf_spectacular.utils import (
    extend_schema,
    OpenApiParameter,
    OpenApiResponse,
)
from drf_spectacular.types import OpenApiTypes

from main.models import Salon, Master, MasterJobRequest, Booking
from main.api.master_job_request import (
    MasterJobRequestSerializer,
    JobRequestReviewSerializer,
)

from main.permissions import (
    IsAdmin
)
from apps.services.notifications import NotificationService
from apps.services.analytics import AnalyticsService
from apps.services.payment import PaymentService, CancellationPolicy

logger = getLogger(__name__)

# Ставки комиссии: мастер получает 70%, салон — 30%
MASTER_SHARE = 0.70
SALON_SHARE = 0.30


class AdminViewSet(ViewSet):
    """
    Все эндпоинты доступны исключительно пользователям с ролью Admin.

    GET  /api/v2/admin/my-masters/              — мастера своих салонов + статистика
    GET  /api/v2/admin/pending-requests/        — заявки мастеров на рассмотрении
    POST /api/v2/admin/review-request/{id}/     — подтвердить или отклонить заявку
    """

    # Все методы этого ViewSet требуют роль Admin
    permission_classes = [IsAdmin]

    # ── Мастера и их статистика ───────────────────────────────────────────────

    @extend_schema(
        summary="Мои мастера со статистикой [Admin]",
        description=(
            "Возвращает список всех мастеров в салонах текущего администратора. "
            "Для каждого мастера рассчитывается дневная и месячная статистика: "
            "количество бронирований, выручка, заработок мастера (70%) и доля салона (30%).\n\n"
            "**Фильтры:**\n"
            "- `salon_id` — показать только мастеров конкретного салона\n"
            "- `is_approved` — true/false — фильтр по статусу подтверждения"
        ),
        parameters=[
            OpenApiParameter('salon_id', OpenApiTypes.INT, OpenApiParameter.QUERY,
                             description='Фильтр по ID салона', required=False),
            OpenApiParameter('is_approved', OpenApiTypes.BOOL, OpenApiParameter.QUERY,
                             description='Фильтр по статусу подтверждения мастера', required=False),
        ],
        responses={
            200: OpenApiResponse(description="Список мастеров с дневной и месячной статистикой"),
            400: OpenApiResponse(description="У администратора нет ни одного салона"),
        },
        tags=['Admin — мастера'],
    )
    @action(detail=False, methods=['get'], url_path='my-masters')
    def my_masters(self, request):
        """Возвращает мастеров своих салонов с подробной статистикой заработка."""
        # Проверяем, что у администратора есть хотя бы один салон
        salons = Salon.objects.filter(owner=request.user)
        if not salons.exists():
            return Response(
                {'status': 'error', 'message': 'У вас ещё нет ни одного салона.'},
                status=HTTP_400_BAD_REQUEST,
            )

        masters = Master.objects.filter(
            salon__in=salons
        ).select_related('user', 'salon')

        # Опциональный фильтр по конкретному салону
        salon_id = request.query_params.get('salon_id')
        if salon_id:
            masters = masters.filter(salon_id=salon_id)

        # Опциональный фильтр по статусу подтверждения
        is_approved = request.query_params.get('is_approved')
        if is_approved is not None:
            masters = masters.filter(is_approved=is_approved.lower() == 'true')

        today = timezone.now().date()
        month_start = today.replace(day=1)

        result = []
        for master in masters:
            # Статистика завершённых бронирований за сегодня
            today_bookings = Booking.objects.filter(
                master=master.user,
                appointment_date=today,
                status='completed',
            )
            today_revenue = today_bookings.aggregate(total=Sum('total_price'))['total'] or 0

            # Статистика завершённых бронирований за текущий месяц
            month_bookings = Booking.objects.filter(
                master=master.user,
                appointment_date__gte=month_start,
                status='completed',
            )
            month_revenue = month_bookings.aggregate(total=Sum('total_price'))['total'] or 0

            result.append({
                'master_id': master.id,
                'master_name': master.user.full_name,
                'email': master.user.email,
                'phone': master.user.phone,
                'salon': master.salon.name,
                'specialization': master.specialization,
                'experience_years': master.experience_years,
                'is_approved': master.is_approved,
                'today': {
                    'bookings': today_bookings.count(),
                    'revenue_kzt': float(today_revenue),
                    'master_earnings_kzt': round(float(today_revenue) * MASTER_SHARE, 2),
                    'salon_share_kzt': round(float(today_revenue) * SALON_SHARE, 2),
                },
                'month': {
                    'bookings': month_bookings.count(),
                    'revenue_kzt': float(month_revenue),
                    'master_earnings_kzt': round(float(month_revenue) * MASTER_SHARE, 2),
                    'salon_share_kzt': round(float(month_revenue) * SALON_SHARE, 2),
                },
            })

        return Response({
            'status': 'success',
            'count': len(result),
            'data': result,
        })

    # ── Заявки мастеров на рассмотрение ──────────────────────────────────────

    @extend_schema(
        summary="Заявки мастеров на рассмотрении [Admin]",
        description=(
            "Возвращает все заявки мастеров со статусом `pending` "
            "для салонов текущего администратора. "
            "Можно фильтровать по `salon_id` если у администратора несколько салонов."
        ),
        parameters=[
            OpenApiParameter('salon_id', OpenApiTypes.INT, OpenApiParameter.QUERY,
                             description='Фильтр по конкретному салону', required=False),
        ],
        responses={200: MasterJobRequestSerializer(many=True)},
        tags=['Admin — заявки'],
    )
    @action(detail=False, methods=['get'], url_path='pending-requests')
    def pending_requests(self, request):
        """Возвращает список необработанных заявок мастеров для своих салонов."""
        # Выбираем только pending-заявки для салонов текущего администратора
        salons = Salon.objects.filter(owner=request.user)
        pending = MasterJobRequest.objects.filter(
            salon__in=salons,
            status='pending',
        ).select_related('master', 'salon')

        # Опциональный фильтр по конкретному салону
        salon_id = request.query_params.get('salon_id')
        if salon_id:
            pending = pending.filter(salon_id=salon_id)

        serializer = MasterJobRequestSerializer(pending, many=True)
        return Response({
            'status': 'success',
            'count': pending.count(),
            'data': serializer.data,
        })

    @extend_schema(
        summary="Рассмотреть заявку мастера [Admin]",
        description=(
            "Подтверждает (`approve`) или отклоняет (`reject`) заявку мастера.\n\n"
            "**При подтверждении:**\n"
            "- Создаётся или обновляется профиль мастера в салоне\n"
            "- Мастер получает email-уведомление об одобрении\n\n"
            "**При отклонении:**\n"
            "- Необходимо указать `rejection_reason`\n"
            "- Мастер получает email с причиной отказа\n\n"
            "⚠️ `{id}` в URL — это ID заявки (`MasterJobRequest`), а не ID пользователя."
        ),
        request=JobRequestReviewSerializer,
        responses={
            200: MasterJobRequestSerializer,
            400: OpenApiResponse(description="Заявка уже была рассмотрена ранее"),
            403: OpenApiResponse(description="Можно рассматривать только заявки своих салонов"),
            404: OpenApiResponse(description="Заявка не найдена"),
        },
        tags=['Admin — заявки'],
    )
    @action(detail=True, methods=['post'], url_path='review-request')
    def review_request(self, request, pk=None):
        """Подтверждает или отклоняет заявку мастера. При подтверждении создаёт профиль мастера."""
        job_request = get_object_or_404(MasterJobRequest, pk=pk)

        # Администратор может рассматривать только заявки в свои салоны
        if job_request.salon.owner != request.user:
            return Response(
                {'status': 'error', 'message': 'Можно рассматривать только заявки своих салонов'},
                status=HTTP_403_FORBIDDEN,
            )

        # Заявку можно рассмотреть только один раз
        if job_request.status != 'pending':
            return Response(
                {'status': 'error', 'message': f'Заявка уже обработана: статус «{job_request.status}»'},
                status=HTTP_400_BAD_REQUEST,
            )

        review_serializer = JobRequestReviewSerializer(data=request.data)
        review_serializer.is_valid(raise_exception=True)

        action_type = review_serializer.validated_data['action']
        rejection_reason = review_serializer.validated_data.get('rejection_reason', '')

        if action_type == 'approve':
            # Обновляем статус заявки на approved
            job_request.status = 'approved'
            job_request.reviewed_by = request.user
            job_request.reviewed_at = timezone.now()
            job_request.save()

            # Создаём профиль мастера или обновляем существующий
            master_obj, created = Master.objects.get_or_create(
                user=job_request.master,
                defaults={
                    'salon': job_request.salon,
                    'specialization': job_request.specialization,
                    'experience_years': job_request.experience_years,
                    'bio': job_request.bio,
                    'is_approved': True,
                },
            )
            if not created:
                # Мастер уже существует — обновляем данные по заявке
                master_obj.salon = job_request.salon
                master_obj.specialization = job_request.specialization
                master_obj.experience_years = job_request.experience_years
                master_obj.bio = job_request.bio
                master_obj.is_approved = True
                master_obj.save()

            # Отправляем мастеру email об одобрении заявки
            NotificationService.send_job_request_approved(job_request)

            logger.info(
                "Заявка ОДОБРЕНА: мастер=%s, салон=%s, admin=%s",
                job_request.master.email, job_request.salon.name, request.user.email,
            )
            return Response({
                'status': 'success',
                'message': (
                    f'{job_request.master.full_name} принят как мастер '
                    f'в салон «{job_request.salon.name}».'
                ),
                'data': MasterJobRequestSerializer(job_request).data,
            })

        else:  # reject
            # Обновляем статус заявки на rejected с указанием причины
            job_request.status = 'rejected'
            job_request.rejection_reason = rejection_reason
            job_request.reviewed_by = request.user
            job_request.reviewed_at = timezone.now()
            job_request.save()

            # Отправляем мастеру email с причиной отказа
            NotificationService.send_job_request_rejected(job_request)

            logger.info(
                "Заявка ОТКЛОНЕНА: мастер=%s, салон=%s, причина=%s",
                job_request.master.email, job_request.salon.name, rejection_reason,
            )
            return Response({
                'status': 'success',
                'message': f'Заявка от {job_request.master.full_name} отклонена.',
                'data': MasterJobRequestSerializer(job_request).data,
            })


