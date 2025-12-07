from django.urls import path
from . import views

app_name = 'account'

urlpatterns = [
    path('api/login/', views.login_view, name='api_login'),
    path('api/logout/', views.logout_view, name='api_logout'),
    path('api/user/', views.current_user_view, name='api_current_user'),
    path('api/lead-owners/', views.lead_owners_view, name='api_lead_owners'),
]