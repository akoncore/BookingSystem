# main/views.py

from logging import getLogger
from django.shortcuts import get_object_or_404
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
)

from .models import (
    Salon, 
    Master,
    Service, 
    Booking,
    WorkSchedule
)
from .serializers import (
    SalonSerializer,
    MasterSerializer,
    MasterIngoSerializer,
    MasterRequestSerializer,
    ServiceSerializer,
    ServiceUpdateSerializer,
    BookingSerializer,
    BookingConfirmSerializer,
    BookingCompleteSerializer,
    BookingCancelSerializer,
    BookingBulkSerializer,
    WorkScheduleSerializer
)

logger = getLogger(__name__)


class MasterViewSet(ViewSet):
    """Master viewset with full CRUD"""
    
    def list(self, request):
        """GET /api/masters/"""
        queryset = Master.objects.select_related('salon', 'user')
        serializer = MasterSerializer(queryset, many=True)
        return Response({
            'status': 'success',
            'count': queryset.count(),
            'data': serializer.data
        }, status=HTTP_200_OK)
    
    def retrieve(self, request, pk=None):
        """GET /api/masters/{id}/"""
        queryset = Master.objects.select_related('salon', 'user')
        master = get_object_or_404(queryset, pk=pk)
        serializer = MasterSerializer(master)
        return Response({
            'status': 'success',
            'data': serializer.data
        }, status=HTTP_200_OK)
    
    def create(self, request):
        """
        POST /api/masters/
        Admin creates master directly (auto-approved)
        """
        serializer = MasterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        master = serializer.save()
        
        logger.info("Master created: %s", master.id)
        
        return Response({
            'status': 'success',
            'message': 'Master created successfully',
            'data': MasterSerializer(master).data
        }, status=HTTP_201_CREATED)
    
    def update(self, request, pk=None):
        """PUT /api/masters/{id}/"""
        master = get_object_or_404(Master, pk=pk)
        serializer = MasterSerializer(master, data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)
        master = serializer.save()
        
        logger.info("Master updated: %s", master.id)
        
        return Response({
            'status': 'success',
            'message': 'Master updated successfully',
            'data': MasterSerializer(master).data
        }, status=HTTP_200_OK)
    
    def partial_update(self, request, pk=None):
        """PATCH /api/masters/{id}/"""
        master = get_object_or_404(Master, pk=pk)
        serializer = MasterSerializer(master, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        master = serializer.save()
        
        return Response({
            'status': 'success',
            'message': 'Master partially updated',
            'data': MasterSerializer(master).data
        }, status=HTTP_200_OK)
    
    def destroy(self, request, pk=None):
        """DELETE /api/masters/{id}/"""
        master = get_object_or_404(Master, pk=pk)
        user = master.user
        master.delete()
        user.delete()  # Also delete user account
        
        logger.warning("Master deleted: %s", pk)
        
        return Response({
            'status': 'success',
            'message': 'Master deleted successfully'
        }, status=HTTP_204_NO_CONTENT)
    
    @action(detail=False, methods=['post'], url_path='request-job')
    def request_job(self, request):
        """POST /api/masters/request-job/"""
        serializer = MasterRequestSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        master = serializer.save()
        
        logger.info("Job request created: %s", master.id)
        
        return Response({
            'status': 'success',
            'message': 'Job request sent successfully',
            'data': MasterSerializer(master).data
        }, status=HTTP_201_CREATED)


class SalonViewSet(ViewSet):
    """Salon viewset with full CRUD"""
    
    def list(self, request):
        """GET /api/salons/"""
        queryset = Salon.objects.filter(is_active=True)
        serializer = SalonSerializer(queryset, many=True)
        return Response({
            'status': 'success',
            'count': queryset.count(),
            'data': serializer.data
        }, status=HTTP_200_OK)
    
    def retrieve(self, request, pk=None):
        """GET /api/salons/{id}/"""
        salon = get_object_or_404(Salon, pk=pk, is_active=True)
        serializer = SalonSerializer(salon)
        return Response({
            'status': 'success',
            'data': serializer.data
        }, status=HTTP_200_OK)
    
    def create(self, request):
        """POST /api/salons/"""
        serializer = SalonSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        salon = serializer.save()
        
        logger.info("Salon created: %s", salon.id)
        
        return Response({
            'status': 'success',
            'message': 'Salon created successfully',
            'data': SalonSerializer(salon).data
        }, status=HTTP_201_CREATED)
    
    def update(self, request, pk=None):
        """PUT /api/salons/{id}/"""
        salon = get_object_or_404(Salon, pk=pk)
        serializer = SalonSerializer(salon, data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)
        salon = serializer.save()
        
        logger.info("Salon updated: %s", salon.id)
        
        return Response({
            'status': 'success',
            'message': 'Salon updated successfully',
            'data': SalonSerializer(salon).data
        }, status=HTTP_200_OK)
    
    def partial_update(self, request, pk=None):
        """PATCH /api/salons/{id}/"""
        salon = get_object_or_404(Salon, pk=pk)
        serializer = SalonSerializer(salon, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        salon = serializer.save()
        
        return Response({
            'status': 'success',
            'message': 'Salon partially updated',
            'data': SalonSerializer(salon).data
        }, status=HTTP_200_OK)
    
    def destroy(self, request, pk=None):
        """DELETE /api/salons/{id}/"""
        salon = get_object_or_404(Salon, pk=pk)
        salon.is_active = False  # Soft delete
        salon.save()
        
        logger.warning("Salon deactivated: %s", pk)
        
        return Response({
            'status': 'success',
            'message': 'Salon deleted successfully'
        }, status=HTTP_204_NO_CONTENT)
    
    @action(detail=True, methods=['get'], url_path='masters')
    def masters(self, request, pk=None):
        """GET /api/salons/{id}/masters/"""
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
        """GET /api/salons/{id}/services/"""
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
    """Service viewset with full CRUD"""
    
    def list(self, request):
        """GET /api/services/"""
        queryset = Service.objects.filter(is_active=True)
        serializer = ServiceSerializer(queryset, many=True)
        return Response({
            'status': 'success',
            'count': queryset.count(),
            'data': serializer.data
        }, status=HTTP_200_OK)
    
    def retrieve(self, request, pk=None):
        """GET /api/services/{id}/"""
        service = get_object_or_404(Service, pk=pk, is_active=True)
        serializer = ServiceSerializer(service)
        return Response({
            'status': 'success',
            'data': serializer.data
        }, status=HTTP_200_OK)
    
    def create(self, request):
        """POST /api/services/"""
        serializer = ServiceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        service = serializer.save()
        
        logger.info("Service created: %s", service.id)
        
        return Response({
            'status': 'success',
            'message': 'Service created successfully',
            'data': ServiceSerializer(service).data
        }, status=HTTP_201_CREATED)
    
    def update(self, request, pk=None):
        """PUT /api/services/{id}/"""
        service = get_object_or_404(Service, pk=pk)
        serializer = ServiceSerializer(service, data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)
        service = serializer.save()
        
        logger.info("Service updated: %s", service.id)
        
        return Response({
            'status': 'success',
            'message': 'Service updated successfully',
            'data': ServiceSerializer(service).data
        }, status=HTTP_200_OK)
    
    def partial_update(self, request, pk=None):
        """PATCH /api/services/{id}/"""
        service = get_object_or_404(Service, pk=pk)
        serializer = ServiceUpdateSerializer(service, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        service = serializer.save()
        
        return Response({
            'status': 'success',
            'message': 'Service partially updated',
            'data': ServiceSerializer(service).data
        }, status=HTTP_200_OK)
    
    def destroy(self, request, pk=None):
        """DELETE /api/services/{id}/"""
        service = get_object_or_404(Service, pk=pk)
        service.is_active = False  # Soft delete
        service.save()
        
        logger.warning("Service deactivated: %s", pk)
        
        return Response({
            'status': 'success',
            'message': 'Service deleted successfully'
        }, status=HTTP_204_NO_CONTENT)
    
    @action(detail=True, methods=['get'], url_path='salons')
    def salons(self, request, pk=None):
        """GET /api/services/{id}/salons/"""
        service = get_object_or_404(Service, pk=pk, is_active=True)
        salons = Salon.objects.filter(
            services__id=service.id,
            is_active=True
        ).distinct()
        
        salons_data = [
            {
                'id': salon.id,
                'name': salon.name,
                'address': salon.address,
                'masters_count': salon.masters.filter(is_approved=True).count(),
            }
            for salon in salons
        ]
        
        return Response({
            'status': 'success',
            'service': {
                'id': service.id,
                'name': service.name,
                'price': service.price,
                'duration': str(service.duration),
            },
            'count': salons.count(),
            'data': salons_data
        }, status=HTTP_200_OK)
    
    @action(detail=True, methods=['get'], url_path='masters')
    def masters(self, request, pk=None):
        """GET /api/services/{id}/masters/"""
        service = get_object_or_404(
            Service,
            pk=pk,
            is_active=True
            )
        masters = Master.objects.filter(
            salon__services=service,
            is_approved=True
        ).distinct()
        
        serializer = MasterSerializer(masters, many=True)
        
        logger.info(
            "Masters for service=%s, count=%s",
            service.id,
            masters.count()
        )
        
        return Response({
            'status': 'success',
            'count': masters.count(),
            'data': serializer.data
        }, status=HTTP_200_OK)



class BookingViewSet(ViewSet):
    """
    Booking viewset with full CRUD + status actions
    """
    
    def list(self, request):
        """GET /api/bookings/"""
        logger.info("Booking list requested")
        
        queryset = (
            Booking.objects
            .select_related('salon', 'client', 'master')
            .prefetch_related('services')
        )
        serializer = BookingSerializer(queryset, many=True)
        
        logger.debug("Bookings fetched: %s", queryset.count())
        
        return Response({
            'status': 'success',
            'count': queryset.count(),
            'data': serializer.data
        }, status=HTTP_200_OK)
    
    def retrieve(self, request, pk=None):
        """GET /api/bookings/{id}/"""
        booking = get_object_or_404(Booking, pk=pk)
        serializer = BookingSerializer(booking)
        return Response({
            'status': 'success',
            'data': serializer.data
        }, status=HTTP_200_OK)
    
    def create(self, request):
        """POST /api/bookings/"""
        serializer = BookingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        booking = serializer.save()
        
        logger.info("Booking created: %s", booking.booking_code)
        
        return Response({
            'status': 'success',
            'message': 'Booking created successfully',
            'data': BookingSerializer(booking).data
        }, status=HTTP_201_CREATED)
    
    def update(self, request, pk=None):
        """PUT /api/bookings/{id}/"""
        booking = get_object_or_404(Booking, pk=pk)
        serializer = BookingSerializer(
            booking,
            data=request.data,
            partial=False
            )
        serializer.is_valid(raise_exception=True)
        booking = serializer.save()
        
        logger.info("Booking updated: %s", booking.booking_code)
        
        return Response({
            'status': 'success',
            'message': 'Booking updated successfully',
            'data': BookingSerializer(booking).data
        }, status=HTTP_200_OK)
    
    def partial_update(self, request, pk=None):
        """PATCH /api/bookings/{id}/"""
        booking = get_object_or_404(Booking, pk=pk)
        serializer = BookingSerializer(
            booking,
            data=request.data, 
            partial=True
            )
        serializer.is_valid(raise_exception=True)
        booking = serializer.save()
        
        return Response({
            'status': 'success',
            'message': 'Booking partially updated',
            'data': BookingSerializer(booking).data
        }, status=HTTP_200_OK)
    
    def destroy(self, request, pk=None):
        """DELETE /api/bookings/{id}/"""
        booking = get_object_or_404(Booking, pk=pk)
        booking.delete()
        
        logger.warning("Booking deleted: %s", pk)
        
        return Response({
            'status': 'success',
            'message': 'Booking deleted successfully'
        }, status=HTTP_204_NO_CONTENT)
    
    # --- Status actions ---
    
    @action(detail=True, methods=['post'], url_path='confirm')
    def confirm(self, request, pk=None):
        """POST /api/bookings/{id}/confirm/"""
        booking = get_object_or_404(Booking, pk=pk)
        serializer = BookingConfirmSerializer(instance=booking, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        logger.info("Booking confirmed: %s", booking.booking_code)
        
        return Response({
            'status': 'success',
            'message': 'Booking confirmed',
            'data': BookingSerializer(booking).data
        }, status=HTTP_200_OK)
    
    
    @action(detail=True, methods=['post'], url_path='complete')
    def complete(self, request, pk=None):
        """POST /api/bookings/{id}/complete/"""
        booking = get_object_or_404(Booking, pk=pk)
        serializer = BookingCompleteSerializer(instance=booking, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        logger.info("Booking completed: %s", booking.booking_code)
        
        return Response({
            'status': 'success',
            'message': 'Booking completed',
            'data': BookingSerializer(booking).data
        }, status=HTTP_200_OK)
    
    
    @action(detail=True, methods=['post'], url_path='cancel')
    def cancel(self, request, pk=None):
        """POST /api/bookings/{id}/cancel/"""
        booking = get_object_or_404(Booking, pk=pk)
        serializer = BookingCancelSerializer(instance=booking, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        logger.info("Booking cancelled: %s", booking.booking_code)
        
        return Response({
            'status': 'success',
            'message': 'Booking cancelled',
            'data': BookingSerializer(booking).data
        }, status=HTTP_200_OK)

    
    # --- Bulk actions ---
    
    
    @action(detail=False, methods=['post'], url_path='bulk-confirm')
    def bulk_confirm(self, request):
        """POST /api/bookings/bulk-confirm/"""
        serializer = BookingBulkSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        ids = serializer.validated_data['booking_ids']
        updated = Booking.objects.filter(
            id__in=ids, status='pending'
        ).update(status='confirmed')
        
        logger.info("Bulk confirm: %s bookings", updated)
        
        return Response({
            'status': 'success',
            'message': f'{updated} booking(s) confirmed',
            'updated_count': updated
        }, status=HTTP_200_OK)
    
    @action(detail=False, methods=['post'], url_path='bulk-complete')
    def bulk_complete(self, request):
        """POST /api/bookings/bulk-complete/"""
        serializer = BookingBulkSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        ids = serializer.validated_data['booking_ids']
        updated = Booking.objects.filter(
            id__in=ids, status='confirmed'
        ).update(status='completed')
        
        logger.info("Bulk complete: %s bookings", updated)
        
        return Response({
            'status': 'success',
            'message': f'{updated} booking(s) completed',
            'updated_count': updated
        }, status=HTTP_200_OK)
    
    
    @action(detail=False, methods=['post'], url_path='bulk-cancel')
    def bulk_cancel(self, request):
        """POST /api/bookings/bulk-cancel/"""
        serializer = BookingBulkSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        ids = serializer.validated_data['booking_ids']
        updated = Booking.objects.filter(
            id__in=ids, status__in=['pending', 'confirmed']
        ).update(status='cancelled')
        
        logger.info("Bulk cancel: %s bookings", updated)
        
        return Response({
            'status': 'success',
            'message': f'{updated} booking(s) cancelled',
            'updated_count': updated
        }, status=HTTP_200_OK)
    


class WorkScheduleViewSet(ViewSet):
    """
    Docstring для WorkScheduleViewSet
    """
    def list(self,request):
        queryset = WorkSchedule.objects.all()
        serializer = WorkScheduleSerializer(queryset,many=True)
        return Response(
            {
                'message':'List of Work Schedule',
                'data':serializer.data
            }
        )
    