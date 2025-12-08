from collections import defaultdict
from datetime import timedelta

from django.db import transaction
from django.db.models import Q, Count, Max, Case, When, IntegerField, OuterRef, Subquery
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny, DjangoModelPermissions
from rest_framework.response import Response

from .models import Source, RawLead, STATUS_CHOICES
from .serializers import (
    SourceSerializer, SourceUpdateSerializer, RawLeadSerializer,
    RawLeadStatusSerializer, LeadIngestionSerializer, BulkAssignmentSerializer
)

DEFAULT_STATUS = STATUS_CHOICES[0][0] if STATUS_CHOICES else 'PENDING'


def get_display_name(user):
    """Get readable display name for user object or dict."""
    if not user:
        return '-'
    if isinstance(user, dict):
        name = f"{user.get('first_name', '')} {user.get('last_name', '')}".strip()
        return name or user.get('username') or '-'
    return user.get_full_name() or user.username or user.email or str(user.id)


class SourceViewSet(viewsets.ModelViewSet):
    """ViewSet for Source management."""
    queryset = Source.objects.all()
    permission_classes = [DjangoModelPermissions]

    def get_queryset(self):
        user = self.request.user
        unassigned_subquery = RawLead.objects.filter(
            source=OuterRef('pk'), assigned_to__isnull=True
        ).values('source').annotate(cnt=Count('id')).values('cnt')

        qs = Source.objects.annotate(_unassigned_count=Subquery(unassigned_subquery))

        if user.is_staff or user.is_superuser:
            return qs
        return qs.filter(Q(owner=user) | Q(leads__assigned_to=user)).distinct()

    def get_serializer_class(self):
        if self.action in ['update', 'partial_update']:
            return SourceUpdateSerializer
        return SourceSerializer

    @action(detail=True, methods=['patch'])
    def bulk_assign(self, request, pk=None):
        """Bulk assign pending leads."""
        if not request.user.has_perm('leads.change_source'):
            raise PermissionDenied("You do not have permission to assign leads.")

        source = self.get_object()
        serializer = BulkAssignmentSerializer(data={
            'source_id': source.id,
            'assigned_to_id': request.data.get('assigned_to_id'),
            'limit': request.data.get('limit', 100)
        })

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            lead_ids = list(RawLead.objects.filter(
                source=source, status=DEFAULT_STATUS, assigned_to__isnull=True
            ).values_list('id', flat=True)[:serializer.validated_data['limit']])

            count = RawLead.objects.filter(id__in=lead_ids).update(
                assigned_to_id=serializer.validated_data['assigned_to_id'],
                assigned_by=request.user,
                assigned_at=timezone.now()
            )

        return Response({'message': f'Successfully assigned {count} leads', 'assigned_count': count})


