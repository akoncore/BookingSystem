"""
AnalyticsViewSet — ViewSet аналитики и статистики.

Отвечает только за HTTP-логику:
- получение параметров из запроса
- базовая валидация обязательных параметров
- вызов AnalyticsService и возврат ответа клиенту

Вся бизнес-логика расчётов — в AnalyticsService (apps/services/analytics_service.py).

Эндпоинты:
    GET /api/v2/analytics/top-masters/       — топ мастеров по бронированиям
    GET /api/v2/analytics/top-services/      — топ услуг по заказам
    GET /api/v2/analytics/revenue/           — статистика выручки за период
    GET /api/v2/analytics/salon-performance/ — KPI конкретного салона
    GET /api/v2/analytics/master-earnings/   — заработок конкретного мастера
    GET /api/v2/analytics/dashboard/         — персональный дашборд по роли
"""

from logging import getLogger

from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.status import HTTP_400_BAD_REQUEST

from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from drf_spectacular.types import OpenApiTypes

# Сервис с бизнес-логикой расчётов — импортируем из services
from apps.services.analytics import AnalyticsService

# Логгер для отладки и мониторинга ошибок
logger = getLogger(__name__)


class AnalyticsViewSet(ViewSet):
    """
    ViewSet аналитики.

    Все методы доступны только авторизованным пользователям.
    Параметры передаются через query string (?salon_id=1&period_days=30).
    """

    # Все эндпоинты требуют авторизации через JWT-токен
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Топ мастеров по количеству бронирований",
        description=(
            "Возвращает рейтинг мастеров по числу завершённых бронирований за период.\n\n"
            "Для каждого мастера рассчитывается выручка с разбивкой:\n"
            "- заработок мастера — **70%**\n"
            "- комиссия салона — **30%**"
        ),
        parameters=[
            OpenApiParameter(
                'salon_id', OpenApiTypes.INT, OpenApiParameter.QUERY,
                description='ID салона для фильтрации (необязательно)',
                required=False,
            ),
            OpenApiParameter(
                'limit', OpenApiTypes.INT, OpenApiParameter.QUERY,
                description='Количество мастеров в топе (по умолчанию: 10)',
                required=False,
            ),
            OpenApiParameter(
                'period_days', OpenApiTypes.INT, OpenApiParameter.QUERY,
                description='Глубина анализа в днях (по умолчанию: 30)',
                required=False,
            ),
        ],
        responses={200: OpenApiResponse(description="Список мастеров со статистикой")},
        tags=['Аналитика'],
    )
    @action(detail=False, methods=['get'], url_path='top-masters')
    def top_masters(self, request):
        """
        Возвращает топ мастеров по числу завершённых бронирований.

        Query params:
            salon_id    — фильтр по конкретному салону (необязательно)
            limit       — максимум мастеров в ответе (default: 10)
            period_days — период анализа в днях (default: 30)
        """
        # Читаем параметры из строки запроса
        salon_id = request.query_params.get('salon_id')
        limit = int(request.query_params.get('limit', 10))
        period_days = int(request.query_params.get('period_days', 30))

        # Делегируем расчёт сервису
        data = AnalyticsService.get_top_masters(salon_id, limit, period_days)

        return Response({'status': 'success', 'count': len(data), 'data': data})

    @extend_schema(
        summary="Топ услуг по количеству заказов",
        description=(
            "Возвращает рейтинг услуг по числу заказов среди завершённых бронирований.\n\n"
            "Учитываются только реально оказанные услуги (статус 'completed')."
        ),
        parameters=[
            OpenApiParameter(
                'salon_id', OpenApiTypes.INT, OpenApiParameter.QUERY,
                description='ID салона для фильтрации (необязательно)',
                required=False,
            ),
            OpenApiParameter(
                'limit', OpenApiTypes.INT, OpenApiParameter.QUERY,
                description='Количество услуг в топе (по умолчанию: 10)',
                required=False,
            ),
            OpenApiParameter(
                'period_days', OpenApiTypes.INT, OpenApiParameter.QUERY,
                description='Глубина анализа в днях (по умолчанию: 30)',
                required=False,
            ),
        ],
        responses={200: OpenApiResponse(description="Список услуг со статистикой заказов")},
        tags=['Аналитика'],
    )
    @action(detail=False, methods=['get'], url_path='top-services')
    def top_services(self, request):
        """
        Возвращает топ услуг по числу заказов за период.

        Query params:
            salon_id    — фильтр по конкретному салону (необязательно)
            limit       — максимум услуг в ответе (default: 10)
            period_days — период анализа в днях (default: 30)
        """
        salon_id = request.query_params.get('salon_id')
        limit = int(request.query_params.get('limit', 10))
        period_days = int(request.query_params.get('period_days', 30))

        data = AnalyticsService.get_top_services(salon_id, limit, period_days)

        return Response({'status': 'success', 'count': len(data), 'data': data})

    @extend_schema(
        summary="Статистика выручки за период",
        description=(
            "Возвращает общую выручку и дневную разбивку за указанный период.\n\n"
            "Распределение суммы:\n"
            "- заработок мастеров — **70%**\n"
            "- доход салона — **30%**"
        ),
        parameters=[
            OpenApiParameter(
                'salon_id', OpenApiTypes.INT, OpenApiParameter.QUERY,
                description='ID салона для фильтрации (необязательно)',
                required=False,
            ),
            OpenApiParameter(
                'period_days', OpenApiTypes.INT, OpenApiParameter.QUERY,
                description='Глубина анализа в днях (по умолчанию: 30)',
                required=False,
            ),
        ],
        responses={
            200: OpenApiResponse(
                description="Сводка и дневная разбивка выручки с долями мастера и салона"
            )
        },
        tags=['Аналитика'],
    )
    @action(detail=False, methods=['get'], url_path='revenue')
    def revenue_statistics(self, request):
        """
        Возвращает общую выручку и дневную динамику за период.

        Query params:
            salon_id    — фильтр по конкретному салону (необязательно)
            period_days — период анализа в днях (default: 30)
        """
        salon_id = request.query_params.get('salon_id')
        period_days = int(request.query_params.get('period_days', 30))

        data = AnalyticsService.get_revenue_statistics(salon_id, period_days)

        return Response({'status': 'success', 'data': data})

    @extend_schema(
        summary="KPI показатели конкретного салона",
        description=(
            "Возвращает ключевые показатели работы салона за период:\n"
            "- статистика бронирований (всего, завершено, отменено)\n"
            "- финансовые показатели (выручка, средний чек, доли)\n"
            "- процент конверсии и процент отмен\n\n"
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
                description='Глубина анализа в днях (по умолчанию: 30)',
                required=False,
            ),
        ],
        responses={
            200: OpenApiResponse(description="KPI и показатели производительности салона"),
            400: OpenApiResponse(description="Параметр salon_id не передан"),
        },
        tags=['Аналитика'],
    )
    @action(detail=False, methods=['get'], url_path='salon-performance')
    def salon_performance(self, request):
        """
        Возвращает KPI-показатели работы конкретного салона.

        Query params:
            salon_id    — ID салона (обязательно)
            period_days — период анализа в днях (default: 30)
        """
        salon_id = request.query_params.get('salon_id')

        # salon_id обязателен — без него нельзя определить, какой салон анализировать
        if not salon_id:
            return Response(
                {'status': 'error', 'message': 'Параметр salon_id обязателен'},
                status=HTTP_400_BAD_REQUEST,
            )

        period_days = int(request.query_params.get('period_days', 30))
        data = AnalyticsService.get_salon_performance(int(salon_id), period_days)

        return Response({'status': 'success', 'data': data})

    @extend_schema(
        summary="Заработок конкретного мастера (для Admin)",
        description=(
            "Возвращает детальную статистику заработка мастера за период.\n\n"
            "Предназначен для Admin-аналитики — просмотр любого мастера.\n"
            "Для личного кабинета мастера используйте: `/api/v2/master/my-earnings/`\n\n"
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
                description='Глубина анализа в днях (по умолчанию: 30)',
                required=False,
            ),
        ],
        responses={
            200: OpenApiResponse(description="Профиль мастера, сводка и дневная разбивка заработка"),
            400: OpenApiResponse(description="Параметр master_id не передан"),
        },
        tags=['Аналитика'],
    )
    @action(detail=False, methods=['get'], url_path='master-earnings')
    def master_earnings(self, request):
        """
        Возвращает заработок конкретного мастера (Admin аналитика).

        Query params:
            master_id   — ID мастера (обязательно)
            period_days — период анализа в днях (default: 30)
        """
        master_id = request.query_params.get('master_id')

        # master_id обязателен — без него непонятно, чью статистику возвращать
        if not master_id:
            return Response(
                {'status': 'error', 'message': 'Параметр master_id обязателен'},
                status=HTTP_400_BAD_REQUEST,
            )

        period_days = int(request.query_params.get('period_days', 30))
        data = AnalyticsService.get_master_earnings(int(master_id), period_days)

        return Response({'status': 'success', 'data': data})

    @extend_schema(
        summary="Персональный дашборд (по роли пользователя)",
        description=(
            "Возвращает дашборд, адаптированный под роль текущего пользователя:\n\n"
            "- **Admin** — KPI своих салонов: выручка за месяц, записи сегодня\n"
            "- **Master** — заработок за текущий месяц, записи сегодня\n"
            "- **Client** — история бронирований и предстоящие записи"
        ),
        responses={
            200: OpenApiResponse(description="Данные дашборда, специфичные для роли пользователя")
        },
        tags=['Аналитика'],
    )
    @action(detail=False, methods=['get'], url_path='dashboard')
    def dashboard(self, request):
        """
        Возвращает персональный дашборд текущего пользователя.

        Данные различаются в зависимости от роли (admin / master / client).
        Авторизация через JWT-токен — пользователь определяется автоматически.
        """
        # Передаём request.user в сервис — он сам определит роль и вернёт нужные данные
        data = AnalyticsService.get_dashboard_summary(request.user)

        return Response({
            'status': 'success',
            # Краткий профиль текущего пользователя для удобства фронтенда
            'user': {
                'id': request.user.id,
                'full_name': request.user.full_name,
                'role': request.user.role,
            },
            'data': data,
        })