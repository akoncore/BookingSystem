# apps/main/services/notifications.py
"""
Notification service for email and SMS
"""

from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from logging import getLogger

logger = getLogger(__name__)


class NotificationService:
    """Хабарламалар жіберу сервисі"""
    
    @staticmethod
    def send_booking_created_to_client(booking):
        """
        Клиентке booking жасалғаны туралы email жіберу
        """
        try:
            subject = f'Booking Confirmation - {booking.booking_code}'
            
            message = f"""
            Dear {booking.client.full_name},
            
            Your booking has been created successfully!
            
            Booking Details:
            ─────────────────────────────────────
            Booking Code: {booking.booking_code}
            Salon: {booking.salon.name}
            Master: {booking.master.full_name}
            Date: {booking.appointment_date}
            Time: {booking.appointment_time}
            Services: {', '.join([s.name for s in booking.services.all()])}
            Total Price: {booking.total_price} KZT
            Status: {booking.get_status_display()}
            
            Notes: {booking.notes or 'N/A'}
            
            Thank you for choosing us!
            
            Best regards,
            {booking.salon.name}
            Phone: {booking.salon.phone}
            """
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[booking.client.email],
                fail_silently=False,
            )
            
            logger.info(f"Booking created email sent to {booking.client.email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send booking email: {e}")
            return False
    
    @staticmethod
    def send_booking_created_to_master(booking):
        """
        Мастерге жаңа booking туралы email жіберу
        """
        try:
            subject = f'New Booking - {booking.booking_code}'
            
            message = f"""
            Dear {booking.master.full_name},
            
            You have a new booking!
            
            Booking Details:
            ─────────────────────────────────────
            Booking Code: {booking.booking_code}
            Client: {booking.client.full_name}
            Client Phone: {booking.client.phone or 'N/A'}
            Date: {booking.appointment_date}
            Time: {booking.appointment_time}
            Services: {', '.join([s.name for s in booking.services.all()])}
            Total Price: {booking.total_price} KZT
            
            Notes: {booking.notes or 'N/A'}
            
            Please confirm or cancel this booking.
            
            Best regards,
            {booking.salon.name}
            """
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[booking.master.email],
                fail_silently=False,
            )
            
            logger.info(f"New booking email sent to master {booking.master.email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send master notification: {e}")
            return False
    
    @staticmethod
    def send_booking_confirmed(booking):
        """
        Booking расталғаны туралы клиентке email жіберу
        """
        try:
            subject = f'Booking Confirmed - {booking.booking_code}'
            
            message = f"""
            Dear {booking.client.full_name},
            
            Great news! Your booking has been CONFIRMED by the master.
            
            Booking Details:
            ─────────────────────────────────────
            Booking Code: {booking.booking_code}
            Master: {booking.master.full_name}
            Date: {booking.appointment_date}
            Time: {booking.appointment_time}
            Location: {booking.salon.address}
            
            Please arrive 5 minutes before your appointment time.
            
            See you soon!
            
            Best regards,
            {booking.salon.name}
            Phone: {booking.salon.phone}
            """
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[booking.client.email],
                fail_silently=False,
            )
            
            logger.info(f"Booking confirmed email sent to {booking.client.email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send confirmation email: {e}")
            return False
    
    @staticmethod
    def send_booking_cancelled(booking, cancelled_by='client'):
        """
        Booking болдырылмағаны туралы email жіберу
        """
        try:
            subject = f'Booking Cancelled - {booking.booking_code}'
            
            if cancelled_by == 'client':
                # Мастерге хабарлама
                message = f"""
                Dear {booking.master.full_name},
                
                A booking has been cancelled by the client.
                
                Booking Details:
                ─────────────────────────────────────
                Booking Code: {booking.booking_code}
                Client: {booking.client.full_name}
                Date: {booking.appointment_date}
                Time: {booking.appointment_time}
                
                This time slot is now available.
                
                Best regards,
                {booking.salon.name}
                """
                recipient = booking.master.email
            else:
                # Клиентке хабарлама
                message = f"""
                Dear {booking.client.full_name},
                
                Unfortunately, your booking has been cancelled.
                
                Booking Details:
                ─────────────────────────────────────
                Booking Code: {booking.booking_code}
                Master: {booking.master.full_name}
                Date: {booking.appointment_date}
                Time: {booking.appointment_time}
                
                Reason: {booking.notes or 'Not specified'}
                
                Please contact us if you have any questions.
                
                Best regards,
                {booking.salon.name}
                Phone: {booking.salon.phone}
                """
                recipient = booking.client.email
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient],
                fail_silently=False,
            )
            
            logger.info(f"Cancellation email sent to {recipient}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send cancellation email: {e}")
            return False
    
    @staticmethod
    def send_booking_completed(booking):
        """
        Booking аяқталғаны туралы клиентке email жіберу
        """
        try:
            subject = f'Service Completed - {booking.booking_code}'
            
            message = f"""
            Dear {booking.client.full_name},
            
            Thank you for visiting us!
            
            Service Summary:
            ─────────────────────────────────────
            Booking Code: {booking.booking_code}
            Master: {booking.master.full_name}
            Services: {', '.join([s.name for s in booking.services.all()])}
            Total Paid: {booking.total_price} KZT
            
            We hope you enjoyed our service!
            
            Looking forward to seeing you again.
            
            Best regards,
            {booking.salon.name}
            """
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[booking.client.email],
                fail_silently=False,
            )
            
            logger.info(f"Completion email sent to {booking.client.email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send completion email: {e}")
            return False
    
    @staticmethod
    def send_booking_reminder(booking):
        """
        Booking-тан 24 сағат бұрын клиентке reminder жіберу
        """
        try:
            subject = f'Reminder: Upcoming Appointment - {booking.booking_code}'
            
            message = f"""
            Dear {booking.client.full_name},
            
            This is a reminder about your upcoming appointment.
            
            Appointment Details:
            ─────────────────────────────────────
            Tomorrow at {booking.appointment_time}
            Master: {booking.master.full_name}
            Location: {booking.salon.address}
            Services: {', '.join([s.name for s in booking.services.all()])}
            
            Please arrive 5 minutes early.
            
            If you need to cancel, please do so at least 24 hours in advance.
            
            See you soon!
            
            Best regards,
            {booking.salon.name}
            Phone: {booking.salon.phone}
            """
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[booking.client.email],
                fail_silently=False,
            )
            
            logger.info(f"Reminder email sent to {booking.client.email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send reminder email: {e}")
            return False


# SMS хабарламалары үшін (болашақта қосуға болады)
class SMSService:
    """SMS хабарламалары жіберу сервисі"""
    
    @staticmethod
    def send_booking_confirmation(booking):
        """
        SMS арқылы booking расталғаны туралы хабарлама
        
        TODO: SMS provider интеграциясы (Twilio, Vonage, т.б.)
        """
        try:
            phone = booking.client.phone
            if not phone:
                logger.warning(f"No phone number for client {booking.client.id}")
                return False
            
            message = (
                f"Booking confirmed!\n"
                f"Code: {booking.booking_code}\n"
                f"Date: {booking.appointment_date}\n"
                f"Time: {booking.appointment_time}\n"
                f"Master: {booking.master.full_name}\n"
                f"{booking.salon.name}"
            )
            
            # TODO: SMS provider API call
            logger.info(f"SMS would be sent to {phone}: {message}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send SMS: {e}")
            return False