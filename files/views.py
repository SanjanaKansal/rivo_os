from django.db import models
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import File, STAGE_CHOICES
from .serializers import FileSerializer, FileStageUpdateSerializer


class FileViewSet(viewsets.ModelViewSet):
    """ViewSet for File model."""
    queryset = File.objects.select_related('identity').all()
    serializer_class = FileSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'patch']

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filter by stage if provided
        stage = self.request.query_params.get('stage')
        if stage:
            queryset = queryset.filter(current_stage=stage)

        # Search by name or phone
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                models.Q(name__icontains=search) | models.Q(phone__icontains=search)
            )

        return queryset

    @action(detail=False, methods=['get'])
    def stages(self, request):
        """Return available stages with counts."""
        from django.db.models import Count

        stage_counts = dict(
            File.objects.values('current_stage')
            .annotate(count=Count('id'))
            .values_list('current_stage', 'count')
        )

        stages = [
            {
                'value': value,
                'label': label,
                'count': stage_counts.get(value, 0)
            }
            for value, label in STAGE_CHOICES
        ]

        return Response({'stages': stages})

    @action(detail=True, methods=['patch'])
    def update_stage(self, request, pk=None):
        """Update file stage."""
        file = self.get_object()
        serializer = FileStageUpdateSerializer(file, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(FileSerializer(file).data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def kanban(self, request):
        """Return files grouped by stage for Kanban view."""
        files = self.get_queryset()
        serializer = FileSerializer(files, many=True)

        # Group by stage
        grouped = {value: [] for value, _ in STAGE_CHOICES}
        for file_data in serializer.data:
            stage = file_data['current_stage']
            if stage in grouped:
                grouped[stage].append(file_data)

        # Build response with stage info
        result = [
            {
                'stage': value,
                'label': label,
                'count': len(grouped[value]),
                'files': grouped[value]
            }
            for value, label in STAGE_CHOICES
        ]

        return Response({'columns': result})