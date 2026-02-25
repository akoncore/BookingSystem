# apps/services/notifications.py - ТОЛЫҚ ЖАҢАРТЫЛҒАН НҰСҚА
"""
Notification service — email + in-app хабарламалар.
Барлық send_* методтар fail_silently=True болатындай
try/except ішіне орналасқан: бір хабарлама fail болса
негізгі flow бұзылмайды.
"""

from django.core.mail import send_mail
from django.conf import settings
from logging import getLogger

logger = getLogger(__name__)


class NotificationService:
    """Хабарламалар жіберу сервисі"""

    # ─── Booking хабарламалары ───────────────────────────────────────────────

    @staticmethod
    def send_booking_created_to_client(booking):
        """Клиентке booking жасалғаны туралы email"""
        try:
            services_str = ', '.join([s.name for s in booking.services.all()])
            subject = f'✅ Booking Confirmation — {booking.booking_code}'
            message = f"""Dear {booking.client.full_name},

Your booking has been created successfully!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 Booking Code : {booking.booking_code}
 Salon        : {booking.salon.name}
 Master       : {booking.master.full_name}
 Date         : {booking.appointment_date}
 Time         : {booking.appointment_time.strftime('%H:%M')}
 Services     : {services_str}
 Total Price  : {booking.total_price:,.0f} KZT
 Status       : {booking.get_status_display()}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Notes: {booking.notes or 'N/A'}

Thank you for choosing us!

Best regards,
{booking.salon.name}
Phone: {booking.salon.phone or 'N/A'}
"""
            send_mail(
                subject=subject,
                message=message,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@salon.kz'),
                recipient_list=[booking.client.email],
                fail_silently=True,
            )
            logger.info("Booking created email → client: %s", booking.client.email)
            return True
        except Exception as e:
            logger.error("Failed to send booking-created to client: %s", e)
            return False

    @staticmethod
    def send_booking_created_to_master(booking):
        """Мастерге жаңа booking туралы email"""
        try:
            services_str = ', '.join([s.name for s in booking.services.all()])
            subject = f'📋 New Booking — {booking.booking_code}'
            message = f"""Dear {booking.master.full_name},

You have a new booking waiting for your confirmation!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 Booking Code  : {booking.booking_code}
 Client        : {booking.client.full_name}
 Client Phone  : {booking.client.phone or 'N/A'}
 Client Email  : {booking.client.email}
 Date          : {booking.appointment_date}
 Time          : {booking.appointment_time.strftime('%H:%M')}
 Services      : {services_str}
 Total Price   : {booking.total_price:,.0f} KZT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Notes: {booking.notes or 'N/A'}

⚡ Please CONFIRM or CANCEL this booking as soon as possible.

Best regards,
{booking.salon.name}
"""
            send_mail(
                subject=subject,
                message=message,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@salon.kz'),
                recipient_list=[booking.master.email],
                fail_silently=True,
            )
            logger.info("Booking created email → master: %s", booking.master.email)
            return True
        except Exception as e:
            logger.error("Failed to send booking-created to master: %s", e)
            return False

    @staticmethod
    def send_booking_confirmed(booking):
        """Booking расталғаны туралы клиентке email"""
        try:
            subject = f'🎉 Booking Confirmed — {booking.booking_code}'
            message = f"""Dear {booking.client.full_name},

Great news! Your booking has been CONFIRMED by the master.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 Booking Code : {booking.booking_code}
 Master       : {booking.master.full_name}
 Date         : {booking.appointment_date}
 Time         : {booking.appointment_time.strftime('%H:%M')}
 Location     : {booking.salon.address}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Please arrive 5 minutes before your appointment time.

See you soon! 💈

Best regards,
{booking.salon.name}
Phone: {booking.salon.phone or 'N/A'}
"""
            send_mail(
                subject=subject,
                message=message,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@salon.kz'),
                recipient_list=[booking.client.email],
                fail_silently=True,
            )
            logger.info("Booking confirmed email → client: %s", booking.client.email)
            return True
        except Exception as e:
            logger.error("Failed to send booking-confirmed: %s", e)
            return False

    @staticmethod
    def send_booking_cancelled(booking, cancelled_by='client'):
        """Booking болдырылмағаны туралы email"""
        try:
            subject = f'❌ Booking Cancelled — {booking.booking_code}'
            if cancelled_by == 'client':
                # Мастерге хабарлама
                message = f"""Dear {booking.master.full_name},

A booking has been CANCELLED by the client.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 Booking Code : {booking.booking_code}
 Client       : {booking.client.full_name}
 Date         : {booking.appointment_date}
 Time         : {booking.appointment_time.strftime('%H:%M')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

This time slot is now available for other clients.

Best regards,
{booking.salon.name}
"""
                recipient = booking.master.email
            else:
                # Клиентке хабарлама
                message = f"""Dear {booking.client.full_name},

Unfortunately, your booking has been CANCELLED.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 Booking Code : {booking.booking_code}
 Master       : {booking.master.full_name}
 Date         : {booking.appointment_date}
 Time         : {booking.appointment_time.strftime('%H:%M')}
 Reason       : {booking.notes or 'Not specified'}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Please contact us if you have any questions.

Best regards,
{booking.salon.name}
Phone: {booking.salon.phone or 'N/A'}
"""
                recipient = booking.client.email

            send_mail(
                subject=subject,
                message=message,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@salon.kz'),
                recipient_list=[recipient],
                fail_silently=True,
            )
            logger.info("Booking cancelled email → %s", recipient)
            return True
        except Exception as e:
            logger.error("Failed to send booking-cancelled: %s", e)
            return False

    @staticmethod
    def send_booking_completed(booking):
        """Booking аяқталғаны туралы клиентке email"""
        try:
            services_str = ', '.join([s.name for s in booking.services.all()])
            subject = f'✨ Service Completed — {booking.booking_code}'
            message = f"""Dear {booking.client.full_name},

Thank you for visiting us! We hope you're happy with the result. 💈

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 Booking Code : {booking.booking_code}
 Master       : {booking.master.full_name}
 Services     : {services_str}
 Total Paid   : {booking.total_price:,.0f} KZT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Looking forward to seeing you again! 🙏

Best regards,
{booking.salon.name}
"""
            send_mail(
                subject=subject,
                message=message,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@salon.kz'),
                recipient_list=[booking.client.email],
                fail_silently=True,
            )
            logger.info("Booking completed email → client: %s", booking.client.email)
            return True
        except Exception as e:
            logger.error("Failed to send booking-completed: %s", e)
            return False

    @staticmethod
    def send_booking_reminder(booking):
        """Booking-тан 24 сағат бұрын reminder"""
        try:
            services_str = ', '.join([s.name for s in booking.services.all()])
            subject = f'⏰ Reminder: Tomorrow\'s Appointment — {booking.booking_code}'
            message = f"""Dear {booking.client.full_name},

This is a friendly reminder about your appointment tomorrow!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 Time     : {booking.appointment_time.strftime('%H:%M')} (tomorrow)
 Master   : {booking.master.full_name}
 Location : {booking.salon.address}
 Services : {services_str}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Please arrive 5 minutes early.
To cancel, please do so at least 24 hours in advance.

See you soon! 💈

Best regards,
{booking.salon.name}
Phone: {booking.salon.phone or 'N/A'}
"""
            send_mail(
                subject=subject,
                message=message,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@salon.kz'),
                recipient_list=[booking.client.email],
                fail_silently=True,
            )
            logger.info("Booking reminder email → %s", booking.client.email)
            return True
        except Exception as e:
            logger.error("Failed to send booking-reminder: %s", e)
            return False

    # ─── Job Request хабарламалары ───────────────────────────────────────────

    @staticmethod
    def send_job_request_to_admin(job_request):
        """
        Жаңа job request келгенде салон Admin-іне email жіберу.
        """
        try:
            admin = job_request.salon.owner
            services_str = ', '.join(job_request.get_offered_services_list()) or 'N/A'
            subject = f'🔔 New Job Request — {job_request.master.full_name}'
            message = f"""Dear {admin.full_name},

A new master has sent a job request to your salon "{job_request.salon.name}".

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 Master Name       : {job_request.master.full_name}
 Master Email      : {job_request.master.email}
 Master Phone      : {job_request.master.phone or 'N/A'}
 Specialization    : {job_request.specialization or 'N/A'}
 Experience        : {job_request.experience_years} years
 Services Offered  : {services_str}
 Expected Salary   : {f"{job_request.expected_salary:,.0f} KZT/month" if job_request.expected_salary else 'N/A'}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Bio / Cover Letter:
{job_request.bio or 'Not provided'}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚡ Please review this request in the admin panel and APPROVE or REJECT.

Best regards,
Salon Management System
"""
            send_mail(
                subject=subject,
                message=message,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@salon.kz'),
                recipient_list=[admin.email],
                fail_silently=True,
            )
            logger.info(
                "Job request email → admin: %s (master: %s)",
                admin.email, job_request.master.email
            )
            return True
        except Exception as e:
            logger.error("Failed to send job-request to admin: %s", e)
            return False

    @staticmethod
    def send_job_request_approved(job_request):
        """Мастерге жұмысқа қабылданғаны туралы email"""
        try:
            subject = f'🎉 Job Request Approved — {job_request.salon.name}'
            message = f"""Dear {job_request.master.full_name},

Congratulations! Your job request has been APPROVED! 🎊

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 Salon       : {job_request.salon.name}
 Address     : {job_request.salon.address}
 Phone       : {job_request.salon.phone or 'N/A'}
 Reviewed by : {job_request.reviewed_by.full_name if job_request.reviewed_by else 'Admin'}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

You are now an approved master at {job_request.salon.name}.
Please set up your work schedule to start accepting bookings.

Welcome to the team! 💈

Best regards,
{job_request.salon.name}
"""
            send_mail(
                subject=subject,
                message=message,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@salon.kz'),
                recipient_list=[job_request.master.email],
                fail_silently=True,
            )
            logger.info("Job approved email → master: %s", job_request.master.email)
            return True
        except Exception as e:
            logger.error("Failed to send job-approved: %s", e)
            return False

    @staticmethod
    def send_job_request_rejected(job_request):
        """Мастерге бас тартылғаны туралы email"""
        try:
            subject = f'Job Request Update — {job_request.salon.name}'
            message = f"""Dear {job_request.master.full_name},

Thank you for your interest in {job_request.salon.name}.

After reviewing your application, we regret to inform you that
we are unable to accept your request at this time.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 Salon  : {job_request.salon.name}
 Reason : {job_request.rejection_reason or 'Not specified'}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

You are welcome to apply to other salons on our platform.

Best regards,
Salon Management System
"""
            send_mail(
                subject=subject,
                message=message,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@salon.kz'),
                recipient_list=[job_request.master.email],
                fail_silently=True,
            )
            logger.info("Job rejected email → master: %s", job_request.master.email)
            return True
        except Exception as e:
            logger.error("Failed to send job-rejected: %s", e)
            return False