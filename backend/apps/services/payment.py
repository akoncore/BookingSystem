
from logging import getLogger
from datetime import datetime, timedelta, date as dt_date

from django.shortcuts import get_object_or_404


from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.status import (
    HTTP_400_BAD_REQUEST,
)

from drf_spectacular.utils import (
    extend_schema,
    OpenApiParameter,
    OpenApiResponse,
)
from drf_spectacular.types import OpenApiTypes

from main.models import  Booking


from apps.services.payment import PaymentService

logger = getLogger(__name__)


class PaymentViewSet(ViewSet):
    """Расчёт распределения оплаты между мастером и салоном, просмотр балансов."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Распределение оплаты по бронированию",
        description="Показывает, как делится сумма бронирования: 70% мастеру, 30% салону.",
        responses={200: OpenApiResponse(description="Разбивка оплаты по участникам")},
        tags=['Оплата'],
    )
    @action(detail=True, methods=['get'], url_path='split')
    def payment_split(self, request, pk=None):
        """Возвращает расчёт распределения оплаты по конкретному бронированию."""
        booking = get_object_or_404(Booking, pk=pk)
        data = PaymentService.calculate_split(booking)
        return Response({'status': 'success', 'data': data})

    @extend_schema(
        summary="Баланс мастера",
        description="Возвращает накопленный баланс мастера по завершённым бронированиям за период.",
        parameters=[
            OpenApiParameter('master_id', OpenApiTypes.INT, OpenApiParameter.QUERY,
                             description='ID мастера (обязательно)', required=True),
            OpenApiParameter('period_days', OpenApiTypes.INT, OpenApiParameter.QUERY,
                             description='Период в днях (по умолчанию: 30)', required=False),
        ],
        responses={
            200: OpenApiResponse(description="Баланс мастера с разбивкой по бронированиям"),
            400: OpenApiResponse(description="master_id обязателен"),
        },
        tags=['Оплата'],
    )
    @action(detail=False, methods=['get'], url_path='master-balance')
    def master_balance(self, request):
        """Возвращает баланс мастера по завершённым бронированиям за указанный период."""
        master_id = request.query_params.get('master_id')
        period_days = int(request.query_params.get('period_days', 30))
        if not master_id:
            return Response(
                {'status': 'error', 'message': 'Параметр master_id обязателен'},
                status=HTTP_400_BAD_REQUEST,
            )
        data = PaymentService.get_master_balance(int(master_id), period_days)
        return Response({'status': 'success', 'data': data})

    @extend_schema(
        summary="Баланс салона",
        description="Возвращает доходы салона с разбивкой по мастерам за период.",
        parameters=[
            OpenApiParameter('salon_id', OpenApiTypes.INT, OpenApiParameter.QUERY,
                             description='ID салона (обязательно)', required=True),
            OpenApiParameter('period_days', OpenApiTypes.INT, OpenApiParameter.QUERY,
                             description='Период в днях (по умолчанию: 30)', required=False),
        ],
        responses={
            200: OpenApiResponse(description="Баланс салона с разбивкой по мастерам"),
            400: OpenApiResponse(description="salon_id обязателен"),
        },
        tags=['Оплата'],
    )
    @action(detail=False, methods=['get'], url_path='salon-balance')
    def salon_balance(self, request):
        """Возвращает доходы салона с детальной разбивкой по каждому мастеру."""
        salon_id = request.query_params.get('salon_id')
        period_days = int(request.query_params.get('period_days', 30))
        if not salon_id:
            return Response(
                {'status': 'error', 'message': 'Параметр salon_id обязателен'},
                status=HTTP_400_BAD_REQUEST,
            )
        data = PaymentService.get_salon_balance(int(salon_id), period_days)
        return Response({'status': 'success', 'data': data})