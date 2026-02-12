# apps/main/services/payment.py
"""
Payment and cancellation policy service
"""

from django.utils import timezone
from django.db import transaction
from datetime import timedelta
from decimal import Decimal
from logging import getLogger

logger = getLogger(__name__)


class CancellationPolicy:
    """
    Болдырмау саясаты
    
    Ережелер:
    - 24 сағат бұрын: Толық қайтару
    - 24 сағаттан кем: Қайтару жоқ, төлем толық алынады
    """
    
    CANCELLATION_WINDOW_HOURS = 24
    REFUND_PERCENTAGE_EARLY = Decimal('1.00')  # 100% қайтару
    REFUND_PERCENTAGE_LATE = Decimal('0.00')   # 0% қайтару
    
    @staticmethod
    def can_cancel(booking):
        """
        Booking-ты болдырмауға бола ма тексеру
        
        Args:
            booking: Booking instance
            
        Returns:
            tuple: (bool, str) - (can_cancel, reason)
        """
        # Статусты тексеру
        if booking.status not in ['pending', 'confirmed']:
            return False, f"Cannot cancel booking with status '{booking.status}'"
        
        # Өткен уақыт па тексеру
        appointment_datetime = timezone.make_aware(
            timezone.datetime.combine(
                booking.appointment_date,
                booking.appointment_time
            )
        )
        
        if appointment_datetime < timezone.now():
            return False, "Cannot cancel past appointments"
        
        # Уақыт қалды ма тексеру
        time_until_appointment = appointment_datetime - timezone.now()
        
        return True, "Can cancel"
    
    @staticmethod
    def get_refund_amount(booking):
        """
        Қайтарылатын сомманы есептеу
        
        Args:
            booking: Booking instance
            
        Returns:
            dict: Refund information
        """
        appointment_datetime = timezone.make_aware(
            timezone.datetime.combine(
                booking.appointment_date,
                booking.appointment_time
            )
        )
        
        time_until_appointment = appointment_datetime - timezone.now()
        hours_until = time_until_appointment.total_seconds() / 3600
        
        total_price = Decimal(str(booking.total_price))
        
        if hours_until >= CancellationPolicy.CANCELLATION_WINDOW_HOURS:
            # Ерте болдырмау - толық қайтару
            refund_percentage = CancellationPolicy.REFUND_PERCENTAGE_EARLY
            refund_amount = total_price * refund_percentage
            cancellation_fee = Decimal('0.00')
            policy = 'early_cancellation'
            message = f"Full refund (cancelled {int(hours_until)} hours before appointment)"
        else:
            # Кеш болдырмау - қайтару жоқ
            refund_percentage = CancellationPolicy.REFUND_PERCENTAGE_LATE
            refund_amount = Decimal('0.00')
            cancellation_fee = total_price
            policy = 'late_cancellation'
            message = (
                f"No refund (cancelled less than 24 hours before appointment). "
                f"Cancellation fee: {cancellation_fee} KZT"
            )
        
        return {
            'total_price': float(total_price),
            'hours_until_appointment': round(hours_until, 2),
            'refund_percentage': float(refund_percentage * 100),
            'refund_amount': float(refund_amount),
            'cancellation_fee': float(cancellation_fee),
            'policy': policy,
            'message': message,
        }
    
    @staticmethod
    def process_cancellation(booking, cancelled_by='client'):
        """
        Болдырмауды өңдеу
        
        Args:
            booking: Booking instance
            cancelled_by: Who cancelled ('client', 'master', 'admin')
            
        Returns:
            dict: Cancellation result
        """
        can_cancel, reason = CancellationPolicy.can_cancel(booking)
        
        if not can_cancel:
            return {
                'success': False,
                'message': reason,
            }
        
        refund_info = CancellationPolicy.get_refund_amount(booking)
        
        # Update booking status
        booking.status = 'cancelled'
        booking.notes = (
            f"{booking.notes or ''}\n\n"
            f"Cancelled by: {cancelled_by}\n"
            f"Cancelled at: {timezone.now()}\n"
            f"{refund_info['message']}"
        ).strip()
        booking.save()
        
        logger.info(
            f"Booking {booking.booking_code} cancelled by {cancelled_by}. "
            f"Refund: {refund_info['refund_amount']} KZT"
        )
        
        return {
            'success': True,
            'booking_code': booking.booking_code,
            'cancelled_by': cancelled_by,
            'refund_info': refund_info,
            'message': 'Booking cancelled successfully',
        }


