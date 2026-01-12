from django.db import models
from django.db.models import (
    CharField,
    TextField,
    ForeignKey,
    ManyToManyField,
    CASCADE,
    PROTECT,
    FloatField,
    DurationField,
    DateField,
    TimeField,
    DateTimeField,
    PositiveIntegerField,
)
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone
import uuid


class Salon(models.Model):
    """Salon/Barbershop Model"""
    
    name = CharField(
        max_length=255,
        verbose_name="Salon Name",
        help_text="Name of the barbershop/salon"
    )
    
    address = CharField(
        max_length=500,
        verbose_name="Address",
        help_text="Full address of the salon"
    )
    
    salon_code = CharField(
        max_length=100,
        unique=True,
        editable=False,
        verbose_name="Salon Code",
        help_text="Unique code for the salon",
    )
    
    owner = ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=CASCADE,
        related_name='owned_salons',
        limit_choices_to={'role': 'admin'},
        verbose_name="Owner",
        help_text="Admin who owns this salon"
    )
    
    phone = CharField(
        max_length=20,
        verbose_name="Contact Phone",
        help_text="Salon contact phone number",
        blank=True,
        null=True
    )
    
    description = TextField(
        verbose_name="Description",
        help_text="Description about the salon",
        blank=True,
        null=True
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name="Is Active",
        help_text="Is salon currently active"
    )
    
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Salon"
        verbose_name_plural = "Salons"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['salon_code']),
            models.Index(fields=['owner', 'is_active']),
        ]
    
    def __str__(self) -> str:
        return f"{self.name} ({self.salon_code})"
    
    def save(self, *args, **kwargs):
        """Generate unique salon code if not exists"""
        if not self.salon_code:
            self.salon_code = f"SALON-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)
    
    def clean(self):
        """Validate that owner has admin role"""
        if self.owner and not self.owner.is_admin:
            raise ValidationError({
                'owner': 'Owner must have admin role'
            })


class Master(models.Model):
    """Master (Barber) Profile Model"""
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=CASCADE,
        related_name='master_profile',
        limit_choices_to={'role': 'master'},
        verbose_name="User"
    )
    
    salon = ForeignKey(
        Salon,
        on_delete=CASCADE,
        related_name='masters',
        verbose_name="Salon",
        help_text="Salon where master works"
    )
    
    specialization = CharField(
        max_length=255,
        verbose_name="Specialization",
        help_text="Master's specialization (e.g., Hair stylist, Beard specialist)",
        blank=True,
        null=True
    )
    
    experience_years = PositiveIntegerField(
        verbose_name="Years of Experience",
        help_text="How many years of experience",
        default=0
    )
    
    bio = TextField(
        verbose_name="Biography",
        help_text="Short bio about the master",
        blank=True,
        null=True
    )
    
    is_approved = models.BooleanField(
        default=False,
        verbose_name="Is Approved",
        help_text="Admin approval status"
    )
    
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Master"
        verbose_name_plural = "Masters"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['salon', 'is_approved']),
        ]
    
    def __str__(self) -> str:
        return f"{self.user.full_name} - {self.salon.name}"
    
    def clean(self):
        """Validate that user has master role"""
        if self.user and not self.user.is_master:
            raise ValidationError({
                'user': 'User must have master role'
            })


class Service(models.Model):
    """Service Model"""
    
    name = CharField(
        max_length=255,
        verbose_name="Service Name",
        help_text="Name of the service (e.g., Haircut, Shave)"
    )
    
    description = TextField(
        verbose_name="Description",
        help_text="Service description",
        blank=True,
        null=True
    )
    
    price = FloatField(
        verbose_name="Price",
        help_text="Service price in KZT"
    )
    
    duration = DurationField(
        verbose_name="Duration",
        help_text="Service duration (e.g., 30 minutes, 1 hour)"
    )
    
    salon = ForeignKey(
        Salon,
        on_delete=CASCADE,
        related_name='services',
        verbose_name="Salon"
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name="Is Active"
    )
    
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Service"
        verbose_name_plural = "Services"
        ordering = ['salon', 'name']
        indexes = [
            models.Index(fields=['salon', 'is_active']),
        ]
    
    def __str__(self) -> str:
        return f"{self.name} - {self.price} KZT ({self.salon.name})"


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
        return f"{self.booking_code}: {self.client.full_name} → {self.master.full_name} ({self.appointment_date} {self.appointment_time})"
    
    def save(self, *args, **kwargs):
        """Generate unique booking code"""
        if not self.booking_code:
            self.booking_code = f"BK-{uuid.uuid4().hex[:10].upper()}"
        super().save(*args, **kwargs)
    
    def clean(self):
        """Validate booking"""
        errors = {}
        
        # Check if client has client role
        if self.client and not self.client.is_client:
            errors['client'] = 'Selected user must be a client'
        
        # Check if master has master role
        if self.master and not self.master.is_master:
            errors['master'] = 'Selected user must be a master'
        
        # Check if appointment is in the past
        if self.appointment_date and self.appointment_time:
            appointment_datetime = timezone.make_aware(
                timezone.datetime.combine(self.appointment_date, self.appointment_time)
            )
            if appointment_datetime < timezone.now():
                errors['appointment_date'] = 'Cannot book appointments in the past'
        
        if errors:
            raise ValidationError(errors)
    
    def calculate_total_price(self):
        """Calculate total price from selected services"""
        if self.pk:  # Only if booking exists (has been saved)
            total = sum(service.price for service in self.services.all())
            self.total_price = total
            return total
        return 0.0


class WorkSchedule(models.Model):
    """Work Schedule for Masters"""
    
    WEEKDAYS = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]
    
    master = ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=CASCADE,
        related_name='work_schedules',
        limit_choices_to={'role': 'master'},
        verbose_name="Master"
    )
    
    weekday = models.IntegerField(
        choices=WEEKDAYS,
        verbose_name="Weekday"
    )
    
    start_time = TimeField(
        verbose_name="Start Time"
    )
    
    end_time = TimeField(
        verbose_name="End Time"
    )
    
    is_working = models.BooleanField(
        default=True,
        verbose_name="Is Working",
        help_text="Is master working on this day"
    )
    
    class Meta:
        verbose_name = "Work Schedule"
        verbose_name_plural = "Work Schedules"
        unique_together = ['master', 'weekday']
        ordering = ['master', 'weekday']
    
    def __str__(self) -> str:
        return f"{self.master.full_name} - {self.get_weekday_display()}: {self.start_time}-{self.end_time}"
    
    def clean(self):
        """Validate that end_time is after start_time"""
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError({
                'end_time': 'End time must be after start time'
            })