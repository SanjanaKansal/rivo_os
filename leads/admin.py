from django.contrib import admin
from .models import Source, RawLead


@admin.register(Source)
class SourceAdmin(admin.ModelAdmin):
    """Admin interface for Source model."""
    list_display = ('name', 'source_type', 'lifecycle_state', 'total_leads', 'valid_leads', 'spam_leads', 'quality_score', 'owner', 'created_at')
    list_filter = ('source_type', 'lifecycle_state', 'created_at')
    search_fields = ('name',)
    readonly_fields = ('total_leads', 'valid_leads', 'spam_leads', 'created_at', 'updated_at')

    def quality_score(self, obj):
        """Display quality score as percentage."""
        return f"{obj.quality_score}%"
    quality_score.short_description = 'Quality Score'


@admin.register(RawLead)
class RawLeadAdmin(admin.ModelAdmin):
    """Admin interface for RawLead model."""
    list_display = ('name', 'phone', 'email', 'source', 'status', 'assigned_to', 'created_at')
    list_filter = ('status', 'source', 'assigned_to', 'created_at')
    search_fields = ('name', 'phone', 'email')
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ('source', 'assigned_to')