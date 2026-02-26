"""
PaymentViewSet — ViewSet обработки платежей и балансов.

Отвечает только за HTTP-логику:
- получение параметров из запроса
- базовая валидация обязательных параметров
- вызов PaymentService и возврат ответа клиенту

Вся бизнес-логика расчётов — в PaymentService (apps/services/payment_service.py).

Эндпоинты:
    GET /api/v2/payment/{id}/split/    — распределение оплаты по бронированию (70/30)
    GET /api/v2/payment/master-balance/ — накопленный баланс мастера
    GET /api/v2/payment/salon-balance/  — доходы салона с разбивкой по мастерам
"""

from logging import getLogger

from django.shortcuts import get_object_or_404

from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.status import HTTP_400_BAD_REQUEST

from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from drf_spectacular.types import OpenApiTypes

# Модель бронирования для получения объекта по pk
from apps.main.models import Booking

# Сервис с бизнес-логикой расчётов платежей
from apps.services.payment import PaymentService

# Логгер для отладки и мониторинга ошибок
logger = getLogger(__name__)


class PaymentViewSet(ViewSet):
    """
    ViewSet платёжной системы.

    Все методы доступны только авторизованным пользователям.
    Параметры передаются через query string (?master_id=5&period_days=30).
    """

    # Все эндпоинты требуют авторизации через JWT-токен
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Распределение оплаты по бронированию (70/30)",
        description=(
            "Возвращает детальный расчёт распределения суммы бронирования:\n\n"
            "- мастер получает **70%** от общей суммы\n"
            "- салон получает **30%** как комиссию за площадку\n\n"
            "Передайте ID бронирования в URL: `/api/v2/payment/{id}/split/`"
        ),
        responses={
            200: OpenApiResponse(description="Суммы для мастера и салона с процентами"),
            404: OpenApiResponse(description="Бронирование с указанным ID не найдено"),
        },
        tags=['Оплата'],
    )
    @action(detail=True, methods=['get'], url_path='split')
    def payment_split(self, request, pk=None):
        """
        Возвращает распределение оплаты между мастером и салоном.

        URL param:
            pk — ID бронирования (обязательно, передаётся в URL)
        """
        # Получаем объект бронирования или возвращаем 404 если не найден
        booking = get_object_or_404(Booking, pk=pk)

        # Делегируем расчёт распределения сервису
        data = PaymentService.calculate_split(booking)

        return Response({'status': 'success', 'data': data})

    @extend_schema(
        summary="Накопленный баланс мастера",
        description=(
            "Возвращает накопленный баланс мастера по завершённым бронированиям за период.\n\n"
            "Включает:\n"
            "- сводку (общая выручка, заработок мастера 70%)\n"
            "- историю последних 20 транзакций\n\n"
            "⚠️ Параметр `master_id` обязателен."
        ),
        parameters=[
            OpenApiParameter(
                'master_id', OpenApiTypes.INT, OpenApiParameter.QUERY,
                description='ID пользователя с ролью master (обязательно)',
                required=True,
            ),
            OpenApiParameter(
                'period_days', OpenApiTypes.INT, OpenApiParameter.QUERY,
                description='Период анализа в днях (по умолчанию: 30)',
                required=False,
            ),
        ],
        responses={
            200: OpenApiResponse(description="Баланс мастера и история транзакций"),
            400: OpenApiResponse(description="Параметр master_id не передан"),
        },
        tags=['Оплата'],
    )
    @action(detail=False, methods=['get'], url_path='master-balance')
    def master_balance(self, request):
        """
        Возвращает баланс и историю транзакций мастера за период.

        Query params:
            master_id   — ID мастера (обязательно)
            period_days — период анализа в днях (default: 30)
        """
        master_id = request.query_params.get('master_id')

        # master_id обязателен — без него неизвестно, чей баланс запрашивается
        if not master_id:
            return Response(
                {'status': 'error', 'message': 'Параметр master_id обязателен'},
                status=HTTP_400_BAD_REQUEST,
            )

        period_days = int(request.query_params.get('period_days', 30))
        data = PaymentService.get_master_balance(int(master_id), period_days)

        return Response({'status': 'success', 'data': data})

    @extend_schema(
        summary="Доходы салона с разбивкой по мастерам",
        description=(
            "Возвращает доходы салона с детальной разбивкой по каждому мастеру.\n\n"
            "Включает:\n"
            "- общую сводку (выручка, комиссия салона 30%)\n"
            "- разбивку по мастерам (выручка и доля каждого)\n\n"
            "⚠️ Параметр `salon_id` обязателен."
        ),
        parameters=[
            OpenApiParameter(
                'salon_id', OpenApiTypes.INT, OpenApiParameter.QUERY,
                description='ID салона (обязательно)',
                required=True,
            ),
            OpenApiParameter(
                'period_days', OpenApiTypes.INT, OpenApiParameter.QUERY,
                description='Период анализа в днях (по умолчанию: 30)',
                required=False,
            ),
        ],
        responses={
            200: OpenApiResponse(description="Доходы салона и разбивка по мастерам"),
            400: OpenApiResponse(description="Параметр salon_id не передан"),
        },
        tags=['Оплата'],
    )
    @action(detail=False, methods=['get'], url_path='salon-balance')
    def salon_balance(self, request):
        """
        Возвращает доходы салона с разбивкой по мастерам за период.

        Query params:
            salon_id    — ID салона (обязательно)
            period_days — период анализа в днях (default: 30)
        """
        salon_id = request.query_params.get('salon_id')

        # salon_id обязателен — без него неизвестно, какой салон анализировать
        if not salon_id:
            return Response(
                {'status': 'error', 'message': 'Параметр salon_id обязателен'},
                status=HTTP_400_BAD_REQUEST,
            )

        period_days = int(request.query_params.get('period_days', 30))
        data = PaymentService.get_salon_balance(int(salon_id), period_days)

        return Response({'status': 'success', 'data': data})