Lead Source Management System - Code Implementation

Overview

Build a lead source management system with automatic source creation, lead validation, quality scoring, and role-based access for source assignment and lead processing.

Models Provided

```python
class Source(BaseModel):
    
    SOURCE_TYPE_CHOICES = [
        ('META_ADS', 'Facebook/Instagram Ads'),
        ('CHAT', 'AskRivo Chat'),
        ('OTHER', 'Other'),
    ]
    LIFECYCLE_CHOICES = [
        ('INCUBATION', 'Incubation - Testing'),
        ('LIVE', 'Live - Production'),
        ('QUARANTINE', 'Quarantine - Paused'),
    ]
    
    name = models.CharField(max_length=255, unique=True)
    source_type = models.CharField(max_length=50, choices=SOURCE_TYPE_CHOICES)
    lifecycle_state = models.CharField(max_length=20, choices=LIFECYCLE_CHOICES, default='INCUBATION')
    total_leads = models.IntegerField(default=0)
    valid_leads = models.IntegerField(default=0)
    spam_leads = models.IntegerField(default=0)
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='owned_sources')
    
    def __str__(self):
        return f"{self.name} ({self.lifecycle_state})"

    @property
    def quality_score(self):
        return round((self.valid_leads / self.total_leads) * 100, 2) if self.total_leads > 0 else 0

class RawLead(BaseModel):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('VALID', 'Valid'),
        ('SPAM', 'Spam'),
    ]
    source = models.ForeignKey(Source, on_delete=models.PROTECT, related_name='leads')
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)
    name = moels.CharField(max_length=255, blank=True, null=True)
    intent = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='assigned_leads')

    def __str__(self):
        return f"{self.name}"
```
Requirements
Auto Source Creation: When new lead comes with unknown source name, create source automatically

Source Management (users with source access):

View all sources + quality scores
Assign source to user (bulk assign 100 pending leads)
Update source lifecycle states
Read source metrics

Lead Processing (lead owners):

View assigned leads only
Mark lead status (PENDING → VALID/SPAM)
Update source counters when status changes

Validations:

Phone deduplication (no duplicate phone numbers)
Valid phone format
Auto-update source counters on lead status change

Need

Backend: DRF serializers, viewsets, resource level permissions, lead ingestion endpoint, bulk assignment logic
Frontend: Source dashboard, lead list, status update UI, bulk assignment interface

Provide complete working code with atomic transactions and proper error handling and ask clarifying questioning before starting.