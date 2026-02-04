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
    MasterIngoSerializer

)


class MasterViewSet(ViewSet):
    """
    Master viewset
    """
    def list(self, request):
        queryset = Master.objects.all()
        serializer = MasterSerializer(queryset, many=True)
        return Response(
            serializer.data,
            status=HTTP_200_OK,
        )


    def retrieve(self, request, pk=None):
        queryset = Master.objects.all()
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
        queryset = Service.objects.filter(is_active=True)
        serializer = ServiceSerializer(queryset, many=True)
        return Response({
            'status': 'success',
            'count': queryset.count(),
            'data': serializer.data
        })


    def retrieve(self, request, pk=None):
        service = get_object_or_404(Service, pk=pk, is_active=True)
        serializer = ServiceSerializer(service)
        return Response({
            'status': 'success',
            'data': serializer.data
        })


    @action(detail=True, methods=['get'], url_path='service')
    def service(self, request, pk=None):
        """Services in salon"""
        service = get_object_or_404(Service, pk=pk, is_active=True)
        salon = service.salon.filter(is_active=True)

        serializer = ServiceSerializer(salon,many=True)

        return Response({
            'status': 'success',
            'salon': {
                'id': salon.id,
                'name': salon.name,
                'address': salon.address,
            },
            'count': salon.count(),
            'data': serializer.data
        })

