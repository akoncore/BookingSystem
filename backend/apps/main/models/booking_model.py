from django.db import models
from django.db.models import (
    CharField,
    TextField,
    ForeignKey,
    ManyToManyField,
    CASCADE,
    PROTECT,
    FloatField,
    DateField,
    TimeField,
    DateTimeField,
)
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone
import uuid
from models.salon_model import Salon
from models.service_model import Service


class Booking(models.Model):
    """Booking/Appointment Model"""

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    booking_code = CharField(
        max_length=100,
        unique=True,
        editable=False,
        verbose_name="Booking Code"
    )
    client = ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=CASCADE,
        related_name='client_bookings',
        limit_choices_to={'role': 'client'},
        verbose_name="Client"
    )
    master = ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=PROTECT,
        related_name='master_appointments',
        limit_choices_to={'role': 'master'},
        verbose_name="Master"
    )
    salon = ForeignKey(
        Salon,
        on_delete=CASCADE,
        related_name='bookings',
        verbose_name="Salon"
    )
    services = ManyToManyField(
        Service,
        related_name='bookings',
        verbose_name="Services",
        help_text="Selected services for this booking"
    )
    appointment_date = DateField(
        verbose_name="Appointment Date",
        help_text="Date of appointment"
    )
    appointment_time = TimeField(
        verbose_name="Appointment Time",
        help_text="Time of appointment"
    )
    status = CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="Status"
    )
    total_price = FloatField(
        verbose_name="Total Price",
        help_text="Total price of all services",
        default=0.0
    )
    notes = TextField(
        verbose_name="Notes",
        help_text="Additional notes or comments",
        blank=True,
        null=True
    )
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Booking"
        verbose_name_plural = "Bookings"
        ordering = ['-appointment_date', '-appointment_time']
        indexes = [
            models.Index(fields=['client', 'status']),
            models.Index(fields=['master', 'appointment_date']),
            models.Index(fields=['salon', 'appointment_date', 'status']),
        ]

    def __str__(self) -> str:
        return (
            f"{self.booking_code}: {self.client.full_name} → "
            f"{self.master.full_name} ({self.appointment_date} {self.appointment_time})"
        )

    def save(self, *args, **kwargs):
        if not self.booking_code:
            self.booking_code = f"BK-{uuid.uuid4().hex[:10].upper()}"
        super().save(*args, **kwargs)

    def clean(self):
        errors = {}
        if self.client and not self.client.is_client:
            errors['client'] = 'Selected user must be a client'
        if self.master and not self.master.is_master:
            errors['master'] = 'Selected user must be a master'
        if self.appointment_date and self.appointment_time:
            appointment_datetime = timezone.make_aware(
                timezone.datetime.combine(self.appointment_date, self.appointment_time)
            )
            if appointment_datetime < timezone.now():
                errors['appointment_date'] = 'Cannot book appointments in the past'
        if errors:
            raise ValidationError(errors)

    def calculate_total_price(self):
        if self.pk:
            total = sum(service.price for service in self.services.all())
            self.total_price = total
            return total
        return 0.0
