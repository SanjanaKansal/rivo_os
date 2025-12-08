from rest_framework import serializers
from .models import Source, RawLead, SOURCE_TYPE_CHOICES


class SourceSerializer(serializers.ModelSerializer):
    """Serializer for Source model with assignment stats."""
    quality_score = serializers.ReadOnlyField()
    pending_leads = serializers.ReadOnlyField()
    assignment_stats = serializers.SerializerMethodField()

    class Meta:
        model = Source
        fields = ('id', 'name', 'source_type', 'lifecycle_state', 'total_leads',
                  'valid_leads', 'spam_leads', 'pending_leads', 'quality_score',
                  'assignment_stats', 'created_at', 'updated_at')
        read_only_fields = ('total_leads', 'valid_leads', 'spam_leads', 'pending_leads', 'created_at', 'updated_at')

    def get_assignment_stats(self, obj):
        if hasattr(obj, '_unassigned_count'):
            unassigned = obj._unassigned_count or 0
            return {'unassigned': unassigned, 'total_assigned': obj.total_leads - unassigned}
        from django.db.models import Count, Q
        stats = obj.leads.aggregate(unassigned=Count('id', filter=Q(assigned_to__isnull=True)))
        unassigned = stats['unassigned'] or 0
        return {'unassigned': unassigned, 'total_assigned': obj.total_leads - unassigned}


class SourceUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating source lifecycle state and owner."""
    class Meta:
        model = Source
        fields = ('lifecycle_state', 'owner')


class RawLeadSerializer(serializers.ModelSerializer):
    """Serializer for RawLead."""
    source_details = serializers.SerializerMethodField()

    class Meta:
        model = RawLead
        fields = ('id', 'source', 'source_details', 'phone', 'email', 'name', 'intent',
                  'status', 'note', 'creation_time', 'assigned_to', 'assigned_by',
                  'assigned_at', 'created_at', 'updated_at')
        read_only_fields = ('creation_time', 'assigned_at', 'created_at', 'updated_at')

    def get_source_details(self, obj):
        return {'id': obj.source_id, 'name': obj.source.name} if obj.source else None


class RawLeadStatusSerializer(serializers.ModelSerializer):
    """Serializer for updating lead status."""
    class Meta:
        model = RawLead
        fields = ('status', 'intent', 'note')


class LeadIngestionSerializer(serializers.Serializer):
    """Serializer for lead ingestion endpoint."""
    source_name = serializers.CharField(max_length=255)
    source_type = serializers.ChoiceField(choices=[c[0] for c in SOURCE_TYPE_CHOICES], default='OTHER')
    phone = serializers.CharField(max_length=20)
    email = serializers.EmailField(required=False, allow_blank=True)
    name = serializers.CharField(max_length=255, required=False, allow_blank=True)
    intent = serializers.CharField(required=False, allow_blank=True)
    creation_time = serializers.DateTimeField(required=False)

    def validate_phone(self, value):
        clean_phone = ''.join(filter(str.isdigit, value))
        if len(clean_phone) < 10:
            raise serializers.ValidationError('Phone number must contain at least 10 digits')
        return value

    def validate(self, data):
        phone = data.get('phone')
        if phone:
            clean_phone = ''.join(filter(str.isdigit, phone))
            if RawLead.objects.filter(phone__icontains=clean_phone).exists():
                raise serializers.ValidationError({'phone': 'A lead with this phone number already exists.'})
        return data


class BulkAssignmentSerializer(serializers.Serializer):
    """Serializer for bulk lead assignment."""
    source_id = serializers.IntegerField()
    assigned_to_id = serializers.IntegerField()
    limit = serializers.IntegerField(default=100, min_value=1, max_value=500)

    def validate_source_id(self, value):
        if not Source.objects.filter(pk=value).exists():
            raise serializers.ValidationError('Source does not exist')
        return value

    def validate_assigned_to_id(self, value):
        from account.models import User
        if not User.objects.filter(pk=value).exists():
            raise serializers.ValidationError('User does not exist')
        return value