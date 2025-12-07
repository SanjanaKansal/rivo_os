from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    # Authentication
    path('login/', views.login_page, name='login'),

    # Dashboard pages
    path('', views.home, name='home'),
    path('sources/', views.sources_page, name='sources'),
    path('leads/', views.leads_page, name='leads'),
]