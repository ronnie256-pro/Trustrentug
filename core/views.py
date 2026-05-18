from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login
from django.contrib import messages
from core.models import Property, UserProfile
from django.contrib.auth.models import User

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        role = request.POST.get('role')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            # Check profile role for manual vetting and approval restriction
            try:
                profile = user.profile
                if profile.role == 'landlord' and not profile.is_approved:
                    messages.error(request, 'Your property owner account is pending vetting and manual approval by the administrator.')
                    return redirect('login')
            except UserProfile.DoesNotExist:
                pass
                
            auth_login(request, user)
            
            # Check profile role for redirection
            is_landlord = False
            try:
                if user.profile.role == 'landlord':
                    is_landlord = True
            except UserProfile.DoesNotExist:
                pass
                
            # Redirect based on the dropdown selection, profile role, or fallback
            if user.is_superuser or user.username == 'admin' or user.username == 'trustadmin':
                return redirect('admin_dashboard')
            elif role == 'owner' or user.username == 'owner' or is_landlord:
                return redirect('landlord_dashboard')
            else:
                return redirect('search')
        else:
            messages.error(request, 'Invalid username or password.')
            return redirect('login')
            
    return render(request, 'auth/login.html')

def register_view(request):
    if request.method == 'POST':
        role = request.POST.get('role')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        username = request.POST.get('username')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        nin = request.POST.get('nin', '')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'auth/register.html')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'This username is already taken.')
            return render(request, 'auth/register.html')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'A user with this email address already exists.')
            return render(request, 'auth/register.html')

        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )

        # Create profile
        UserProfile.objects.create(
            user=user,
            role=role,
            phone=phone,
            nin=nin if role == 'landlord' else ''
        )

        messages.success(request, 'Registration successful! You can now sign in.')
        return redirect('login')

    return render(request, 'auth/register.html')

def landlord_dashboard(request):
    if not request.user.is_authenticated:
        messages.error(request, 'Please log in to access the landlord dashboard.')
        return redirect('login')
        
    # Check approval status
    is_approved = False
    try:
        if request.user.profile.role == 'landlord' and request.user.profile.is_approved:
            is_approved = True
    except UserProfile.DoesNotExist:
        pass
        
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
        'stats': stats,
        'is_approved': is_approved
    })

def admin_dashboard(request):
    if not request.user.is_authenticated or not request.user.is_superuser:
        messages.error(request, 'Access denied. Only system administrators can access this page.')
        return redirect('login')
        
    tab = request.GET.get('tab', 'overview')
    
    # Fetch parent properties (Single-Unit or Buildings)
    properties = Property.objects.filter(parent=None).prefetch_related('units')
    
    # Fetch all registered landlords with their profile details
    landlords = User.objects.filter(profile__role='landlord').select_related('profile')
    
    stats = {
        'total_properties': Property.objects.count(),
        'pending': Property.objects.filter(status='pending_verification').count(),
        'available': Property.objects.filter(status='available').count(),
        'rented': Property.objects.filter(status='rented').count(),
    }
    
    return render(request, 'admin/dashboard.html', {
        'properties': properties,
        'stats': stats,
        'landlords': landlords,
        'current_tab': tab
    })

def approve_landlord(request, user_id):
    if not request.user.is_authenticated or not request.user.is_superuser:
        messages.error(request, 'Access denied. Only system administrators can perform this action.')
        return redirect('login')
        
    if request.method == 'POST':
        try:
            landlord_user = User.objects.get(id=user_id)
            profile = landlord_user.profile
            if profile.role == 'landlord':
                profile.is_approved = True
                profile.save()
                messages.success(request, f"Property owner account for {landlord_user.first_name} {landlord_user.last_name} has been successfully approved!")
            else:
                messages.error(request, "Selected user is not registered as a property owner.")
        except User.DoesNotExist:
            messages.error(request, "Landlord account not found.")
            
    return redirect('/admin-dashboard/?tab=landlords')

def add_property(request):
    if not request.user.is_authenticated:
        messages.error(request, 'Please log in to add a property.')
        return redirect('login')
        
    # Block unapproved landlords from adding new properties
    try:
        profile = request.user.profile
        if profile.role == 'landlord' and not profile.is_approved:
            messages.warning(request, 'Your account is currently pending manual vetting. You cannot list properties until approved.')
            return redirect('landlord_dashboard')
    except UserProfile.DoesNotExist:
        messages.error(request, 'Profile not found.')
        return redirect('login')
        
    buildings = Property.objects.filter(is_multi_unit=True)
    return render(request, 'landlord/add_property.html', {'buildings': buildings})
