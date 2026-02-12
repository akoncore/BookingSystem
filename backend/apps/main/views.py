# apps/main/views.py - COMPLETE VERSION WITH ALL FEATURES

from logging import getLogger
from datetime import datetime, timedelta, time as dt_time
from django.shortcuts import get_object_or_404
from django.db.models import Q
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
    HTTP_403_FORBIDDEN,
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
    WorkScheduleSerializer,
    WorkScheduleUpdateSerializer,
)

# Import custom permissions
from .permissions import (
    IsClient,
    IsAdmin,
    IsMaster,
    IsAdminOrMaster,
    IsOwnerOrAdmin,
    IsBookingParticipant,
    CanManageWorkSchedule,
)

# Import services
from apps.services.notifications import NotificationService
from apps.services.analytics import AnalyticsService
from apps.services.payment import PaymentService, CancellationPolicy

logger = getLogger(__name__)


class MasterViewSet(ViewSet):
    """Master viewset with full CRUD"""
    
    permission_classes = [IsAuthenticated]
    
    def get_permissions(self):
        """Әр action үшін өз permission-дары"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdmin()]
        return [IsAuthenticated()]
    
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
        """POST /api/masters/ - Only Admin"""
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
        """PUT /api/masters/{id}/ - Only Admin"""
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
        """PATCH /api/masters/{id}/ - Only Admin"""
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
        """DELETE /api/masters/{id}/ - Only Admin"""
        master = get_object_or_404(Master, pk=pk)
        user = master.user
        master.delete()
        user.delete()
        
        logger.warning("Master deleted: %s", pk)
        
        return Response({
            'status': 'success',
            'message': 'Master deleted successfully'
        }, status=HTTP_204_NO_CONTENT)
    
    @action(detail=False, methods=['post'], url_path='request-job')
    def request_job(self, request):
        """POST /api/masters/request-job/ - Any authenticated user"""
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
    
    def get_permissions(self):
        """Әр action үшін өз permission-дары"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdmin()]
        return [AllowAny()]  # Барлығы салондарды көре алады
    
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
        """POST /api/salons/ - Only Admin"""
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
        """PUT /api/salons/{id}/ - Only Admin"""
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
        """PATCH /api/salons/{id}/ - Only Admin"""
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
        """DELETE /api/salons/{id}/ - Only Admin"""
        salon = get_object_or_404(Salon, pk=pk)
        salon.is_active = False
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
    
    def get_permissions(self):
        """Әр action үшін өз permission-дары"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdmin()]
        return [AllowAny()]
    
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
        """POST /api/services/ - Only Admin"""
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
        """PUT /api/services/{id}/ - Only Admin"""
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
        """PATCH /api/services/{id}/ - Only Admin"""
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
        """DELETE /api/services/{id}/ - Only Admin"""
        service = get_object_or_404(Service, pk=pk)
        service.is_active = False
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
        service = get_object_or_404(Service, pk=pk, is_active=True)
        masters = Master.objects.filter(
            salon__services=service,
            is_approved=True
        ).distinct()
        
        serializer = MasterSerializer(masters, many=True)


        return Response({
            'status': 'success',
            'count': masters.count(),
            'data': serializer.data
        }, status=HTTP_200_OK)



class BookingViewSet(ViewSet):
    """
    Booking viewset - ТОЛЫҚ ФУНКЦИОНАЛ
    """
    
    permission_classes = [IsAuthenticated]
    
    def get_permissions(self):
        """Әр action үшін өз permission-дары"""
        if self.action == 'create':
            return [IsClient()]  # Тек клиент booking жасай алады
        elif self.action in ['confirm', 'complete']:
            return [IsMaster()]  # Тек мастер растай/аяқтай алады
        elif self.action in ['list', 'retrieve']:
            return [IsAuthenticated()]
        return [IsAuthenticated()]
    
    def list(self, request):
        """GET /api/bookings/ - Роліне қарай фильтрленеді"""
        user = request.user
        
        if user.is_client:
            # Клиент тек өзінің booking-тарын көреді
            queryset = Booking.objects.filter(client=user)
        elif user.is_master:
            # Мастер өзіне жасалған booking-тарды көреді
            queryset = Booking.objects.filter(master=user)
        elif user.is_admin:
            # Admin өз салондарының booking-тарын көреді
            salons = Salon.objects.filter(owner=user)
            queryset = Booking.objects.filter(salon__in=salons)
        else:
            queryset = Booking.objects.none()
        
        queryset = queryset.select_related(
            'salon', 'client', 'master'
        ).prefetch_related('services')
        
        serializer = BookingSerializer(queryset, many=True)


        return Response({
            'status': 'success',
            'count': queryset.count(),
            'data': serializer.data
        }, status=HTTP_200_OK)
    
    def retrieve(self, request, pk=None):
        """GET /api/bookings/{id}/"""
        booking = get_object_or_404(Booking, pk=pk)
        
        # Тек қатысушылар көре алады
        user = request.user
        if not (
            user.is_admin or
            booking.client == user or
            booking.master == user
        ):
            return Response({
                'status': 'error',
                'message': 'You do not have permission to view this booking'
            }, status=HTTP_403_FORBIDDEN)
        
        serializer = BookingSerializer(booking)
        return Response({
            'status': 'success',
            'data': serializer.data
        }, status=HTTP_200_OK)
    
    def create(self, request):
        """
        POST /api/bookings/ - Only Client
        
        ✨ ЖАҢА ФУНКЦИОНАЛ:
        - Мастердің жұмыс уақытын тексереді
        - Қайталанатын booking-тарды блоктайды
        - Email хабарламалары жіберед

