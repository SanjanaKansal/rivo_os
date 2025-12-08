from django.shortcuts import render
from django.contrib.auth.decorators import login_required, permission_required


def login_page(request):
    """Login page view."""
    return render(request, 'dashboard/login.html')


@login_required(login_url='/login/')
def home(request):
    """Home/dashboard page view."""
    return render(request, 'dashboard/home.html')


@login_required(login_url='/login/')
@permission_required('leads.view_source', login_url='/', raise_exception=False)
def sources_page(request):
    """Source management page view."""
    return render(request, 'dashboard/sources.html')


@login_required(login_url='/login/')
@permission_required('leads.view_rawlead', login_url='/', raise_exception=False)
def leads_page(request):
    """My leads page view."""
    return render(request, 'dashboard/leads.html')


@login_required(login_url='/login/')
@permission_required('leads.view_source', login_url='/', raise_exception=False)
def campaigns_page(request):
    """Campaign performance page view for RM."""
    return render(request, 'dashboard/campaigns.html')


@login_required(login_url='/login/')
@permission_required('files.view_file', login_url='/', raise_exception=False)
def pipeline_page(request):
    """Pipeline view for files/clients."""
    return render(request, 'dashboard/pipeline.html')
