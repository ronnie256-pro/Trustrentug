from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login
from django.contrib import messages
from core.models import Property

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        role = request.POST.get('role')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            # Redirect based on the dropdown selection or fallback to username
            if user.is_superuser or user.username == 'admin':
                return redirect('admin_dashboard')
            elif role == 'owner' or user.username == 'owner':
                return redirect('landlord_dashboard')
            else:
                return redirect('search')
        else:
            messages.error(request, 'Invalid username or password.')
            return redirect('login')
            
    return render(request, 'auth/login.html')

def landlord_dashboard(request):
    # Fetch properties belonging to the logged-in owner
    owner_properties = Property.objects.filter(owner=request.user, parent=None).prefetch_related('units')
    
    stats = {
        'total': Property.objects.filter(owner=request.user).count(),
        'available': Property.objects.filter(owner=request.user, status='available').count(),
        'pending': Property.objects.filter(owner=request.user, status='pending_verification').count(),
        # For simplicity, calculating total potential revenue
        'revenue': sum(p.price for p in Property.objects.filter(owner=request.user, price__isnull=False))
    }
    
    return render(request, 'landlord/dashboard.html', {
        'properties': owner_properties,
        'stats': stats
    })

def admin_dashboard(request):
    # Fetch parent properties (Single-Unit or Buildings)
    properties = Property.objects.filter(parent=None).prefetch_related('units')
    
    stats = {
        'total_properties': Property.objects.count(),
        'pending': Property.objects.filter(status='pending_verification').count(),
        'available': Property.objects.filter(status='available').count(),
        'rented': Property.objects.filter(status='rented').count(),
    }
    
    return render(request, 'admin/dashboard.html', {
        'properties': properties,
        'stats': stats
    })

def add_property(request):
    buildings = Property.objects.filter(is_multi_unit=True)
    return render(request, 'landlord/add_property.html', {'buildings': buildings})
