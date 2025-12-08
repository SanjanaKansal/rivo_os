Build a simple client pipeline view with two display modes: Ticker (list view) and Kanban (board view). Shows clients grouped by stage with basic information.
Models Provided

```python
class File(BaseModel):
    """Central entity in the mortgage pipeline"""
    
    STAGE_CHOICES = [
        ('LEAD_IN', 'Lead In'),
        ('QUALIFIED', 'Qualified'),
        ('PROCESSING', 'Processing'),
        ('SUBMITTED', 'Submitted'),
        ('DISBURSED', 'Disbursed'),
        ('LOST', 'Lost'),
        ('REJECTED', 'Rejected'),
    ]
    
    raw_lead = models.OneToOneField(RawLead, on_delete=models.PROTECT, related_name='client')
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, db_index=True)
    email = models.EmailField(blank=True, null=True)
    current_stage = models.CharField(max_length=50, choices=STAGE_CHOICES, default='LEAD_IN', db_index=True)
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='assigned_clients')

class IdentityAtom(BaseModel):
    """KYC information"""
    
    client = models.OneToOneField(Client, on_delete=models.CASCADE, related_name='identity', primary_key=True)
    full_legal_name = models.CharField(max_length=255, blank=True)
    nationality = models.CharField(max_length=100, blank=True)
    emirates_id = models.CharField(max_length=20, blank=True)
    residency_status = models.CharField(max_length=50, blank=True)
    
    @property
    def is_complete(self):
        return all([self.full_legal_name, self.nationality, self.residency_status, self.emirates_id])
```

Requirements
Backend

Single endpoint: GET /api/files/

Returns all files with basic info
Include: id, name, phone, current_stage, assigned_to (name), created_at
Include identity completion status
Order by: -created_at (newest first)



Frontend

Ticker View (default): Simple list of files with filters
Kanban View: Drag-and-drop board grouped by stage
View toggle button (switch between Ticker/Kanban)
Stage filter dropdown (show all stages or specific stage)

Ticker View Shows

File name
Phone number
Current stage (badge/chip)
Assigned to (agent name)
Created date
Identity completion indicator (e.g., "✓ Complete" or "3/4 fields")

Kanban View Shows

7 columns (one per stage)
File cards in each column showing:

Name
Phone
Assigned agent
Identity status


Column headers show count (e.g., "Lead In (5)")

Need
Backend:

Single serializer (FileSerializer with nested identity_complete)
Single viewset (FileViewSet with list endpoint)
No permissions for now (just basic auth)

Frontend:

File list page with view toggle
Ticker component (table/list)
Kanban component (board with columns)
Stage filter dropdown
Basic styling (can use Tailwind/MUI)

Nice to have (optional):

Search by name/phone
Click File card → basic detail modal
Pagination (if many Files)

