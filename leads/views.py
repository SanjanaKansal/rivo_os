from django.db import transaction
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, DjangoModelPermissions

from .models import Source, RawLead
from .serializers import (
    SourceSerializer, SourceUpdateSerializer, RawLeadSerializer,
    RawLeadStatusSerializer, LeadIngestionSerializer, BulkAssignmentSerializer
)


class SourceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Source management.
    - List: View all sources with quality scores (requires view_source permission)
    - Retrieve: Get source details (requires view_source permission)
    - Update: Update source lifecycle state and owner (requires change_source permission)
    - Bulk assign: Assign pending leads to a user

    Uses Django's built-in model permissions.
    Staff/Superusers see all sources, others see only sources they own.
    """
    queryset = Source.objects.all()
    permission_classes = [DjangoModelPermissions]

    def get_queryset(self):
        """
        Filter queryset based on user:
        - Staff/Superusers can see all sources
        - All other users see sources they own OR sources with leads assigned to them
        """
        from django.db.models import Q

        user = self.request.user

        # Staff/superuser can see all
        if user.is_staff or user.is_superuser:
            return Source.objects.all()

        # All other users see sources they own OR sources with leads assigned to them
        return Source.objects.filter(
            Q(owner=user) | Q(leads__assigned_to=user)
        ).distinct()

    def get_serializer_class(self):
        if self.action in ['update', 'partial_update']:
            return SourceUpdateSerializer
        return SourceSerializer

    @action(detail=True, methods=['patch'])
    def bulk_assign(self, request, pk=None):
        """
        Bulk assign pending leads from this source to a user.
        PATCH /api/sources/{id}/bulk_assign/
        Body: {"assigned_to_id": <user_id>, "limit": 100}

        Requires change_source permission.
        """
        # Check permission manually for custom action
        if not request.user.has_perm('leads.change_source'):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You do not have permission to assign leads from this source.")

        source = self.get_object()

        serializer = BulkAssignmentSerializer(data={
            'source_id': source.id,
            'assigned_to_id': request.data.get('assigned_to_id'),
            'limit': request.data.get('limit', 100)
        })

        if serializer.is_valid():
            assigned_to_id = serializer.validated_data['assigned_to_id']
            limit = serializer.validated_data['limit']

            with transaction.atomic():
                # Get pending leads for this source
                pending_leads = RawLead.objects.filter(
                    source=source,
                    status='PENDING',
                    assigned_to__isnull=True
                ).select_for_update()[:limit]

                # Assign to user
                count = 0
                for lead in pending_leads:
                    lead.assigned_to_id = assigned_to_id
                    lead.assigned_by = request.user
                    lead.save(update_fields=['assigned_to', 'assigned_by'])
                    count += 1

            return Response({
                'message': f'Successfully assigned {count} leads',
                'assigned_count': count
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RawLeadViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Lead operations.
    - List: View assigned leads (requires view_rawlead permission)
    - Retrieve: Get lead details (requires view_rawlead permission)
    - Update: Update lead status (requires change_rawlead permission)
    - update_status: Update lead status with note (requires change_rawlead permission)

    Uses Django's built-in model permissions.
    Staff/Superusers see all leads, others see only leads assigned to/by them.
    """
    queryset = RawLead.objects.all()
    serializer_class = RawLeadSerializer
    permission_classes = [DjangoModelPermissions]

    def get_queryset(self):
        """
        Filter queryset based on user:
        - Staff/Superusers can see all leads
        - All other users can see leads assigned TO them OR assigned BY them
        """
        from django.db.models import Q

        user = self.request.user

        # Staff/superuser can see all
        if user.is_staff or user.is_superuser:
            return RawLead.objects.all()

        # All other users see leads assigned to them OR assigned by them
        return RawLead.objects.filter(Q(assigned_to=user) | Q(assigned_by=user))

    def get_serializer_class(self):
        if self.action in ['update', 'partial_update']:
            return RawLeadStatusSerializer
        return RawLeadSerializer

    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        """
        Update lead status.
        PATCH /api/leads/{id}/update_status/
        Body: {"status": "VALID" | "SPAM" | "PENDING", "note": "Optional note"}

        Requires change_rawlead permission.
        """
        # Check permission manually for custom action
        if not request.user.has_perm('leads.change_rawlead'):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You do not have permission to update lead status.")

        lead = self.get_object()
        serializer = RawLeadStatusSerializer(lead, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(RawLeadSerializer(lead).data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def lead_ingestion(request):
    """
    Lead ingestion endpoint with auto source creation.
    POST /api/leads/ingest/
    Body: {
        "source_name": "Facebook Campaign 1",
        "source_type": "META_ADS",
        "phone": "+1234567890",
        "email": "test@example.com",
        "name": "John Doe",
        "intent": "Looking for a loan"
    }
    """
    serializer = LeadIngestionSerializer(data=request.data)

    if serializer.is_valid():
        data = serializer.validated_data

        with transaction.atomic():
            # Get or create source
            source, created = Source.objects.get_or_create(
                name=data['source_name'],
                defaults={
                    'source_type': data.get('source_type', 'OTHER')
                }
            )

            # Create lead
            lead_data = {
                'source': source,
                'phone': data['phone'],
                'email': data.get('email', ''),
                'name': data.get('name', ''),
                'intent': data.get('intent', '')
            }

            # Use creation_time from payload if provided
            if 'creation_time' in data:
                lead_data['creation_time'] = data['creation_time']

            lead = RawLead.objects.create(**lead_data)

        return Response({
            'message': 'Lead created successfully',
            'lead_id': lead.id,
            'source_created': created
        }, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)