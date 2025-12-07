from django.db import models
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from account.models import BaseModel, User


# Choices
SOURCE_TYPE_CHOICES = [
    ('META_ADS', 'Facebook Ads'),
    ('INSTA_ADS', 'Instagram Ads'),
    ('WHATSAPP_ADS', 'WhatsApp Ads'),
    ('CHAT', 'AskRivo Chat'),
    ('PARTNER_HUB', 'Partner Hub'),
    ('OTHER', 'Other'),
]

LIFECYCLE_CHOICES = [
    ('INCUBATION', 'Incubation - Testing'),
    ('LIVE', 'Live - Production'),
    ('QUARANTINE', 'Quarantine - Paused'),
]

STATUS_CHOICES = [
    ('PENDING', 'Pending'),
    ('VALID', 'Valid'),
    ('SPAM', 'Spam'),
]


# Phone validator - at least 10 digits
phone_validator = RegexValidator(
    regex=r'^\+?\d{10,}$',
    message='Phone number must contain at least 10 digits',
    code='invalid_phone'
)


class Source(BaseModel):
    """
    Source model for tracking lead sources with quality metrics.
    Automatically manages lead counters and calculates quality scores.
    """
    name = models.CharField(max_length=255, unique=True)
    source_type = models.CharField(max_length=50, choices=SOURCE_TYPE_CHOICES)
    lifecycle_state = models.CharField(max_length=20, choices=LIFECYCLE_CHOICES, default='INCUBATION')
    total_leads = models.IntegerField(default=0)
    valid_leads = models.IntegerField(default=0)
    spam_leads = models.IntegerField(default=0)
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='owned_sources')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.lifecycle_state})"

    @property
    def pending_leads(self):
        """Calculate pending leads (total - valid - spam)."""
        return max(0, self.total_leads - self.valid_leads - self.spam_leads)

    @property
    def quality_score(self):
        """Calculate quality score as percentage of valid leads."""
        if self.total_leads > 0:
            return round((self.valid_leads / self.total_leads) * 100, 2)
        return 0


class RawLead(BaseModel):
    """
    RawLead model for managing incoming leads.
    Handles phone deduplication, status tracking, and automatic source counter updates.
    """
    source = models.ForeignKey(Source, on_delete=models.PROTECT, related_name='leads')
    phone = models.CharField(max_length=20, validators=[phone_validator])
    email = models.EmailField(blank=True, null=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    intent = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    note = models.TextField(blank=True, null=True, help_text='Note added when marking lead as valid/spam')
    creation_time = models.DateTimeField(default=timezone.now)
    # Assignment fields
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_leads')
    assigned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='leads_assigned_by_me')
    assigned_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['phone']),
            models.Index(fields=['status']),
            models.Index(fields=['assigned_to']),
        ]

    def __str__(self):
        return f"{self.name or self.phone}"

    def clean(self):
        """Validate phone number uniqueness before saving."""
        if self.phone:
            # Remove all non-digit characters for comparison
            clean_phone = ''.join(filter(str.isdigit, self.phone))

            existing = RawLead.objects.filter(phone__icontains=clean_phone)
            if self.pk:
                existing = existing.exclude(pk=self.pk)

            if existing.exists():
                raise ValidationError({'phone': 'A lead with this phone number already exists.'})

    def save(self, *args, **kwargs):
        """Save lead and update source counters if status changed."""
        # Validate before saving
        self.full_clean()

        # Track status changes
        old_status = None
        if self.pk:
            try:
                old_status = RawLead.objects.get(pk=self.pk).status
            except RawLead.DoesNotExist:
                pass

        super().save(*args, **kwargs)

        # Update source counters if status changed
        if old_status != self.status:
            self.update_source_counters(old_status, self.status)

    def update_source_counters(self, old_status, new_status):
        """Update source counters when lead status changes."""
        from django.db import transaction

        with transaction.atomic():
            source = Source.objects.select_for_update().get(pk=self.source_id)

            # Decrement old status counter
            if old_status == 'VALID':
                source.valid_leads = max(0, source.valid_leads - 1)
            elif old_status == 'SPAM':
                source.spam_leads = max(0, source.spam_leads - 1)

            # Increment new status counter
            if new_status == 'VALID':
                source.valid_leads += 1
            elif new_status == 'SPAM':
                source.spam_leads += 1

            # Update total leads (only count new leads, not status changes)
            if old_status is None:
                source.total_leads += 1

            source.save()