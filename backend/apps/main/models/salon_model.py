from django.db.models import (
    Model,
    CharField,
    ForeignKey,
    CASCADE,
    TextField,
    BooleanField,
    DateTimeField,
    Index
)
from django.conf import settings
import uuid
from django.core.exceptions import ValidationError

class Salon(Model):
    """
    Salon/Barbershop Model
    """
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
    is_active = BooleanField(
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
            Index(fields=['salon_code']),
            Index(fields=['owner', 'is_active']),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.salon_code})"

    def save(self, *args, **kwargs):
        if not self.salon_code:
            self.salon_code = f"SALON-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    def clean(self):
        if self.owner and not self.owner.is_admin:
            raise ValidationError({'owner': 'Owner must have admin role'})
