
from logging import getLogger
from datetime import datetime, timedelta, date as dt_date

from django.shortcuts import get_object_or_404

from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
    HTTP_403_FORBIDDEN,
)

from drf_spectacular.utils import (
    extend_schema,
    OpenApiParameter,
    OpenApiResponse,
)
from drf_spectacular.types import OpenApiTypes

from main.models import Salon,Booking, WorkSchedule
from .serializers import (
    BookingSerializer,
    BookingCreateSerializer,
    BookingConfirmSerializer,
    BookingCompleteSerializer,
    BookingBulkSerializer,
)
from main.permissions import (
    IsClient,
    IsMaster,
)
from apps.services.notifications import NotificationService
from apps.services.payment import PaymentService, CancellationPolicy

logger = getLogger(__name__)



# ══════════════════════════════════════════════════════════════════════════════
#  BookingViewSet  —  полный жизненный цикл бронирования
# ══════════════════════════════════════════════════════════════════════════════

class BookingViewSet(ViewSet):
    """
    Управление бронированиями.
    Клиент создаёт, мастер подтверждает/завершает, любой участник может отменить.
    """

    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        """Создание — только Client, подтверждение/завершение — только Master."""
        if self.action == 'create':
            return [IsClient()]
        if self.action in ['confirm', 'complete']:
            return [IsMaster()]
        return [IsAuthenticated()]

    @extend_schema(
        summary="Список бронирований",
        description=(
            "Возвращает бронирования в зависимости от роли пользователя:\n"
            "- **Client** — только свои бронирования\n"
            "- **Master** — бронирования к нему\n"
            "- **Admin** — все бронирования своих салонов\n\n"
            "Поддерживаются фильтры по статусу, дате и мастеру."
        ),
        parameters=[
            OpenApiParameter('status', OpenApiTypes.STR, OpenApiParameter.QUERY,
                             description='pending | confirmed | completed | cancelled',
                             required=False,
                             enum=['pending', 'confirmed', 'completed', 'cancelled']),
            OpenApiParameter('date_from', OpenApiTypes.DATE, OpenApiParameter.QUERY,
                             description='Дата от (YYYY-MM-DD)', required=False),
            OpenApiParameter('date_to', OpenApiTypes.DATE, OpenApiParameter.QUERY,
                             description='Дата до (YYYY-MM-DD)', required=False),
            OpenApiParameter('master_id', OpenApiTypes.INT, OpenApiParameter.QUERY,
                             description='Фильтр по мастеру (только для Admin)', required=False),
        ],
        responses={200: BookingSerializer(many=True)},
        tags=['Бронирования'],
    )
    def list(self, request):
        """Возвращает бронирования текущего пользователя согласно его роли."""
        user = request.user

        # Формируем queryset в зависимости от роли
        if user.is_client:
            queryset = Booking.objects.filter(client=user)
        elif user.is_master:
            queryset = Booking.objects.filter(master=user)
        elif user.is_admin:
            salons = Salon.objects.filter(owner=user)
            queryset = Booking.objects.filter(salon__in=salons)
        else:
            queryset = Booking.objects.none()

        # Фильтр по статусу бронирования
        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        # Фильтр по начальной дате периода
        date_from = request.query_params.get('date_from')
        if date_from:
            queryset = queryset.filter(appointment_date__gte=date_from)

        # Фильтр по конечной дате периода
        date_to = request.query_params.get('date_to')
        if date_to:
            queryset = queryset.filter(appointment_date__lte=date_to)

        # Фильтр по конкретному мастеру (только для Admin)
        master_id = request.query_params.get('master_id')
        if master_id and user.is_admin:
            queryset = queryset.filter(master_id=master_id)

        queryset = queryset.select_related(
            'salon', 'client', 'master'
        ).prefetch_related('services').order_by('-appointment_date', '-appointment_time')

        serializer = BookingSerializer(queryset, many=True)
        return Response({
            'status': 'success',
            'count': queryset.count(),
            'data': serializer.data,
        })

    @extend_schema(
        summary="Детали бронирования",
        description="Возвращает данные бронирования. Доступно только участникам: клиенту, мастеру или Admin.",
        responses={
            200: BookingSerializer,
            403: OpenApiResponse(description="Нет доступа к этому бронированию"),
            404: OpenApiResponse(description="Бронирование не найдено"),
        },
        tags=['Бронирования'],
    )
    def retrieve(self, request, pk=None):
        """Возвращает детали бронирования. Проверяет, является ли пользователь участником."""
        booking = get_object_or_404(Booking, pk=pk)
        user = request.user
        # Доступ только участникам бронирования или администратору
        if not (user.is_admin or booking.client == user or booking.master == user):
            return Response(
                {'status': 'error', 'message': 'Нет доступа к этому бронированию'},
                status=HTTP_403_FORBIDDEN,
            )
        return Response({'status': 'success', 'data': BookingSerializer(booking).data})

    @extend_schema(
        summary="Создать бронирование [Client]",
        description=(
            "Клиент создаёт бронирование к выбранному мастеру. "
            "Салон определяется автоматически по салону мастера. "
            "Система проверяет рабочее расписание мастера и отсутствие конфликтов. "
            "После создания клиент и мастер получают email-уведомления."
        ),
        request=BookingCreateSerializer,
        responses={
            201: BookingSerializer,
            400: OpenApiResponse(description="Мастер недоступен или время занято"),
        },
        tags=['Бронирования'],
    )
    def create(self, request):
        """Создаёт бронирование с проверкой расписания и конфликтов. Отправляет уведомления."""
        serializer = BookingCreateSerializer(
            data=request.data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)

        master_id = request.data.get('master')
        appointment_date = request.data.get('appointment_date')
        appointment_time = request.data.get('appointment_time')

        # Проверяем, работает ли мастер в указанное время по расписанию
        if not self._is_master_available(master_id, appointment_date, appointment_time):
            return Response(
                {'status': 'error', 'message': 'Мастер не работает в это время'},
                status=HTTP_400_BAD_REQUEST,
            )

        # Проверяем, нет ли пересекающегося активного бронирования
        if self._has_conflicting_booking(master_id, appointment_date, appointment_time):
            return Response(
                {'status': 'error', 'message': 'Это время уже занято'},
                status=HTTP_400_BAD_REQUEST,
            )

        booking = serializer.save()

        # Уведомляем клиента и мастера по email
        NotificationService.send_booking_created_to_client(booking)
        NotificationService.send_booking_created_to_master(booking)

        logger.info("Создано бронирование: code=%s", booking.booking_code)
        return Response({
            'status': 'success',
            'message': 'Бронирование успешно создано',
            'data': BookingSerializer(booking).data,
        }, status=HTTP_201_CREATED)

    def _is_master_available(self, master_id, appointment_date, appointment_time):
        """Проверяет, входит ли указанное время в рабочий график мастера на этот день."""
        try:
            date_obj = datetime.strptime(appointment_date, '%Y-%m-%d').date()
            time_str = ':'.join(appointment_time.split(':')[:2])
            time_obj = datetime.strptime(time_str, '%H:%M').time()
            weekday = date_obj.weekday()
            schedule = WorkSchedule.objects.filter(
                master_id=master_id, weekday=weekday, is_working=True
            ).first()
            if not schedule:
                return False
            return schedule.start_time <= time_obj <= schedule.end_time
        except Exception as e:
            logger.error("Ошибка проверки расписания мастера: %s", e)
            return False

    def _has_conflicting_booking(self, master_id, appointment_date, appointment_time):
        """Проверяет, нет ли у мастера активного бронирования в это же время."""
        return Booking.objects.filter(
            master_id=master_id,
            appointment_date=appointment_date,
            appointment_time=appointment_time,
            status__in=['pending', 'confirmed'],
        ).exists()

    @extend_schema(
        summary="Удалить бронирование",
        responses={204: OpenApiResponse(description="Бронирование удалено")},
        tags=['Бронирования'],
    )
    def destroy(self, request, pk=None):
        """Полностью удаляет запись бронирования из базы данных."""
        booking = get_object_or_404(Booking, pk=pk)
        booking.delete()
        return Response(
            {'status': 'success', 'message': 'Бронирование удалено'},
            status=HTTP_204_NO_CONTENT,
        )

    # ── Переходы статусов ─────────────────────────────────────────────────────

    @extend_schema(
        summary="Подтвердить бронирование [Master]",
        description="Мастер переводит бронирование из статуса `pending` в `confirmed`. "
                    "Клиент получает email-уведомление.",
        responses={
            200: BookingSerializer,
            403: OpenApiResponse(description="Можно подтверждать только свои записи"),
            400: OpenApiResponse(description="Бронирование не в статусе pending"),
        },
        tags=['Бронирования — статусы'],
    )
    @action(detail=True, methods=['post'], url_path='confirm')
    def confirm(self, request, pk=None):
        """Переводит бронирование в confirmed. Только мастер этой записи. Email клиенту."""
        booking = get_object_or_404(Booking, pk=pk)
        if booking.master != request.user:
            return Response(
                {'status': 'error', 'message': 'Можно подтверждать только свои записи'},
                status=HTTP_403_FORBIDDEN,
            )
        serializer = BookingConfirmSerializer(instance=booking, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        # Отправляем клиенту уведомление о подтверждении
        NotificationService.send_booking_confirmed(booking)
        logger.info("Бронирование подтверждено: %s", booking.booking_code)
        return Response({
            'status': 'success',
            'message': 'Бронирование подтверждено',
            'data': BookingSerializer(booking).data,
        })

    @extend_schema(
        summary="Завершить бронирование [Master]",
        description="Мастер переводит бронирование из `confirmed` в `completed`. "
                    "Автоматически рассчитывается разделение оплаты (70/30). "
                    "Клиент получает email-уведомление.",
        responses={
            200: BookingSerializer,
            403: OpenApiResponse(description="Можно завершать только свои записи"),
        },
        tags=['Бронирования — статусы'],
    )
    @action(detail=True, methods=['post'], url_path='complete')
    def complete(self, request, pk=None):
        """Переводит бронирование в completed, обрабатывает оплату, уведомляет клиента."""
        booking = get_object_or_404(Booking, pk=pk)
        if booking.master != request.user:
            return Response(
                {'status': 'error', 'message': 'Можно завершать только свои записи'},
                status=HTTP_403_FORBIDDEN,
            )
        serializer = BookingCompleteSerializer(instance=booking, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        # Уведомляем клиента и обрабатываем платёж
        NotificationService.send_booking_completed(booking)
        payment_result = PaymentService.process_payment(booking)
        logger.info("Бронирование завершено: %s", booking.booking_code)
        return Response({
            'status': 'success',
            'message': 'Бронирование завершено',
            'data': BookingSerializer(booking).data,
            'payment': payment_result,
        })

    @extend_schema(
        summary="Отменить бронирование",
        description=(
            "Отменяет бронирование. Доступно клиенту, мастеру и Admin. "
            "Применяется политика возврата:\n"
            "- Отмена за 24+ ч до записи — полный возврат\n"
            "- Отмена менее чем за 24 ч — без возврата"
        ),
        responses={
            200: BookingSerializer,
            403: OpenApiResponse(description="Нет прав для отмены этого бронирования"),
            400: OpenApiResponse(description="Бронирование невозможно отменить"),
        },
        tags=['Бронирования — статусы'],
    )
    @action(detail=True, methods=['post'], url_path='cancel')
    def cancel(self, request, pk=None):
        """Отменяет бронирование с расчётом суммы возврата по политике отмены."""
        booking = get_object_or_404(Booking, pk=pk)

        # Определяем, кто выполняет отмену, для логики возврата
        if booking.client == request.user:
            cancelled_by = 'client'
        elif booking.master == request.user:
            cancelled_by = 'master'
        elif request.user.is_admin:
            cancelled_by = 'admin'
        else:
            return Response(
                {'status': 'error', 'message': 'Нет прав для отмены этого бронирования'},
                status=HTTP_403_FORBIDDEN,
            )

        result = CancellationPolicy.process_cancellation(booking, cancelled_by)
        if not result['success']:
            return Response(
                {'status': 'error', 'message': result['message']},
                status=HTTP_400_BAD_REQUEST,
            )

        # Уведомляем участников об отмене
        NotificationService.send_booking_cancelled(booking, cancelled_by)
        logger.info("Бронирование отменено: %s, инициатор: %s", booking.booking_code, cancelled_by)
        return Response({
            'status': 'success',
            'message': 'Бронирование отменено',
            'data': BookingSerializer(booking).data,
            'cancellation': result,
        })

    @extend_schema(
        summary="Политика отмены бронирования",
        description="Проверяет, можно ли отменить бронирование, и рассчитывает сумму возврата.",
        responses={200: OpenApiResponse(description="Информация о возможности отмены и возврате")},
        tags=['Бронирования — статусы'],
    )
    @action(detail=True, methods=['get'], url_path='cancellation-policy')
    def get_cancellation_policy(self, request, pk=None):
        """Возвращает информацию о возможности отмены и ожидаемой сумме возврата."""
        booking = get_object_or_404(Booking, pk=pk)
        can_cancel, reason = CancellationPolicy.can_cancel(booking)
        refund_info = CancellationPolicy.get_refund_amount(booking)
        return Response({
            'status': 'success',
            'booking_code': booking.booking_code,
            'can_cancel': can_cancel,
            'reason': reason,
            'refund_policy': refund_info,
        })

    # ── Массовые операции ─────────────────────────────────────────────────────

    @extend_schema(
        summary="Массово подтвердить бронирования",
        request=BookingBulkSerializer,
        responses={200: OpenApiResponse(description="Количество обновлённых записей")},
        tags=['Бронирования — массово'],
    )
    @action(detail=False, methods=['post'], url_path='bulk-confirm')
    def bulk_confirm(self, request):
        """Массово переводит бронирования из pending в confirmed по списку ID."""
        serializer = BookingBulkSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ids = serializer.validated_data['booking_ids']
        updated = Booking.objects.filter(id__in=ids, status='pending').update(status='confirmed')
        return Response({
            'status': 'success',
            'message': f'Подтверждено {updated} бронирований',
            'updated_count': updated,
        })

    @extend_schema(
        summary="Массово завершить бронирования",
        request=BookingBulkSerializer,
        responses={200: OpenApiResponse(description="Количество обновлённых записей")},
        tags=['Бронирования — массово'],
    )
    @action(detail=False, methods=['post'], url_path='bulk-complete')
    def bulk_complete(self, request):
        """Массово переводит бронирования из confirmed в completed по списку ID."""
        serializer = BookingBulkSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ids = serializer.validated_data['booking_ids']
        updated = Booking.objects.filter(id__in=ids, status='confirmed').update(status='completed')
        return Response({
            'status': 'success',
            'message': f'Завершено {updated} бронирований',
            'updated_count': updated,
        })

    @extend_schema(
        summary="Массово отменить бронирования",
        request=BookingBulkSerializer,
        responses={200: OpenApiResponse(description="Количество обновлённых записей")},
        tags=['Бронирования — массово'],
    )
    @action(detail=False, methods=['post'], url_path='bulk-cancel')
    def bulk_cancel(self, request):
        """Массово отменяет бронирования со статусом pending или confirmed по списку ID."""
        serializer = BookingBulkSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ids = serializer.validated_data['booking_ids']
        updated = Booking.objects.filter(
            id__in=ids, status__in=['pending', 'confirmed']
        ).update(status='cancelled')
        return Response({
            'status': 'success',
            'message': f'Отменено {updated} бронирований',
            'updated_count': updated,
        })

