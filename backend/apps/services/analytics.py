# apps/main/services/analytics.py
"""
Analytics service for statistics and reports
"""

from django.db.models import Count, Sum, Avg, Q, F
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from ..main.models import Booking, Master, Service, Salon


class AnalyticsService:
    """Статистика және аналитика сервисі"""
    
    @staticmethod
    def get_top_masters(salon_id=None, limit=10, period_days=30):
        """
        Ең танымал мастерлер
        
        Args:
            salon_id: Салон ID (опционал)
            limit: Қанша мастерді қайтару
            period_days: Қанша күн артқа қарау
            
        Returns:
            List of masters with booking count and revenue
        """
        start_date = timezone.now().date() - timedelta(days=period_days)
        
        # Base queryset
        masters = Master.objects.filter(is_approved=True)
        
        if salon_id:
            masters = masters.filter(salon_id=salon_id)
        
        # Annotate with statistics
        masters = masters.annotate(
            total_bookings=Count(
                'user__master_appointments',
                filter=Q(
                    user__master_appointments__appointment_date__gte=start_date,
                    user__master_appointments__status='completed'
                )
            ),
            total_revenue=Sum(
                'user__master_appointments__total_price',
                filter=Q(
                    user__master_appointments__appointment_date__gte=start_date,
                    user__master_appointments__status='completed'
                )
            ),
            avg_rating=Avg('user__master_appointments__total_price')  # Placeholder
        ).order_by('-total_bookings')[:limit]
        
        result = []
        for master in masters:
            result.append({
                'master_id': master.id,
                'master_name': master.user.full_name,
                'salon': master.salon.name,
                'specialization': master.specialization,
                'total_bookings': master.total_bookings or 0,
                'total_revenue': float(master.total_revenue or 0),
                'avg_booking_value': (
                    float(master.total_revenue / master.total_bookings)
                    if master.total_bookings and master.total_revenue
                    else 0
                ),
            })
        
        return result
    
    @staticmethod
    def get_top_services(salon_id=None, limit=10, period_days=30):
        """
        Ең көп тапсырыс берілген қызметтер
        
        Args:
            salon_id: Салон ID (опционал)
            limit: Қанша қызметті қайтару
            period_days: Қанша күн артқа қарау
            
        Returns:
            List of services with booking count and revenue
        """
        start_date = timezone.now().date() - timedelta(days=period_days)
        
        # Base queryset
        services = Service.objects.filter(is_active=True)
        
        if salon_id:
            services = services.filter(salon_id=salon_id)
        
        # Annotate with statistics
        services = services.annotate(
            times_booked=Count(
                'bookings',
                filter=Q(
                    bookings__appointment_date__gte=start_date,
                    bookings__status='completed'
                )
            ),
            total_revenue=Sum(
                'price',
                filter=Q(
                    bookings__appointment_date__gte=start_date,
                    bookings__status='completed'
                )
            ) * Count(
                'bookings',
                filter=Q(
                    bookings__appointment_date__gte=start_date,
                    bookings__status='completed'
                )
            )
        ).order_by('-times_booked')[:limit]
        
        result = []
        for service in services:
            result.append({
                'service_id': service.id,
                'service_name': service.name,
                'salon': service.salon.name,
                'price': float(service.price),
                'times_booked': service.times_booked or 0,
                'estimated_revenue': float(service.price * (service.times_booked or 0)),
            })
        
        return result
    
    @staticmethod
    def get_revenue_statistics(salon_id=None, period_days=30):
        """
        Кірістер статистикасы
        
        Args:
            salon_id: Салон ID (опционал)
            period_days: Қанша күн артқа қарау
            
        Returns:
            Revenue statistics dict
        """
        start_date = timezone.now().date() - timedelta(days=period_days)
        
        # Base queryset
        bookings = Booking.objects.filter(
            appointment_date__gte=start_date,
            status='completed'
        )
        
        if salon_id:
            bookings = bookings.filter(salon_id=salon_id)
        
        # Calculate statistics
        total_bookings = bookings.count()
        total_revenue = bookings.aggregate(Sum('total_price'))['total_price__sum'] or 0
        avg_booking_value = (
            bookings.aggregate(Avg('total_price'))['total_price__avg'] or 0
        )
        
        # Daily breakdown
        daily_stats = []
        for i in range(period_days):
            date = start_date + timedelta(days=i)
            day_bookings = bookings.filter(appointment_date=date)
            day_revenue = day_bookings.aggregate(Sum('total_price'))['total_price__sum'] or 0
            
            daily_stats.append({
                'date': date.strftime('%Y-%m-%d'),
                'bookings': day_bookings.count(),
                'revenue': float(day_revenue)
            })
        
        # Status breakdown
        status_breakdown = []
        for status_code, status_name in Booking.STATUS_CHOICES:
            count = Booking.objects.filter(
                appointment_date__gte=start_date,
                status=status_code
            ).count()
            
            if salon_id:
                count = Booking.objects.filter(
                    salon_id=salon_id,
                    appointment_date__gte=start_date,
                    status=status_code
                ).count()
            
            status_breakdown.append({
                'status': status_name,
                'count': count,
                'percentage': round(count / total_bookings * 100, 2) if total_bookings else 0
            })
        
        return {
            'period': f'Last {period_days} days',
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': timezone.now().date().strftime('%Y-%m-%d'),
            'total_bookings': total_bookings,
            'total_revenue': float(total_revenue),
            'avg_booking_value': float(avg_booking_value),
            'daily_stats': daily_stats,
            'status_breakdown': status_breakdown,
        }
    
    @staticmethod
    def get_salon_performance(salon_id, period_days=30):
        """
        Салон өнімділігі статистикасы
        
        Args:
            salon_id: Салон ID
            period_days: Қанша күн артқа қарау
            
        Returns:
            Salon performance statistics
        """
        start_date = timezone.now().date() - timedelta(days=period_days)
        
        salon = Salon.objects.get(id=salon_id)
        
        # Bookings statistics
        bookings = Booking.objects.filter(
            salon_id=salon_id,
            appointment_date__gte=start_date
        )
        
        completed_bookings = bookings.filter(status='completed')
        cancelled_bookings = bookings.filter(status='cancelled')
        
        # Revenue
        total_revenue = completed_bookings.aggregate(
            Sum('total_price')
        )['total_price__sum'] or 0
        
        # Masters statistics
        active_masters = Master.objects.filter(
            salon_id=salon_id,
            is_approved=True
        ).count()
        
        # Services statistics
        active_services = Service.objects.filter(
            salon_id=salon_id,
            is_active=True
        ).count()
        
        # Cancellation rate
        total_count = bookings.count()
        cancellation_rate = (
            (cancelled_bookings.count() / total_count * 100)
            if total_count > 0 else 0
        )
        
        return {
            'salon_id': salon_id,
            'salon_name': salon.name,
            'period': f'Last {period_days} days',
            'total_bookings': total_count,
            'completed_bookings': completed_bookings.count(),
            'cancelled_bookings': cancelled_bookings.count(),
            'cancellation_rate': round(cancellation_rate, 2),
            'total_revenue': float(total_revenue),
            'active_masters': active_masters,
            'active_services': active_services,
            'avg_revenue_per_booking': (
                float(total_revenue / completed_bookings.count())
                if completed_bookings.count() > 0 else 0
            ),
        }
    
    @staticmethod
    def get_master_earnings(master_id, period_days=30):
        """
        Мастердің табысы
        
        Args:
            master_id: Master ID
            period_days: Қанша күн артқа қарау
            
        Returns:
            Master earnings statistics
        """
        start_date = timezone.now().date() - timedelta(days=period_days)
        
        # Get master user
        master = Master.objects.get(id=master_id)
        
        # Completed bookings
        bookings = Booking.objects.filter(
            master=master.user,
            appointment_date__gte=start_date,
            status='completed'
        )
        
        # Calculate earnings
        total_revenue = bookings.aggregate(
            Sum('total_price')
        )['total_price__sum'] or 0
        
        # Master gets 70% of revenue (это можно настроить)
        MASTER_COMMISSION = Decimal('0.70')
        master_earnings = total_revenue * MASTER_COMMISSION
        salon_commission = total_revenue * (1 - MASTER_COMMISSION)
        
        # Services breakdown
        services_stats = []
        for service in Service.objects.filter(
            salon=master.salon,
            is_active=True
        ):
            service_bookings = bookings.filter(services=service)
            service_count = service_bookings.count()
            
            if service_count > 0:
                services_stats.append({
                    'service_name': service.name,
                    'times_provided': service_count,
                    'revenue': float(service.price * service_count),
                })
        
        # Daily earnings
        daily_earnings = []
        for i in range(min(period_days, 30)):  # Last 30 days max
            date = start_date + timedelta(days=i)
            day_bookings = bookings.filter(appointment_date=date)
            day_revenue = day_bookings.aggregate(
                Sum('total_price')
            )['total_price__sum'] or 0
            day_earnings = day_revenue * MASTER_COMMISSION
            
            daily_earnings.append({
                'date': date.strftime('%Y-%m-%d'),
                'bookings': day_bookings.count(),
                'revenue': float(day_revenue),
                'earnings': float(day_earnings)
            })
        
        return {
            'master_id': master_id,
            'master_name': master.user.full_name,
            'salon': master.salon.name,
            'period': f'Last {period_days} days',
            'total_bookings': bookings.count(),
            'total_revenue': float(total_revenue),
            'master_earnings': float(master_earnings),
            'salon_commission': float(salon_commission),
            'commission_rate': f'{int(MASTER_COMMISSION * 100)}%',
            'avg_earning_per_booking': (
                float(master_earnings / bookings.count())
                if bookings.count() > 0 else 0
            ),
            'services_breakdown': services_stats,
            'daily_earnings': daily_earnings,
        }
    
    @staticmethod
    def get_dashboard_summary(user):
        """
        Пайдаланушы рольіне қарай dashboard summary
        
        Args:
            user: CustomUser instance
            
        Returns:
            Dashboard statistics based on user role
        """
        if user.is_admin:
            # Admin салондарының статистикасын көреді
            salons = Salon.objects.filter(owner=user)
            
            if not salons.exists():
                return {'message': 'No salons found'}
            
            salon_id = salons.first().id
            return AnalyticsService.get_salon_performance(salon_id)
            
        elif user.is_master:
            # Master өзінің статистикасын көреді
            try:
                master = Master.objects.get(user=user)
                return AnalyticsService.get_master_earnings(master.id)
            except Master.DoesNotExist:
                return {'message': 'Master profile not found'}
                
        elif user.is_client:
            # Client өзінің booking тарихын көреді
            bookings = Booking.objects.filter(client=user)
            
            return {
                'total_bookings': bookings.count(),
                'completed': bookings.filter(status='completed').count(),
                'upcoming': bookings.filter(
                    status__in=['pending', 'confirmed'],
                    appointment_date__gte=timezone.now().date()
                ).count(),
                'cancelled': bookings.filter(status='cancelled').count(),
                'total_spent': float(
                    bookings.filter(status='completed').aggregate(
                        Sum('total_price')
                    )['total_price__sum'] or 0
                ),
            }
        
        return {'message': 'Invalid user role'}