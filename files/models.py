from django.db import models
from account.models import BaseModel, User
from leads.models import RawLead


STAGE_CHOICES = [
    ('LEAD_IN', 'Lead In'),
    ('QUALIFIED', 'Qualified'),
    ('PROCESSING', 'Processing'),
    ('SUBMITTED', 'Submitted'),
    ('DISBURSED', 'Disbursed'),
    ('LOST', 'Lost'),
    ('REJECTED', 'Rejected'),
]


class File(BaseModel):
    """Central entity in the mortgage pipeline"""

    raw_lead = models.OneToOneField(RawLead, on_delete=models.PROTECT, related_name='file')
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, db_index=True)
    email = models.EmailField(blank=True, null=True)
    current_stage = models.CharField(max_length=50, choices=STAGE_CHOICES, default='LEAD_IN', db_index=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.current_stage})"


class FileHistory(BaseModel):
    """Tracks stage transitions for files"""

    file = models.ForeignKey(File, on_delete=models.CASCADE, related_name='history')
    from_stage = models.CharField(max_length=50, choices=STAGE_CHOICES, blank=True, null=True)
    to_stage = models.CharField(max_length=50, choices=STAGE_CHOICES)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    note = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'File histories'
        db_table = 'files_filehistory'

    def __str__(self):
        from_display = dict(STAGE_CHOICES).get(self.from_stage, '-') if self.from_stage else '-'
        to_display = dict(STAGE_CHOICES).get(self.to_stage, self.to_stage)
        return f"{self.file.name}: {from_display} → {to_display}"


class IdentityAtom(BaseModel):
    """KYC information"""

    file = models.OneToOneField(File, on_delete=models.CASCADE, related_name='identity', primary_key=True)
    full_legal_name = models.CharField(max_length=255, blank=True)
    nationality = models.CharField(max_length=100, blank=True)
    emirates_id = models.CharField(max_length=20, blank=True)
    residency_status = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return f"Identity: {self.file.name}"

    @property
    def is_complete(self):
        return all([self.full_legal_name, self.nationality, self.residency_status, self.emirates_id])

    @property
    def completed_fields(self):
        fields = [self.full_legal_name, self.nationality, self.residency_status, self.emirates_id]
        return sum(1 for f in fields if f)

    @property
    def total_fields(self):
        return 4