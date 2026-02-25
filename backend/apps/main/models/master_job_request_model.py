from django.db import models
from django.db.models import (
    CharField,
    TextField,
    ForeignKey,
    CASCADE,
    FloatField,
    DateTimeField,
    PositiveIntegerField,
    JSONField,
)
from django.conf import settings
from models.salon_model import Salon


class MasterJobRequest(models.Model):
    """
    Master → Salon жұмыс сұрауы (резюмемен)
    """

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    master = ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=CASCADE,
        related_name='job_requests',
        limit_choices_to={'role': 'master'},
        verbose_name="Master"
    )
    salon = ForeignKey(
        Salon,
        on_delete=CASCADE,
        related_name='job_requests',
        verbose_name="Salon"
    )

    # --- Кәсіби ақпарат ---
    specialization = CharField(
        max_length=255,
        verbose_name="Specialization",
        blank=True,
        null=True
    )
    experience_years = PositiveIntegerField(
        default=0,
        verbose_name="Years of Experience"
    )
    bio = TextField(
        verbose_name="Bio / Cover Letter",
        blank=True,
        null=True,
        help_text="Шағын биография немесе жұмыс орнына хат"
    )

    # --- Жасай алатын қызметтер ---
    offered_services = TextField(
        verbose_name="Services Can Provide",
        blank=True,
        null=True,
        help_text="Comma-separated service names (e.g., Haircut, Beard Trim, Coloring)"
    )

    # --- Күтілетін жалақы ---
    expected_salary = FloatField(
        verbose_name="Expected Monthly Salary (KZT)",
        blank=True,
        null=True
    )

    # --- Қосымша сұрақтарға жауап (JSON) ---
    answers = JSONField(
        verbose_name="Salon Q&A Answers",
        default=dict,
        blank=True,
        help_text="Salon-specific questions and master's answers"
    )

    # --- Күй ---
    status = CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="Status"
    )
    rejection_reason = TextField(
        verbose_name="Rejection Reason",
        blank=True,
        null=True
    )

    # --- Уақыт ---
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
    reviewed_at = DateTimeField(
        verbose_name="Reviewed At",
        blank=True,
        null=True
    )
    reviewed_by = ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_requests',
        verbose_name="Reviewed By"
    )

    class Meta:
        verbose_name = "Job Request"
        verbose_name_plural = "Job Requests"
        ordering = ['-created_at']
        # Бір мастер бір салонға бір рет ғана жіберуі тиіс
        unique_together = [('master', 'salon')]
        indexes = [
            models.Index(fields=['salon', 'status']),
            models.Index(fields=['master', 'status']),
        ]

    def __str__(self) -> str:
        return f"{self.master.full_name} → {self.salon.name} [{self.status}]"

    def get_offered_services_list(self):
        """Қызметтер тізімін list ретінде қайтару"""
        if self.offered_services:
            return [s.strip() for s in self.offered_services.split(',') if s.strip()]
        return []
