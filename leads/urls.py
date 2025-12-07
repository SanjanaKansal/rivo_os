from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'leads'

# API router
router = DefaultRouter()
router.register(r'sources', views.SourceViewSet, basename='source')
router.register(r'leads', views.RawLeadViewSet, basename='rawlead')

urlpatterns = [
    # API endpoints only - all frontend is in dashboard app
    path('api/', include(router.urls)),
    path('api/ingest/', views.lead_ingestion, name='lead_ingestion'),
]