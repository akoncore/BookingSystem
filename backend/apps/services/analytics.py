
from logging import getLogger
from datetime import datetime, timedelta, date as dt_date

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

from apps.services.analytics import AnalyticsService


logger = getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════════════
#  AnalyticsViewSet  —  аналитика и отчёты
# ══════════════════════════════════════════════════════════════════════════════

class AnalyticsViewSet(ViewSet):
    """Аналитика по салонам, мастерам и услугам. Доступно для авторизованных пользователей."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Топ мастеров по количеству записей",
        description="Возвращает рейтинг мастеров по числу завершённых бронирований за период.",
        parameters=[
            OpenApiParameter('salon_id', OpenApiTypes.INT, OpenApiParameter.QUERY,
                             description='Фильтр по салону', required=False),
            OpenApiParameter('limit', OpenApiTypes.INT, OpenApiParameter.QUERY,
                             description='Количество мастеров в топе (по умолчанию: 10)',
                             required=False),
            OpenApiParameter('period_days', OpenApiTypes.INT, OpenApiParameter.QUERY,
                             description='Период в днях (по умолчанию: 30)', required=False),
        ],
        responses={200: OpenApiResponse(description="Рейтинг мастеров")},
        tags=['Аналитика'],
    )
    @action(detail=False, methods=['get'], url_path='top-masters')
    def top_masters(self, request):
        """Возвращает топ мастеров по числу завершённых бронирований за указанный период."""
        salon_id = request.query_params.get('salon_id')
        limit = int(request.query_params.get('limit', 10))
        period_days = int(request.query_params.get('period_days', 30))
        data = AnalyticsService.get_top_masters(salon_id, limit, period_days)
        return Response({'status': 'success', 'data': data})

    @extend_schema(
        summary="Топ услуг по частоте заказов",
        description="Возвращает рейтинг услуг по количеству заказов за период.",
        parameters=[
            OpenApiParameter('salon_id', OpenApiTypes.INT, OpenApiParameter.QUERY,
                             description='Фильтр по салону', required=False),
            OpenApiParameter('limit', OpenApiTypes.INT, OpenApiParameter.QUERY,
                             description='Количество услуг в топе (по умолчанию: 10)',
                             required=False),
            OpenApiParameter('period_days', OpenApiTypes.INT, OpenApiParameter.QUERY,
                             description='Период в днях (по умолчанию: 30)', required=False),
        ],
        responses={200: OpenApiResponse(description="Рейтинг услуг")},
        tags=['Аналитика'],
    )
    @action(detail=False, methods=['get'], url_path='top-services')
    def top_services(self, request):
        """Возвращает топ услуг по числу заказов за указанный период."""
        salon_id = request.query_params.get('salon_id')
        limit = int(request.query_params.get('limit', 10))
        period_days = int(request.query_params.get('period_days', 30))
        data = AnalyticsService.get_top_services(salon_id, limit, period_days)
        return Response({'status': 'success', 'data': data})

    @extend_schema(
        summary="Статистика выручки",
        description="Возвращает общую и дневную статистику выручки по завершённым бронированиям.",
        parameters=[
            OpenApiParameter('salon_id', OpenApiTypes.INT, OpenApiParameter.QUERY,
                             description='Фильтр по салону', required=False),
            OpenApiParameter('period_days', OpenApiTypes.INT, OpenApiParameter.QUERY,
                             description='Период в днях (по умолчанию: 30)', required=False),
        ],
        responses={200: OpenApiResponse(description="Статистика выручки с разбивкой по дням")},
        tags=['Аналитика'],
    )
    @action(detail=False, methods=['get'], url_path='revenue')
    def revenue_statistics(self, request):
        """Возвращает статистику выручки с дневной разбивкой и итогами."""
        salon_id = request.query_params.get('salon_id')
        period_days = int(request.query_params.get('period_days', 30))
        data = AnalyticsService.get_revenue_statistics(salon_id, period_days)
        return Response({'status': 'success', 'data': data})

    @extend_schema(
        summary="KPI салона",
        description="Возвращает ключевые показатели салона: выручку, средний чек, процент отмен.",
        parameters=[
            OpenApiParameter('salon_id', OpenApiTypes.INT, OpenApiParameter.QUERY,
                             description='ID салона (обязательно)', required=True),
            OpenApiParameter('period_days', OpenApiTypes.INT, OpenApiParameter.QUERY,
                             description='Период в днях (по умолчанию: 30)', required=False),
        ],
        responses={
            200: OpenApiResponse(description="KPI и показатели производительности салона"),
            400: OpenApiResponse(description="salon_id обязателен"),
        },
        tags=['Аналитика'],
    )
    @action(detail=False, methods=['get'], url_path='salon-performance')
    def salon_performance(self, request):
        """Возвращает KPI салона: выручку, отмены, средний чек за период."""
        salon_id = request.query_params.get('salon_id')
        period_days = int(request.query_params.get('period_days', 30))
        if not salon_id:
            return Response(
                {'status': 'error', 'message': 'Параметр salon_id обязателен'},
                status=HTTP_400_BAD_REQUEST,
            )
        data = AnalyticsService.get_salon_performance(int(salon_id), period_days)
        return Response({'status': 'success', 'data': data})

    @extend_schema(
        summary="Статистика заработка мастера (Admin/аналитика)",
        description="Детальная статистика заработка мастера за период. "
                    "Используется для аналитики Admin, в отличие от /master/my-earnings/.",
        parameters=[
            OpenApiParameter('master_id', OpenApiTypes.INT, OpenApiParameter.QUERY,
                             description='ID мастера (обязательно)', required=True),
            OpenApiParameter('period_days', OpenApiTypes.INT, OpenApiParameter.QUERY,
                             description='Период в днях (по умолчанию: 30)', required=False),
        ],
        responses={
            200: OpenApiResponse(description="Детальная статистика заработка"),
            400: OpenApiResponse(description="master_id обязателен"),
        },
        tags=['Аналитика'],
    )
    @action(detail=False, methods=['get'], url_path='master-earnings')
    def master_earnings(self, request):
        """Возвращает детальную статистику заработка мастера. Для аналитики Admin."""
        master_id = request.query_params.get('master_id')
        period_days = int(request.query_params.get('period_days', 30))
        if not master_id:
            return Response(
                {'status': 'error', 'message': 'Параметр master_id обязателен'},
                status=HTTP_400_BAD_REQUEST,
            )
        data = AnalyticsService.get_master_earnings(int(master_id), period_days)
        return Response({'status': 'success', 'data': data})

    @extend_schema(
        summary="Дашборд текущего пользователя",
        description=(
            "Возвращает персональный дашборд согласно роли пользователя:\n"
            "- **Admin** — KPI первого салона\n"
            "- **Master** — статистика заработка\n"
            "- **Client** — история и итоги бронирований"
        ),
        responses={200: OpenApiResponse(description="Данные дашборда под роль пользователя")},
        tags=['Аналитика'],
    )
    @action(detail=False, methods=['get'], url_path='dashboard')
    def dashboard(self, request):
        """Возвращает персональный дашборд, адаптированный под роль текущего пользователя."""
        data = AnalyticsService.get_dashboard_summary(request.user)
        return Response({
            'status': 'success',
            'user_role': request.user.role,
            'data': data,
        })

