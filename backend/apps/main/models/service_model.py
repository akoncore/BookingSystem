from django.db import models
from django.db.models import (
    CharField,
    TextField,
    ForeignKey,
    CASCADE,
    FloatField,
    DurationField,
    DateTimeField,
    BooleanField,
)
from django.conf import settings
from models.salon_model import Salon


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
    is_active = BooleanField(
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

