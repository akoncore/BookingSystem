from logging import getLogger

from django.shortcuts import get_object_or_404

from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import  AllowAny
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_204_NO_CONTENT,
)

from drf_spectacular.utils import (
    extend_schema,
    OpenApiParameter,
    OpenApiResponse,
)
from drf_spectacular.types import OpenApiTypes

from models import Salon, MasterJobRequest
from main.api.salon.serializers import (
    SalonSerializer,
    SalonListSerializer,
    MasterIngoSerializer,
    MasterJobRequestSerializer,
    ServiceSerializer,
)
from main.permissions import (
    IsAdmin,
)

logger = getLogger(__name__)



# ══════════════════════════════════════════════════════════════════════════════
#  SalonViewSet  —  CRUD салонов + вложенные ресурсы
# ══════════════════════════════════════════════════════════════════════════════

class SalonViewSet(ViewSet):
    """
    CRUD для салонов и вложенные ресурсы (мастера, услуги, заявки).
    Создание, изменение, удаление — только Admin.
    Просмотр списка и деталей — публичный доступ.
    """

    def get_permissions(self):
        """Определяет права доступа: изменение — Admin, просмотр — публично."""
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'job_requests']:
            return [IsAdmin()]
        return [AllowAny()]

    @extend_schema(
        summary="Список активных салонов",
        description="Возвращает все активные салоны. Доступно без авторизации. "
                    "Поддерживаются фильтры по названию, городу и наличию мастеров.",
        parameters=[
            OpenApiParameter('name', OpenApiTypes.STR, OpenApiParameter.QUERY,
                             description='Фильтр по названию (частичное совпадение)', required=False),
            OpenApiParameter('city', OpenApiTypes.STR, OpenApiParameter.QUERY,
                             description='Поиск по городу (ищет в поле address)', required=False),
            OpenApiParameter('has_masters', OpenApiTypes.BOOL, OpenApiParameter.QUERY,
                             description='Показать только салоны с подтверждёнными мастерами',
                             required=False),
        ],
        responses={200: SalonListSerializer(many=True)},
        tags=['Салоны'],
    )
    def list(self, request):
        """Возвращает список активных салонов с фильтрацией по названию, городу и мастерам."""
        queryset = Salon.objects.filter(is_active=True)

        # Фильтр по названию салона
        name = request.query_params.get('name')
        if name:
            queryset = queryset.filter(name__icontains=name)

        # Фильтр по городу (ищем в поле адреса)
        city = request.query_params.get('city')
        if city:
            queryset = queryset.filter(address__icontains=city)

        # Фильтр: только салоны с хотя бы одним подтверждённым мастером
        has_masters = request.query_params.get('has_masters')
        if has_masters == 'true':
            queryset = queryset.filter(masters__is_approved=True).distinct()

        serializer = SalonListSerializer(queryset, many=True)
        return Response({
            'status': 'success',
            'count': queryset.count(),
            'data': serializer.data,
        })

    @extend_schema(
        summary="Профиль салона",
        description="Возвращает полную информацию о салоне включая мастеров и услуги.",
        responses={
            200: SalonSerializer,
            404: OpenApiResponse(description="Салон не найден или неактивен"),
        },
        tags=['Салоны'],
    )
    def retrieve(self, request, pk=None):
        """Возвращает полный профиль салона с мастерами и услугами."""
        salon = get_object_or_404(Salon, pk=pk, is_active=True)
        serializer = SalonSerializer(salon)
        return Response({'status': 'success', 'data': serializer.data})

    @extend_schema(
        summary="Создать салон [Admin]",
        description="Создаёт новый салон. Владелец устанавливается автоматически — текущий Admin.",
        request=SalonSerializer,
        responses={
            201: SalonSerializer,
            400: OpenApiResponse(description="Ошибка валидации данных"),
        },
        tags=['Салоны'],
    )
    def create(self, request):
        """Создаёт новый салон. Поле owner заполняется автоматически из request.user."""
        data = request.data.copy()
        data['owner'] = request.user.id
        serializer = SalonSerializer(data=data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        salon = serializer.save(owner=request.user)
        logger.info("Создан салон: id=%s, admin=%s", salon.id, request.user.email)
        return Response({
            'status': 'success',
            'message': 'Салон успешно создан',
            'data': SalonSerializer(salon).data,
        }, status=HTTP_201_CREATED)

    @extend_schema(
        summary="Обновить салон [Admin]",
        description="Полностью обновляет данные салона. Доступно только владельцу-Admin.",
        request=SalonSerializer,
        responses={200: SalonSerializer},
        tags=['Салоны'],
    )
    def update(self, request, pk=None):
        """Полностью обновляет все поля салона (PUT). Только для владельца-Admin."""
        salon = get_object_or_404(Salon, pk=pk, owner=request.user)
        serializer = SalonSerializer(salon, data=request.data, partial=False,
                                     context={'request': request})
        serializer.is_valid(raise_exception=True)
        salon = serializer.save()
        return Response({'status': 'success', 'data': SalonSerializer(salon).data})

    @extend_schema(
        summary="Частично обновить салон [Admin]",
        description="Обновляет отдельные поля салона (PATCH). Только для владельца-Admin.",
        request=SalonSerializer,
        responses={200: SalonSerializer},
        tags=['Салоны'],
    )
    def partial_update(self, request, pk=None):
        """Частично обновляет поля салона (PATCH). Только для владельца-Admin."""
        salon = get_object_or_404(Salon, pk=pk, owner=request.user)
        serializer = SalonSerializer(salon, data=request.data, partial=True,
                                     context={'request': request})
        serializer.is_valid(raise_exception=True)
        salon = serializer.save()
        return Response({'status': 'success', 'data': SalonSerializer(salon).data})

    @extend_schema(
        summary="Деактивировать салон [Admin]",
        description="Выполняет мягкое удаление: устанавливает is_active=False. "
                    "Данные сохраняются в базе. Только для владельца-Admin.",
        responses={204: OpenApiResponse(description="Салон успешно деактивирован")},
        tags=['Салоны'],
    )
    def destroy(self, request, pk=None):
        """Деактивирует салон (soft delete). Данные не удаляются из базы."""
        salon = get_object_or_404(Salon, pk=pk, owner=request.user)
        salon.is_active = False
        salon.save()
        return Response(
            {'status': 'success', 'message': 'Салон деактивирован'},
            status=HTTP_204_NO_CONTENT,
        )

    @extend_schema(
        summary="Мастера салона",
        description="Возвращает список подтверждённых мастеров конкретного салона.",
        responses={200: MasterIngoSerializer(many=True)},
        tags=['Салоны'],
    )
    @action(detail=True, methods=['get'], url_path='masters')
    def masters(self, request, pk=None):
        """Возвращает подтверждённых мастеров указанного салона."""
        salon = get_object_or_404(Salon, pk=pk, is_active=True)
        masters = salon.masters.filter(is_approved=True).select_related('user')
        serializer = MasterIngoSerializer(masters, many=True)
        return Response({
            'status': 'success',
            'salon': {'id': salon.id, 'name': salon.name},
            'master_count': masters.count(),
            'data': serializer.data,
        })

    @extend_schema(
        summary="Услуги салона",
        description="Возвращает список активных услуг салона с фильтрацией по цене и названию.",
        parameters=[
            OpenApiParameter('name', OpenApiTypes.STR, OpenApiParameter.QUERY,
                             description='Поиск по названию услуги', required=False),
            OpenApiParameter('min_price', OpenApiTypes.FLOAT, OpenApiParameter.QUERY,
                             description='Минимальная цена', required=False),
            OpenApiParameter('max_price', OpenApiTypes.FLOAT, OpenApiParameter.QUERY,
                             description='Максимальная цена', required=False),
        ],
        responses={200: ServiceSerializer(many=True)},
        tags=['Салоны'],
    )
    @action(detail=True, methods=['get'], url_path='services')
    def services(self, request, pk=None):
        """Возвращает активные услуги салона с возможной фильтрацией по цене и названию."""
        salon = get_object_or_404(Salon, pk=pk, is_active=True)
        services_qs = salon.services.filter(is_active=True)

        # Фильтр по названию услуги
        name = request.query_params.get('name')
        if name:
            services_qs = services_qs.filter(name__icontains=name)

        # Фильтр по минимальной цене
        min_price = request.query_params.get('min_price')
        if min_price:
            services_qs = services_qs.filter(price__gte=float(min_price))

        # Фильтр по максимальной цене
        max_price = request.query_params.get('max_price')
        if max_price:
            services_qs = services_qs.filter(price__lte=float(max_price))

        serializer = ServiceSerializer(services_qs, many=True)
        return Response({
            'status': 'success',
            'salon': {'id': salon.id, 'name': salon.name},
            'count': services_qs.count(),
            'data': serializer.data,
        })

    @extend_schema(
        summary="Заявки мастеров в салон [Admin]",
        description="Возвращает все заявки мастеров для данного салона. "
                    "Доступно только владельцу-Admin. Фильтр по статусу.",
        parameters=[
            OpenApiParameter('status', OpenApiTypes.STR, OpenApiParameter.QUERY,
                             description='pending | approved | rejected',
                             required=False,
                             enum=['pending', 'approved', 'rejected']),
        ],
        responses={200: MasterJobRequestSerializer(many=True)},
        tags=['Admin — заявки'],
    )
    @action(detail=True, methods=['get'], url_path='job-requests')
    def job_requests(self, request, pk=None):
        """Возвращает заявки мастеров для конкретного салона с фильтрацией по статусу."""
        # Только владелец салона может видеть его заявки
        salon = get_object_or_404(Salon, pk=pk, owner=request.user)
        requests_qs = MasterJobRequest.objects.filter(
            salon=salon
        ).select_related('master', 'reviewed_by')

        # Опциональный фильтр по статусу заявки
        status_filter = request.query_params.get('status')
        if status_filter:
            requests_qs = requests_qs.filter(status=status_filter)

        serializer = MasterJobRequestSerializer(requests_qs, many=True)
        return Response({
            'status': 'success',
            'salon': {'id': salon.id, 'name': salon.name},
            'count': requests_qs.count(),
            'data': serializer.data,
        })
