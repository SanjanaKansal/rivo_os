from rest_framework import serializers
from .models import File, IdentityAtom, STAGE_CHOICES


class IdentitySerializer(serializers.ModelSerializer):
    """Serializer for IdentityAtom model."""
    is_complete = serializers.ReadOnlyField()
    completed_fields = serializers.ReadOnlyField()
    total_fields = serializers.ReadOnlyField()

    class Meta:
        model = IdentityAtom
        fields = ('full_legal_name', 'nationality', 'emirates_id', 'residency_status',
                  'is_complete', 'completed_fields', 'total_fields')


class FileSerializer(serializers.ModelSerializer):
    """Serializer for File model with identity status."""
    identity_status = serializers.SerializerMethodField()
    stage_display = serializers.SerializerMethodField()

    class Meta:
        model = File
        fields = ('id', 'name', 'phone', 'email', 'current_stage', 'stage_display',
                  'identity_status', 'created_at')
        read_only_fields = ('created_at',)

    def get_identity_status(self, obj):
        try:
            identity = obj.identity
            return {
                'is_complete': identity.is_complete,
                'completed_fields': identity.completed_fields,
                'total_fields': identity.total_fields
            }
        except IdentityAtom.DoesNotExist:
            return {
                'is_complete': False,
                'completed_fields': 0,
                'total_fields': 4
            }

    def get_stage_display(self, obj):
        return dict(STAGE_CHOICES).get(obj.current_stage, obj.current_stage)


class FileStageUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating file stage."""
    class Meta:
        model = File
        fields = ('current_stage',)