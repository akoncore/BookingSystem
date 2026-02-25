from django.db import models
from django.db.models import (
    ForeignKey,
    CASCADE,
    TimeField,
)
from django.conf import settings
from django.core.exceptions import ValidationError


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
    weekday = models.IntegerField(choices=WEEKDAYS, verbose_name="Weekday")
    start_time = TimeField(verbose_name="Start Time")
    end_time = TimeField(verbose_name="End Time")
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
        return (
            f"{self.master.full_name} - "
            f"{self.get_weekday_display()}: {self.start_time}-{self.end_time}"
        )

    def clean(self):
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError({'end_time': 'End time must be after start time'})