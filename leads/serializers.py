from rest_framework import serializers
from .models import Source, RawLead, SOURCE_TYPE_CHOICES
from account.serializers import UserSerializer


class SourceSerializer(serializers.ModelSerializer):
    """
    Serializer for Source model with full details.
    Includes quality score calculation, owner information, and assignment stats.
    """
    quality_score = serializers.ReadOnlyField()
    pending_leads = serializers.ReadOnlyField()
    owner_details = UserSerializer(source='owner', read_only=True)
    assignment_stats = serializers.SerializerMethodField()

    class Meta:
        model = Source
        fields = ('id', 'name', 'source_type', 'lifecycle_state', 'total_leads',
                  'valid_leads', 'spam_leads', 'pending_leads', 'quality_score', 'owner', 'owner_details',
                  'assignment_stats', 'created_at', 'updated_at')
        read_only_fields = ('total_leads', 'valid_leads', 'spam_leads', 'pending_leads', 'created_at', 'updated_at')

    def get_assignment_stats(self, obj):
        """Get assignment breakdown by user for this source."""
        from django.db.models import Count
        leads = obj.leads.values(
            'assigned_to',
            'assigned_to__first_name',
            'assigned_to__last_name',
            'assigned_to__username'
        ).annotate(count=Count('id'))

        assigned = []
        unassigned = 0
        for item in leads:
            if item['assigned_to']:
                name = f"{item['assigned_to__first_name'] or ''} {item['assigned_to__last_name'] or ''}".strip()
                if not name:
                    name = item['assigned_to__username']
                assigned.append({
                    'user_id': item['assigned_to'],
                    'name': name,
                    'count': item['count']
                })
            else:
                unassigned = item['count']

        return {
            'assigned': sorted(assigned, key=lambda x: x['count'], reverse=True),
            'unassigned': unassigned,
            'total_assigned': sum(a['count'] for a in assigned)
        }


class SourceUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating source lifecycle state and owner.
    Used for partial updates to sources.
    """

    class Meta:
        model = Source
        fields = ('lifecycle_state', 'owner')


class RawLeadSerializer(serializers.ModelSerializer):
    """
    Serializer for RawLead model with full details.
    Includes nested source, assigned user, and assigner information.
    """
    source_details = SourceSerializer(source='source', read_only=True)
    assigned_to_details = UserSerializer(source='assigned_to', read_only=True)
    assigned_by_details = UserSerializer(source='assigned_by', read_only=True)

    class Meta:
        model = RawLead
        fields = ('id', 'source', 'source_details', 'phone', 'email', 'name', 'intent',
                  'status', 'note', 'creation_time', 'assigned_to', 'assigned_to_details',
                  'assigned_by', 'assigned_by_details', 'assigned_at', 'created_at', 'updated_at')
        read_only_fields = ('creation_time', 'assigned_at', 'created_at', 'updated_at')


class RawLeadStatusSerializer(serializers.ModelSerializer):
    """
    Serializer for updating lead status and intent.
    Allows status, intent, and note field updates for lead processing.
    """

    class Meta:
        model = RawLead
        fields = ('status', 'intent', 'note')


class LeadIngestionSerializer(serializers.Serializer):
    """
    Serializer for lead ingestion endpoint.
    Handles phone validation and deduplication checks.
    Auto-creates sources if they don't exist.
    """
    source_name = serializers.CharField(max_length=255)
    source_type = serializers.ChoiceField(choices=[c[0] for c in SOURCE_TYPE_CHOICES], default='OTHER')
    phone = serializers.CharField(max_length=20)
    email = serializers.EmailField(required=False, allow_blank=True)
    name = serializers.CharField(max_length=255, required=False, allow_blank=True)
    intent = serializers.CharField(required=False, allow_blank=True)
    creation_time = serializers.DateTimeField(required=False)

    def validate_phone(self, value):
        """Validate phone format - at least 10 digits."""
        clean_phone = ''.join(filter(str.isdigit, value))
        if len(clean_phone) < 10:
            raise serializers.ValidationError('Phone number must contain at least 10 digits')
        return value

    def validate(self, data):
        """Check for phone deduplication before ingestion."""
        phone = data.get('phone')
        if phone:
            clean_phone = ''.join(filter(str.isdigit, phone))
            existing = RawLead.objects.filter(phone__icontains=clean_phone)
            if existing.exists():
                raise serializers.ValidationError({'phone': 'A lead with this phone number already exists.'})
        return data


class BulkAssignmentSerializer(serializers.Serializer):
    """
    Serializer for bulk lead assignment.
    Validates source and user existence before assignment.
    Supports assigning up to 500 leads at once.
    """
    source_id = serializers.IntegerField()
    assigned_to_id = serializers.IntegerField()
    limit = serializers.IntegerField(default=100, min_value=1, max_value=500)

    def validate_source_id(self, value):
        """Validate that source exists."""
        if not Source.objects.filter(pk=value).exists():
            raise serializers.ValidationError('Source does not exist')
        return value

    def validate_assigned_to_id(self, value):
        """Validate that user exists."""
        from account.models import User
        if not User.objects.filter(pk=value).exists():
            raise serializers.ValidationError('User does not exist')
        return value