from django.db import models
from django.db.models import (
    CharField,
    TextField,
    ForeignKey,
    CASCADE,
    PROTECT,
    DateTimeField,
    PositiveIntegerField,
)
from django.conf import settings
from django.core.exceptions import ValidationError
from .salon_model import Salon




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
        if self.user and not self.user.is_master:
            raise ValidationError({'user': 'User must have master role'})
