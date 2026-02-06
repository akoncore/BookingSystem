#Python modules
from logging import getLogger

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
    HTTP_204_NO_CONTENT
)

from .models import Master
#from rest_framework.permissions import IsAuthenticated

#Project Models
from .models import (
    Master,
    Salon,
    Service,
    Booking
)
from .serializers import (
    MasterSerializer,
    MasterRequestSerializer,
    SalonSerializer,
    ServiceSerializer,
    MasterIngoSerializer,
    ServiceUpdateSerializer,
    BookingSerializer,
    BookingBulkSerializer,
    BookingCancelSerializer,
    BookingCompleteSerializer,
    BookingConfirmSerializer

)

#Logging
logger = getLogger(__name__)


class MasterViewSet(ViewSet):
    """
    Master viewset
    """
    def list(self, request):
        queryset = Master.objects.select_related(
            'salon','user'
            )
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

    def destroy(self,request,pk=None):
        service = get_object_or_404(Service, pk=pk, is_active=True)
        service.delete()
        return Response(
            {
                'status': 'success',
                "message": "Service has been deleted"
            },
            status=HTTP_204_NO_CONTENT
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
        return Response(
            {
                'status': 'success',
                'services': {
                    "id":service.id,
                    'name':service.name,
                    'price':service.price,
                    'duration':service.duration,
                },
                'count': salons.count(),
                'data': salons_data
            }
        )


    @action(detail=True, methods=['get'], url_path='masters')
    def masters(self,request,pk=None):
        """
        Services in masters
        """
        service = get_object_or_404(Service, pk=pk, is_active=True)
        masters = Master.objects.filter(
            salon__services=service,
        ).distinct()

        serializer = MasterSerializer(masters, many=True)

        logger.info(
            "See masters user=%s count=%s",
            self.request.user,
            len(serializer.data)
        )
        return Response(
            {
                'status': 'success',
                'count': masters.count(),
                'data': serializer.data
            }
        )



class BookingViewSet(ViewSet):
    """
    Booking viewset
    """
    def list(self, request):
        logger.info("Booking list requested")

        queryset = (
            Booking.objects
            .select_related('salon', 'client', 'master')
            .prefetch_related('services')
        )

        serializer = BookingSerializer(queryset, many=True)

        logger.debug(
            "Bookings fetched",
            extra={
                "count": queryset.count(),
                "user_id": request.user.id if request.user.is_authenticated else None
            }
        )

        return Response(
            {
                'status': 'success',
                'count': queryset.count(),
                'data': serializer.data
            },
            status=HTTP_200_OK
        )


    def retrieve(self, request, pk=None):
        booking = get_object_or_404(Booking, pk=pk)
        serializer = BookingSerializer(booking)
        return Response(
            {
                'status': 'success',
                #'count': booking.count(),
                'data': serializer.data
            },
            status=HTTP_200_OK
        )


    def create(self, request):
        serializer = BookingSerializer(data=request.data)

        logger.warning(f"Preparing to create booking {serializer.data}")

        serializer.is_valid(raise_exception=True)
        booking = serializer.save()

        logger.info('Booking %s',booking)

        return Response(
            {
                'status': 'success',
                'count': booking.count(),
                'data': serializer.data
            },
            status=HTTP_201_CREATED
        )


    @action(detail=True, methods=['get'], url_path='masters')
    def masters(self, request, pk=None):
        """
        Services in masters
        """
        booking = get_object_or_404(Booking, pk=pk, is_active=True)
        masters = booking.masters.filter(is_active=True)
        serializer = BookingBulkSerializer(masters, many=True)

        masters_data = [
            {
                'id':master.id,
                'name':master.name,
            }
            for master in masters
        ]
        return Response(
            {
                'status': 'success',
                'count': masters.count(),
                'masters_data': masters_data,
                'data':serializer.data
            }
        )