class RawLeadViewSet(viewsets.ModelViewSet):
    """ViewSet for Lead operations."""
    queryset = RawLead.objects.all()
    serializer_class = RawLeadSerializer
    permission_classes = [DjangoModelPermissions]

    def get_queryset(self):
        user = self.request.user
        qs = RawLead.objects.select_related('source', 'assigned_to', 'assigned_by')
        if user.is_staff or user.is_superuser:
            return qs
        return qs.filter(Q(assigned_to=user) | Q(assigned_by=user))

    def get_serializer_class(self):
        if self.action in ['update', 'partial_update']:
            return RawLeadStatusSerializer
        return RawLeadSerializer

    def list(self, request, *args, **kwargs):
        group_by = request.query_params.get('group_by')
        status_filter = request.query_params.get('status')

        qs = self.get_queryset()
        if status_filter:
            qs = qs.filter(status=status_filter)

        if group_by == 'assigned_by':
            return self._grouped_response(qs)
        return super().list(request, *args, **kwargs)

    def _grouped_response(self, qs):
        """Return leads grouped by source."""
        groups = defaultdict(lambda: {
            'leads': [], 'latest_assigned_at': None,
            'latest_assigned_by': None, 'latest_assigned_by_id': None, 'latest_assigned_to': None
        })

        for lead in qs.order_by('-creation_time'):
            group = groups[lead.source.name]

            if lead.assigned_at and (group['latest_assigned_at'] is None or lead.assigned_at > group['latest_assigned_at']):
                group['latest_assigned_at'] = lead.assigned_at
                group['latest_assigned_by'] = get_display_name(lead.assigned_by)
                group['latest_assigned_by_id'] = lead.assigned_by_id
                group['latest_assigned_to'] = get_display_name(lead.assigned_to)

            group['leads'].append({
                'id': lead.id, 'name': lead.name or '-',
                'phone': lead.phone, 'intent': lead.intent or '-'
            })

        sorted_groups = sorted(groups.items(), key=lambda x: x[1]['latest_assigned_at'] or timezone.now(), reverse=True)

        return Response([{
            'source': name, 'count': len(data['leads']),
            'assigned_by': data['latest_assigned_by'] or '-',
            'assigned_by_id': data['latest_assigned_by_id'],
            'assigned_to': data['latest_assigned_to'] or '-',
            'assigned_at': data['latest_assigned_at'].isoformat() if data['latest_assigned_at'] else None,
            'leads': data['leads']
        } for name, data in sorted_groups])

    @action(detail=False, methods=['get'])
    def choices(self, request):
        """Get status choices with counts."""
        counts = dict(self.get_queryset().values('status').annotate(count=Count('id')).values_list('status', 'count'))
        statuses = [{'value': v, 'label': l, 'count': counts.get(v, 0)} for v, l in STATUS_CHOICES]
        return Response({'statuses': statuses, 'default': DEFAULT_STATUS})

    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        """Update lead status. Promotes to File when marked VALID."""
        if not request.user.has_perm('leads.change_rawlead'):
            raise PermissionDenied("You do not have permission to update lead status.")

        lead = self.get_object()
        old_status = lead.status

        serializer = RawLeadStatusSerializer(lead, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()

        # Promote to File when status changes to VALID
        new_status = serializer.validated_data.get('status')
        if new_status == 'VALID' and old_status != 'VALID':
            file = lead.promote_to_file(changed_by=request.user)
            if file:
                return Response({
                    **RawLeadSerializer(lead).data,
                    'promoted_to_file': file.id
                })

        return Response(RawLeadSerializer(lead).data)

    @action(detail=False, methods=['get'])
    def campaign_performance(self, request):
        """Get campaign performance stats grouped by source, with lead owners nested."""
        user = request.user
        time_filter = request.query_params.get('period', 'all')

        if user.is_staff or user.is_superuser:
            qs = RawLead.objects.filter(assigned_to__isnull=False)
        else:
            qs = RawLead.objects.filter(Q(source__owner=user) | Q(assigned_to=user), assigned_to__isnull=False)

        now = timezone.now()
        if time_filter == 'today':
            qs = qs.filter(assigned_at__date=now.date())
        elif time_filter == 'week':
            qs = qs.filter(assigned_at__gte=now - timedelta(days=7))

        # Get per-user stats
        user_stats = qs.values(
            'source__id', 'source__name',
            'assigned_to__id', 'assigned_to__first_name', 'assigned_to__last_name', 'assigned_to__username'
        ).annotate(
            total=Count('id'),
            pending=Count(Case(When(status='PENDING', then=1), output_field=IntegerField())),
            valid=Count(Case(When(status='VALID', then=1), output_field=IntegerField())),
            spam=Count(Case(When(status='SPAM', then=1), output_field=IntegerField())),
            last_assigned_at=Max('assigned_at')
        )

        # Group by campaign
        campaigns = {}
        for s in user_stats:
            cid = s['source__id']
            if cid not in campaigns:
                campaigns[cid] = {
                    'campaign_id': cid, 'campaign_name': s['source__name'],
                    'total': 0, 'pending': 0, 'valid': 0, 'spam': 0,
                    'last_assigned_at': None, 'lead_owners': []
                }

            c = campaigns[cid]
            valid, spam = s['valid'] or 0, s['spam'] or 0
            c['total'] += s['total']
            c['pending'] += s['pending']
            c['valid'] += valid
            c['spam'] += spam

            if s['last_assigned_at'] and (c['last_assigned_at'] is None or s['last_assigned_at'] > c['last_assigned_at']):
                c['last_assigned_at'] = s['last_assigned_at']

            owner_name = f"{s['assigned_to__first_name'] or ''} {s['assigned_to__last_name'] or ''}".strip() or s['assigned_to__username'] or '-'
            reviewed = valid + spam
            c['lead_owners'].append({
                'id': s['assigned_to__id'], 'name': owner_name,
                'total': s['total'], 'pending': s['pending'], 'valid': valid, 'spam': spam,
                'quality': round((valid / reviewed) * 100) if reviewed > 0 else 0
            })

        # Calculate campaign-level quality and format
        result = []
        for c in campaigns.values():
            reviewed = c['valid'] + c['spam']
            c['quality'] = round((c['valid'] / reviewed) * 100) if reviewed > 0 else 0
            c['last_assigned_at'] = c['last_assigned_at'].isoformat() if c['last_assigned_at'] else None
            result.append(c)

        result.sort(key=lambda x: x['last_assigned_at'] or '', reverse=True)
        return Response({'campaigns': result})


@api_view(['POST'])
@permission_classes([AllowAny])
def lead_ingestion(request):
    """Lead ingestion endpoint with auto source creation."""
    serializer = LeadIngestionSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data = serializer.validated_data

    with transaction.atomic():
        source, created = Source.objects.get_or_create(
            name=data['source_name'],
            defaults={'source_type': data.get('source_type', 'OTHER')}
        )

        lead_data = {
            'source': source, 'phone': data['phone'],
            'email': data.get('email', ''), 'name': data.get('name', ''), 'intent': data.get('intent', '')
        }
        if 'creation_time' in data:
            lead_data['creation_time'] = data['creation_time']

        lead = RawLead.objects.create(**lead_data)

    return Response({
        'message': 'Lead created successfully', 'lead_id': lead.id, 'source_created': created
    }, status=status.HTTP_201_CREATED)