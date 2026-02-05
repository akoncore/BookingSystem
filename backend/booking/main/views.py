#Django Models
from django.shortcuts import get_object_or_404


#REST Models
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_404_NOT_FOUND,
    HTTP_400_BAD_REQUEST,
    HTTP_201_CREATED,
)

from .models import Master
#from rest_framework.permissions import IsAuthenticated

#Project Models
from .models import (
    Master,
    Salon,
    Service
)
from .serializers import (
    MasterSerializer,
    MasterRequestSerializer,
    SalonSerializer,
    ServiceSerializer,
    MasterIngoSerializer,
    ServiceUpdateSerializer

)


class MasterViewSet(ViewSet):
    """
    Master viewset
    """
    def list(self, request):
        queryset = Master.objects.select_related('salon','user')
        serializer = MasterSerializer(queryset, many=True)
        return Response(
            serializer.data,
            status=HTTP_200_OK,
        )


    def retrieve(self, request, pk=None):
        queryset = Master.objects.select_related('salon','user')
        user = get_object_or_404(queryset, pk=pk)
        serializer = MasterSerializer(user)
        return Response(
            serializer.data,
            status=HTTP_200_OK,
        )


    @action(detail=False, methods=['post'], url_path='request-job')
    def request_job(self,request):
        serializer = MasterRequestSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        master = serializer.save()

        return Response({
            'status':'success',
            'message':'Request job has been requested',
            'data':MasterSerializer(master).data
            },status=HTTP_200_OK
        )


class SalonViewSet(ViewSet):
    """
    Salon viewset
    """

    def list(self, request):
        """
        List all salons
        """
        queryset = Salon.objects.filter(is_active=True)
        serializer = SalonSerializer(queryset, many=True)
        return Response({
            'status': 'success',
            'count': queryset.count(),
            'data': serializer.data
        }, status=HTTP_200_OK)

    def retrieve(self, request, pk=None):
        """
        Get single salon
        """
        salon = get_object_or_404(Salon, pk=pk, is_active=True)
        serializer = SalonSerializer(salon)
        return Response({
            'status': 'success',
            'data': serializer.data
        }, status=HTTP_200_OK)

    @action(detail=True, methods=['get'], url_path='masters')
    def masters(self, request, pk=None):
        """
        Get all masters in this salon
        """
        salon = get_object_or_404(Salon, pk=pk, is_active=True)
        masters = salon.masters.filter(is_approved=True)

        serializer = MasterIngoSerializer(masters, many=True)

        return Response({
            'status': 'success',
            'salon': {
                'id': salon.id,
                'name': salon.name,
                'address': salon.address,
            },
            'master_count': masters.count(),
            'data': serializer.data
        }, status=HTTP_200_OK)

    @action(detail=True, methods=['get'], url_path='services')
    def services(self, request, pk=None):
        """
        Get all services in this salon
        """
        salon = get_object_or_404(Salon, pk=pk, is_active=True)
        services = salon.services.filter(is_active=True)

        serializer = ServiceSerializer(services, many=True)

        return Response({
            'status': 'success',
            'salon': {
                'id': salon.id,
                'name': salon.name,
                'address': salon.address,
            },
            'count': services.count(),
            'data': serializer.data
        }, status=HTTP_200_OK)


class ServiceViewSet(ViewSet):
    """
    Service viewset
    """
    def list(self, request):
        """
        List all services
        """
        queryset = Service.objects.filter(is_active=True)
        serializer = ServiceSerializer(queryset, many=True)
        return Response({
            'status': 'success',
            'count': queryset.count(),
            'data': serializer.data
        })


    def retrieve(self, request, pk=None):
        """
        Get single service
        """
        service = get_object_or_404(Service, pk=pk, is_active=True)
        serializer = ServiceSerializer(service)
        return Response({
            'status': 'success',
            'data': serializer.data
        })


    def create(self, request):
        """
        Create new service
        """
        serializer = ServiceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = serializer.save()

        return Response(
            serializer.data,
            status=HTTP_201_CREATED
        )


    def update(self, request, pk=None):
        """
        Update existing service
        """
        service = get_object_or_404(Service, pk=pk, is_active=True)

        serializer = ServiceUpdateSerializer(
            service,
            data=request.data
        )

        serializer.is_valid(raise_exception=True)
        service = serializer.save()

        return Response(
            serializer.data,
            status=HTTP_200_OK
        )


    @action(detail=True, methods=['get'], url_path='salons')
    def salons(self, request,pk=None):
        """
        Services in salon
        """
        service = get_object_or_404(Service, pk=pk, is_active=True)

        salons = Salon.objects.filter(
            services__id=service.id,
            is_active=True
        ).distinct()

        salons_data = [
            {
                'id':salon.id,
                'name':salon.name,
                'address':salon.address,
                'salons_masters_count':salon.masters.filter(
                    is_approved=True
                ).count(),
            }
            for salon in salons
        ]

        return Response({
            'status': 'success',
            'services': {
                'id':service.id,
                'name':service.name,
                'price':service.price,
                'duration':service.duration,
            },
            'count': salons.count(),
            'data': salons_data
        })