i
        """
        serializer = BookingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Validate time availability
        master_id = request.data.get('master')
        appointment_date = request.data.get('appointment_date')
        appointment_time = request.data.get('appointment_time')
        
        # Check if master is working on that day and time
        if not self._is_master_available(master_id, appointment_date, appointment_time):
            return Response({
                'status': 'error',
                'message': 'Master is not available at this time'
            }, status=HTTP_400_BAD_REQUEST)
        
        # Check for conflicting bookings
        if self._has_conflicting_booking(master_id, appointment_date, appointment_time):
            return Response({
                'status': 'error',
                'message': 'This time slot is already booked'
            }, status=HTTP_400_BAD_REQUEST)
        
        booking = serializer.save()
        
        # Send notifications ✨
        NotificationService.send_booking_created_to_client(booking)
        NotificationService.send_booking_created_to_master(booking)
        
        logger.info("Booking created: %s", booking.booking_code)
        
        return Response({
            'status': 'success',
            'message': 'Booking created successfully',
            'data': BookingSerializer(booking).data
        }, status=HTTP_201_CREATED)
    
    def _is_master_available(self, master_id, appointment_date, appointment_time):
        """Мастердің сол күні жұмыс істейтінін тексереді"""
        try:
            date_obj = datetime.strptime(appointment_date, '%Y-%m-%d').date()
            time_obj = datetime.strptime(appointment_time, '%H:%M:%S').time()
            
            weekday = date_obj.weekday()
            
            schedule = WorkSchedule.objects.filter(
                master_id=master_id,
                weekday=weekday,
                is_working=True
            ).first()
            
            if not schedule:
                return False
            
            return schedule.start_time <= time_obj <= schedule.end_time
            
        except Exception as e:
            logger.error(f"Error checking master availability: {e}")
            return False
    
    def _has_conflicting_booking(self, master_id, appointment_date, appointment_time):
        """Қайталанатын booking бар ма тексереді"""
        return Booking.objects.filter(
            master_id=master_id,
            appointment_date=appointment_date,
            appointment_time=appointment_time,
            status__in=['pending', 'confirmed']
        ).exists()
    
    def update(self, request, pk=None):
        """PUT /api/bookings/{id}/"""
        booking = get_object_or_404(Booking, pk=pk)
        serializer = BookingSerializer(booking, data=request.data, partial=False)
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
        serializer = BookingSerializer(booking, data=request.data, partial=True)
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
        """POST /api/bookings/{id}/confirm/ - Only Master"""
        booking = get_object_or_404(Booking, pk=pk)
        
        # Тек өз booking-ын растай алады
        if booking.master != request.user:
            return Response({
                'status': 'error',
                'message': 'You can only confirm your own bookings'
            }, status=HTTP_403_FORBIDDEN)
        
        serializer = BookingConfirmSerializer(instance=booking, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        # Send confirmation email ✨
        NotificationService.send_booking_confirmed(booking)
        
        logger.info("Booking confirmed: %s", booking.booking_code)
        
        return Response({
            'status': 'success',
            'message': 'Booking confirmed',
            'data': BookingSerializer(booking).data
        }, status=HTTP_200_OK)
    
    @action(detail=True, methods=['post'], url_path='complete')
    def complete(self, request, pk=None):
        """POST /api/bookings/{id}/complete/ - Only Master"""
        booking = get_object_or_404(Booking, pk=pk)
        
        # Тек өз booking-ын аяқтай алады
        if booking.master != request.user:
            return Response({
                'status': 'error',
                'message': 'You can only complete your own bookings'
            }, status=HTTP_403_FORBIDDEN)
        
        serializer = BookingCompleteSerializer(instance=booking, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        # Send completion email ✨
        NotificationService.send_booking_completed(booking)
        
        # Process payment ✨
        payment_result = PaymentService.process_payment(booking)
        
        logger.info("Booking completed: %s", booking.booking_code)
        
        return Response({
            'status': 'success',
            'message': 'Booking completed',
            'data': BookingSerializer(booking).data,
            'payment': payment_result
        }, status=HTTP_200_OK)
    

    @action(detail=True, methods=['post'], url_path='cancel')
    def cancel(self, request, pk=None):
        """
        POST /api/bookings/{id}/cancel/
        
        ✨ ЖАҢА: 24-сағаттық cancellation policy
        """
        booking = get_object_or_404(Booking, pk=pk)
        
        # Determine who is cancelling
        if booking.client == request.user:
            cancelled_by = 'client'
        elif booking.master == request.user:
            cancelled_by = 'master'
        elif request.user.is_admin:
            cancelled_by = 'admin'
        else:
            return Response({
                'status': 'error',
                'message': 'You do not have permission to cancel this booking'
            }, status=HTTP_403_FORBIDDEN)
        
        # Process cancellation with policy ✨
        result = CancellationPolicy.process_cancellation(booking, cancelled_by)
        
        if not result['success']:
            return Response({
                'status': 'error',
                'message': result['message']
            }, status=HTTP_400_BAD_REQUEST)
        
        # Send cancellation email ✨
        NotificationService.send_booking_cancelled(booking, cancelled_by)
        
        logger.info("Booking cancelled: %s by %s", booking.booking_code, cancelled_by)
        
        return Response({
            'status': 'success',
            'message': 'Booking cancelled',
            'data': BookingSerializer(booking).data,
            'cancellation': result
        }, status=HTTP_200_OK)
    
    @action(detail=True, methods=['get'], url_path='cancellation-policy')
    def get_cancellation_policy(self, request, pk=None):
        """
        GET /api/bookings/{id}/cancellation-policy/
        
        ✨ ЖАҢА: Болдырмау саясатын көру
        """
        booking = get_object_or_404(Booking, pk=pk)
        
        can_cancel, reason = CancellationPolicy.can_cancel(booking)
        refund_info = CancellationPolicy.get_refund_amount(booking)
        
        return Response({
            'status': 'success',
            'booking_code': booking.booking_code,
            'can_cancel': can_cancel,
            'reason': reason,
            'refund_policy': refund_info
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
    WorkSchedule ViewSet - ТОЛЫҚ CRUD
    """
    
    permission_classes = [CanManageWorkSchedule]
    
    def list(self, request):
        """GET /api/work-schedules/"""
        # Admin барлық кестелерді көреді
        # Master тек өзінікін көреді
        if request.user.is_admin:
            queryset = WorkSchedule.objects.all()
        else:
            queryset = WorkSchedule.objects.filter(master=request.user)
        
        queryset = queryset.select_related('master')
        serializer = WorkScheduleSerializer(queryset, many=True)
        
        return Response({
            'status': 'success',
            'count': queryset.count(),
            'data': serializer.data
        }, status=HTTP_200_OK)
    
    def retrieve(self, request, pk=None):
        """GET /api/work-schedules/{id}/"""
        schedule = get_object_or_404(WorkSchedule, pk=pk)
        
        # Permission check
        self.check_object_permissions(request, schedule)
        
        serializer = WorkScheduleSerializer(schedule)
        return Response({
            'status': 'success',
            'data': serializer.data
        }, status=HTTP_200_OK)
    
    def create(self, request):
        """POST /api/work-schedules/"""
        serializer = WorkScheduleUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        schedule = serializer.save()
        
        logger.info(
            "WorkSchedule created for master=%s, weekday=%s",
            schedule.master_id, schedule.weekday
        )
        
        return Response({
            'status': 'success',
            'message': 'Work schedule created successfully',
            'data': WorkScheduleSerializer(schedule).data
        }, status=HTTP_201_CREATED)
    
    def update(self, request, pk=None):
        """PUT /api/work-schedules/{id}/"""
        schedule = get_object_or_404(WorkSchedule, pk=pk)
        self.check_object_permissions(request, schedule)
        
        serializer = WorkScheduleUpdateSerializer(
            schedule, data=request.data, partial=False
        )
        serializer.is_valid(raise_exception=True)
        schedule = serializer.save()
        
        logger.info("WorkSchedule updated: %s", pk)
        
        return Response({
            'status': 'success',
            'message': 'Work schedule updated successfully',
            'data': WorkScheduleSerializer(schedule).data
        }, status=HTTP_200_OK)
    
    def partial_update(self, request, pk=None):
        """PATCH /api/work-schedules/{id}/"""
        schedule = get_object_or_404(WorkSchedule, pk=pk)
        self.check_object_permissions(request, schedule)
        
        serializer = WorkScheduleUpdateSerializer(
            schedule, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        schedule = serializer.save()
        
        return Response({
            'status': 'success',
            'message': 'Work schedule partially updated',
            'data': WorkScheduleSerializer(schedule).data
        }, status=HTTP_200_OK)
    
    def destroy(self, request, pk=None):
        """DELETE /api/work-schedules/{id}/"""
        schedule = get_object_or_404(WorkSchedule, pk=pk)
        self.check_object_permissions(request, schedule)
        
        schedule.delete()
        
        logger.warning("WorkSchedule deleted: %s", pk)
        
        return Response({
            'status': 'success',
            'message': 'Work schedule deleted successfully'
        }, status=HTTP_204_NO_CONTENT)
    
    @action(detail=False, methods=['get'], url_path='master/(?P<master_id>[^/.]+)')
    def by_master(self, request, master_id=None):
        """GET /api/work-schedules/master/{master_id}/"""
        schedules = WorkSchedule.objects.filter(
            master_id=master_id
        ).order_by('weekday')
        
        if not schedules.exists():
            return Response({
                'status': 'error',
                'message': 'No work schedule found for this master'
            }, status=HTTP_400_BAD_REQUEST)
        
        serializer = WorkScheduleSerializer(schedules, many=True)
        
        return Response({
            'status': 'success',
            'master_id': int(master_id),
            'count': schedules.count(),
            'data': serializer.data
        }, status=HTTP_200_OK)
    
    @action(detail=False, methods=['get'], url_path='available-slots')
    def available_slots(self, request):
        """
        GET /api/work-schedules/available-slots/?master_id=5&date=2026-01-20
        
        Мастердің еркін уақыттарын көрсетеді
        """
        master_id = request.query_params.get('master_id')
        date_str = request.query_params.get('date')
        
        if not master_id or not date_str:
            return Response({
                'status': 'error',
                'message': 'master_id and date are required'
            }, status=HTTP_400_BAD_REQUEST)
        
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            weekday = date_obj.weekday()
            
            schedule = WorkSchedule.objects.filter(
                master_id=master_id,
                weekday=weekday
            ).first()
            
            if not schedule or not schedule.is_working:
                return Response({
                    'status': 'success',
                    'master_id': int(master_id),
                    'date': date_str,
                    'weekday': date_obj.strftime('%A'),
                    'working': False,
                    'message': 'Master is not working on this day'
                }, status=HTTP_200_OK)
            
            all_slots = self._generate_time_slots(
                schedule.start_time,
                schedule.end_time,
                interval_minutes=30
            )
            
            booked_bookings = Booking.objects.filter(
                master_id=master_id,
                appointment_date=date_obj,
                status__in=['pending', 'confirmed']
            ).values_list('appointment_time', flat=True)
            
            booked_slots = [t.strftime('%H:%M') for t in booked_bookings]
            
            available_slots = [
                slot for slot in all_slots
                if slot not in booked_slots
            ]
            
            return Response({
                'status': 'success',
                'master_id': int(master_id),
                'date': date_str,
                'weekday': date_obj.strftime('%A'),
                'working': True,
                'work_hours': {
                    'start': schedule.start_time.strftime('%H:%M:%S'),
                    'end': schedule.end_time.strftime('%H:%M:%S')
                },
                'total_slots': len(all_slots),
                'available_slots': available_slots,
                'booked_slots': booked_slots
            }, status=HTTP_200_OK)
            
        except ValueError:
            return Response({
                'status': 'error',
                'message': 'Invalid date format. Use YYYY-MM-DD'
            }, status=HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error getting available slots: {e}")
            return Response({
                'status': 'error',
                'message': 'Internal server error'
            }, status=HTTP_400_BAD_REQUEST)
    
    def _generate_time_slots(self, start_time, end_time, interval_minutes=30):
        """Generate time slots between start and end time"""
        slots = []
        current = datetime.combine(datetime.today(), start_time)
        end = datetime.combine(datetime.today(), end_time)
        
        while current < end:
            slots.append(current.strftime('%H:%M'))
            current += timedelta(minutes=interval_minutes)
        
        return slots


class AnalyticsViewSet(ViewSet):
    """
    ✨ ЖАҢА: Analytics ViewSet - Статистика және есептер
    """
    
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'], url_path='top-masters')
    def top_masters(self, request):
        """
        GET /api/analytics/top-masters/?salon_id=1&limit=10&period_days=30
        
        Ең танымал мастерлер
        """
        salon_id = request.query_params.get('salon_id')
        limit = int(request.query_params.get('limit', 10))
        period_days = int(request.query_params.get('period_days', 30))
        
        data = AnalyticsService.get_top_masters(salon_id, limit, period_days)
        
        return Response({
            'status': 'success',
            'data': data
        }, status=HTTP_200_OK)
    
    @action(detail=False, methods=['get'], url_path='top-services')
    def top_services(self, request):
        """
        GET /api/analytics/top-services/?salon_id=1&limit=10&period_days=30
        
        Ең көп тапсырыс берілген қызметтер
        """
        salon_id = request.query_params.get('salon_id')
        limit = int(request.query_params.get('limit', 10))
        period_days = int(request.query_params.get('period_days', 30))
        
        data = AnalyticsService.get_top_services(salon_id, limit, period_days)
        
        return Response({
            'status': 'success',
            'data': data
        }, status=HTTP_200_OK)
    
    @action(detail=False, methods=['get'], url_path='revenue')
    def revenue_statistics(self, request):
        """
        GET /api/analytics/revenue/?salon_id=1&period_days=30
        
        Кірістер статистикасы
        """
        salon_id = request.query_params.get('salon_id')
        period_days = int(request.query_params.get('period_days', 30))
        
        data = AnalyticsService.get_revenue_statistics(salon_id, period_days)
        
        return Response({
            'status': 'success',
            'data': data
        }, status=HTTP_200_OK)
    
    @action(detail=False, methods=['get'], url_path='salon-performance')
    def salon_performance(self, request):
        """
        GET /api/analytics/salon-performance/?salon_id=1&period_days=30
        
        Салон өнімділігі
        """
        salon_id = request.query_params.get('salon_id')
        period_days = int(request.query_params.get('period_days', 30))
        
        if not salon_id:
            return Response({
                'status': 'error',
                'message': 'salon_id is required'
            }, status=HTTP_400_BAD_REQUEST)
        
        data = AnalyticsService.get_salon_performance(
            int(salon_id), period_days
        )
        
        return Response({
            'status': 'success',
            'data': data
        }, status=HTTP_200_OK)
    
    @action(detail=False, methods=['get'], url_path='master-earnings')
    def master_earnings(self, request):
        """
        GET /api/analytics/master-earnings/?master_id=1&period_days=30
        
        ✨ Мастердің табысы және комиссиясы
        """
        master_id = request.query_params.get('master_id')
        period_days = int(request.query_params.get('period_days', 30))
        
        if not master_id:
            return Response({
                'status': 'error',
                'message': 'master_id is required'
            }, status=HTTP_400_BAD_REQUEST)
        
        data = AnalyticsService.get_master_earnings(
            int(master_id), period_days
        )
        
        return Response({
            'status': 'success',
            'data': data
        }, status=HTTP_200_OK)
    
    @action(detail=False, methods=['get'], url_path='dashboard')
    def dashboard(self, request):
        """
        GET /api/analytics/dashboard/
        
        ✨ Пайдаланушы роліне қарай dashboard
        """
        data = AnalyticsService.get_dashboard_summary(request.user)
        
        return Response({
            'status': 'success',
            'user_role': request.user.role,
            'data': data
        }, status=HTTP_200_OK)


class PaymentViewSet(ViewSet):
    """
    ✨ ЖАҢА: Payment ViewSet - Төлем және баланстар
    """
    
    permission_classes = [IsAuthenticated]
    
    @action(detail=True, methods=['get'], url_path='split')
    def payment_split(self, request, pk=None):
        """
        GET /api/payments/{booking_id}/split/
        
        Booking-тан түскен табысты бөлу
        """
        booking = get_object_or_404(Booking, pk=pk)
        
        data = PaymentService.calculate_split(booking)
        
        return Response({
            'status': 'success',
            'data': data
        }, status=HTTP_200_OK)
    
    @action(detail=False, methods=['get'], url_path='master-balance')
    def master_balance(self, request):
        """
        GET /api/payments/master-balance/?master_id=1&period_days=30
        
        ✨ Мастердің балансы
        """
        master_id = request.query_params.get('master_id')
        period_days = int(request.query_params.get('period_days', 30))
        
        if not master_id:
            return Response({
                'status': 'error',
                'message': 'master_id is required'
            }, status=HTTP_400_BAD_REQUEST)
        
        data = PaymentService.get_master_balance(
            int(master_id), period_days
        )
        
        return Response({
            'status': 'success',
            'data': data
        }, status=HTTP_200_OK)
    
    @action(detail=False, methods=['get'], url_path='salon-balance')
    def salon_balance(self, request):
        """
        GET /api/payments/salon-balance/?salon_id=1&period_days=30
        
        ✨ Салонның балансы
        """
        salon_id = request.query_params.get('salon_id')
        period_days = int(request.query_params.get('period_days', 30))
        
        if not salon_id:
            return Response({
                'status': 'error',
                'message': 'salon_id is required'
            }, status=HTTP_400_BAD_REQUEST)
        
        data = PaymentService.get_salon_balance(
            int(salon_id), period_days
        )
        
        return Response({
            'status': 'success',
            'data': data
        }, status=HTTP_200_OK)