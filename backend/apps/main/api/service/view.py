
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

from apps.main.models import Service
from .serializers import (
    ServiceSerializer,
    ServiceCreateSerializer,
    ServiceUpdateSerializer,
)
from apps.main.permissions import (
    IsAdmin,
)

logger = getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════════════
#  ServiceViewSet  —  CRUD услуг с фильтрацией
# ══════════════════════════════════════════════════════════════════════════════

class ServiceViewSet(ViewSet):
    """
    CRUD для услуг салона.
    Создание, изменение, удаление — только Admin.
    Просмотр и поиск — публичный доступ.
    """

    def get_permissions(self):
        """Определяет права: изменение — Admin, просмотр — публично."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdmin()]
        return [AllowAny()]

    @extend_schema(
        summary="Список услуг",
        description="Возвращает активные услуги. Поддерживает фильтрацию по салону, "
                    "названию и ценовому диапазону. Доступно без авторизации.",
        parameters=[
            OpenApiParameter('salon_id', OpenApiTypes.INT, OpenApiParameter.QUERY,
                             description='Фильтр по ID салона', required=False),
            OpenApiParameter('name', OpenApiTypes.STR, OpenApiParameter.QUERY,
                             description='Поиск по названию услуги', required=False),
            OpenApiParameter('min_price', OpenApiTypes.FLOAT, OpenApiParameter.QUERY,
                             description='Минимальная цена', required=False),
            OpenApiParameter('max_price', OpenApiTypes.FLOAT, OpenApiParameter.QUERY,
                             description='Максимальная цена', required=False),
        ],
        responses={200: ServiceSerializer(many=True)},
        tags=['Услуги'],
    )
    def list(self, request):
        """Возвращает активные услуги с фильтрацией по салону, названию и цене."""
        queryset = Service.objects.filter(is_active=True).select_related('salon')

        # Фильтр по салону
        salon_id = request.query_params.get('salon_id')
        if salon_id:
            queryset = queryset.filter(salon_id=salon_id)

        # Поиск по названию услуги
        name = request.query_params.get('name')
        if name:
            queryset = queryset.filter(name__icontains=name)

        # Фильтр по нижней границе цены
        min_price = request.query_params.get('min_price')
        if min_price:
            queryset = queryset.filter(price__gte=float(min_price))

        # Фильтр по верхней границе цены
        max_price = request.query_params.get('max_price')
        if max_price:
            queryset = queryset.filter(price__lte=float(max_price))

        serializer = ServiceSerializer(queryset, many=True)
        return Response({
            'status': 'success',
            'count': queryset.count(),
            'data': serializer.data,
        })

    @extend_schema(
        summary="Детали услуги",
        responses={
            200: ServiceSerializer,
            404: OpenApiResponse(description="Услуга не найдена или неактивна"),
        },
        tags=['Услуги'],
    )
    def retrieve(self, request, pk=None):
        """Возвращает подробную информацию об одной услуге по ID."""
        service = get_object_or_404(Service, pk=pk, is_active=True)
        return Response({'status': 'success', 'data': ServiceSerializer(service).data})

    @extend_schema(
        summary="Создать услугу [Admin]",
        description="Создаёт новую услугу. Принимает `duration_minutes` (целое число) "
                    "вместо timedelta.",
        request=ServiceCreateSerializer,
        responses={
            201: ServiceSerializer,
            400: OpenApiResponse(description="Ошибка валидации данных"),
        },
        tags=['Услуги'],
    )
    def create(self, request):
        """Создаёт новую услугу в салоне. Принимает duration_minutes вместо timedelta."""
        serializer = ServiceCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        service = serializer.save()
        logger.info("Создана услуга: id=%s, salon=%s", service.id, service.salon_id)
        return Response({
            'status': 'success',
            'message': 'Услуга создана',
            'data': ServiceSerializer(service).data,
        }, status=HTTP_201_CREATED)

    @extend_schema(
        summary="Обновить услугу [Admin]",
        request=ServiceCreateSerializer,
        responses={200: ServiceSerializer},
        tags=['Услуги'],
    )
    def update(self, request, pk=None):
        """Полностью обновляет все поля услуги (PUT)."""
        service = get_object_or_404(Service, pk=pk)
        serializer = ServiceCreateSerializer(service, data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)
        service = serializer.save()
        return Response({'status': 'success', 'data': ServiceSerializer(service).data})

    @extend_schema(
        summary="Частично обновить услугу [Admin]",
        description="Обновляет отдельные поля услуги, например только цену (PATCH).",
        request=ServiceUpdateSerializer,
        responses={200: ServiceSerializer},
        tags=['Услуги'],
    )
    def partial_update(self, request, pk=None):
        """Частично обновляет поля услуги (PATCH). Удобно для изменения только цены."""
        service = get_object_or_404(Service, pk=pk)
        serializer = ServiceUpdateSerializer(service, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        service = serializer.save()
        return Response({'status': 'success', 'data': ServiceSerializer(service).data})

    @extend_schema(
        summary="Деактивировать услугу [Admin]",
        description="Выполняет мягкое удаление услуги: is_active=False.",
        responses={204: OpenApiResponse(description="Услуга деактивирована")},
        tags=['Услуги'],
    )
    def destroy(self, request, pk=None):
        """Деактивирует услугу (soft delete). Услуга скрывается но не удаляется из базы."""
        service = get_object_or_404(Service, pk=pk)
        service.is_active = False
        service.save()
        return Response(
            {'status': 'success', 'message': 'Услуга деактивирована'},
            status=HTTP_204_NO_CONTENT,
        )