class PaymentService:
    """
    Төлем сервисі және мастерлердің табысын есептеу
    """
    
    # Комиссия: Салон алатын пайыз
    SALON_COMMISSION_RATE = Decimal('0.30')  # 30% салонға
    MASTER_COMMISSION_RATE = Decimal('0.70')  # 70% мастерге
    
    @staticmethod
    def calculate_split(booking):
        """
        Booking-тан түскен табысты бөлу
        
        Args:
            booking: Booking instance
            
        Returns:
            dict: Payment split information
        """
        total_price = Decimal(str(booking.total_price))
        
        salon_amount = total_price * PaymentService.SALON_COMMISSION_RATE
        master_amount = total_price * PaymentService.MASTER_COMMISSION_RATE
        
        return {
            'booking_code': booking.booking_code,
            'total_price': float(total_price),
            'salon_commission': {
                'rate': f"{int(PaymentService.SALON_COMMISSION_RATE * 100)}%",
                'amount': float(salon_amount),
                'salon_name': booking.salon.name,
            },
            'master_commission': {
                'rate': f"{int(PaymentService.MASTER_COMMISSION_RATE * 100)}%",
                'amount': float(master_amount),
                'master_name': booking.master.full_name,
            },
        }
    
    @staticmethod
    def process_payment(booking):
        """
        Төлемді өңдеу
        
        Args:
            booking: Booking instance
            
        Returns:
            dict: Payment result
        """
        if booking.status != 'completed':
            return {
                'success': False,
                'message': 'Can only process payment for completed bookings',
            }
        
        split = PaymentService.calculate_split(booking)
        
        # TODO: Нақты төлем жүйесімен интеграция
        # (Stripe, PayPal, Kaspi, т.б.)
        
        logger.info(
            f"Payment processed for {booking.booking_code}: "
            f"Salon: {split['salon_commission']['amount']} KZT, "
            f"Master: {split['master_commission']['amount']} KZT"
        )
        
        return {
            'success': True,
            'message': 'Payment processed successfully',
            'payment_details': split,
        }
    
    @staticmethod
    def get_master_balance(master_id, period_days=30):
        """
        Мастердің балансын есептеу
        
        Args:
            master_id: Master ID
            period_days: Қанша күн артқа қарау
            
        Returns:
            dict: Master balance information
        """
        from .models import Master, Booking
        
        start_date = timezone.now().date() - timedelta(days=period_days)
        
        master = Master.objects.get(id=master_id)
        
        # Аяқталған booking-тар
        completed_bookings = Booking.objects.filter(
            master=master.user,
            appointment_date__gte=start_date,
            status='completed'
        )
        
        total_revenue = Decimal('0.00')
        master_earnings = Decimal('0.00')
        salon_earnings = Decimal('0.00')
        
        bookings_details = []
        
        for booking in completed_bookings:
            split = PaymentService.calculate_split(booking)
            
            total_revenue += Decimal(str(split['total_price']))
            master_earnings += Decimal(str(split['master_commission']['amount']))
            salon_earnings += Decimal(str(split['salon_commission']['amount']))
            
            bookings_details.append({
                'booking_code': booking.booking_code,
                'date': booking.appointment_date.strftime('%Y-%m-%d'),
                'total': split['total_price'],
                'master_share': split['master_commission']['amount'],
                'salon_share': split['salon_commission']['amount'],
            })
        
        return {
            'master_id': master_id,
            'master_name': master.user.full_name,
            'salon': master.salon.name,
            'period': f'Last {period_days} days',
            'total_bookings': completed_bookings.count(),
            'total_revenue': float(total_revenue),
            'master_earnings': float(master_earnings),
            'salon_earnings': float(salon_earnings),
            'commission_rate': f"{int(PaymentService.MASTER_COMMISSION_RATE * 100)}%",
            'bookings': bookings_details,
        }
    
    @staticmethod
    def get_salon_balance(salon_id, period_days=30):
        """
        Салонның балансын есептеу
        
        Args:
            salon_id: Salon ID
            period_days: Қанша күн артқа қарау
            
        Returns:
            dict: Salon balance information
        """
        from .models import Salon, Booking
        
        start_date = timezone.now().date() - timedelta(days=period_days)
        
        salon = Salon.objects.get(id=salon_id)
        
        # Аяқталған booking-тар
        completed_bookings = Booking.objects.filter(
            salon_id=salon_id,
            appointment_date__gte=start_date,
            status='completed'
        )
        
        total_revenue = Decimal('0.00')
        salon_earnings = Decimal('0.00')
        masters_earnings = Decimal('0.00')
        
        masters_breakdown = {}
        
        for booking in completed_bookings:
            split = PaymentService.calculate_split(booking)
            
            total_revenue += Decimal(str(split['total_price']))
            salon_earnings += Decimal(str(split['salon_commission']['amount']))
            masters_earnings += Decimal(str(split['master_commission']['amount']))
            
            # Per-master breakdown
            master_name = booking.master.full_name
            if master_name not in masters_breakdown:
                masters_breakdown[master_name] = {
                    'bookings': 0,
                    'revenue': Decimal('0.00'),
                    'master_share': Decimal('0.00'),
                }
            
            masters_breakdown[master_name]['bookings'] += 1
            masters_breakdown[master_name]['revenue'] += Decimal(str(split['total_price']))
            masters_breakdown[master_name]['master_share'] += Decimal(
                str(split['master_commission']['amount'])
            )
        
        # Format masters breakdown
        formatted_masters = []
        for master_name, data in masters_breakdown.items():
            formatted_masters.append({
                'master_name': master_name,
                'bookings': data['bookings'],
                'revenue': float(data['revenue']),
                'master_share': float(data['master_share']),
            })
        
        return {
            'salon_id': salon_id,
            'salon_name': salon.name,
            'period': f'Last {period_days} days',
            'total_bookings': completed_bookings.count(),
            'total_revenue': float(total_revenue),
            'salon_earnings': float(salon_earnings),
            'masters_earnings': float(masters_earnings),
            'commission_rate': f"{int(PaymentService.SALON_COMMISSION_RATE * 100)}%",
            'masters_breakdown': formatted_masters,
        }