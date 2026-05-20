from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login
from django.contrib import messages
from django.db.models import Q
from core.models import Property, UserProfile, AgentRole, InspectionAgent, Inspection, InspectionReport, PropertyAmenity, ProximityCategory, ProximityItem
from django.contrib.auth.models import User

AMENITY_ICONS = {
    # Core Details
    'bedrooms': 'fa-bed',
    'bathrooms': 'fa-bath',
    'rent': 'fa-money-bill-wave',
    'location': 'fa-location-dot',
    'parking': 'fa-car',
    'water': 'fa-droplet',
    'power': 'fa-bolt',

    # Luxury / Optional
    'swimming pool': 'fa-water',
    'gym': 'fa-dumbbell',
    'sauna': 'fa-spa',
    'rooftop': 'fa-building',
    'smart home': 'fa-house-laptop',
    'solar backup': 'fa-solar-panel',

    # Indoor Comfort & Amenities
    'sitting room': 'fa-couch',
    'dining area': 'fa-utensils',
    'kitchen': 'fa-kitchen-set',
    'pantry': 'fa-box-archive',
    'laundry area': 'fa-soap',
    'balcony': 'fa-door-open',
    'walk-in closet': 'fa-shirt',
    'furnished / unfurnished': 'fa-chair',
    'air conditioning': 'fa-wind',
    'ceiling fans': 'fa-fan',
    'water heater': 'fa-fire-burner',
    'dstv connection': 'fa-tv',
    'wi-fi / internet ready': 'fa-wifi',
    'smart tv': 'fa-tv',
    'built-in wardrobes': 'fa-door-closed',
    'tiled floors': 'fa-border-all',
    'gypsum ceiling': 'fa-window-maximize',
    'modern finishing': 'fa-star',

    # Utilities & Infrastructure
    'power supply': 'fa-plug',
    'backup generator': 'fa-bolt-lightning',
    'solar power': 'fa-solar-panel',
    'water supply': 'fa-faucet',
    'water tank capacity': 'fa-bucket',
    'borehole access': 'fa-arrow-down-long',
    'garbage collection': 'fa-trash-can',
    'sewage system': 'fa-water-ladder',
    'internet connectivity': 'fa-wifi',
    'cctv surveillance': 'fa-video',
    'intercom system': 'fa-phone-volume',

    # Security Features
    'security guards': 'fa-user-shield',
    'perimeter wall': 'fa-border-outer',
    'electric fence': 'fa-bolt-lightning',
    'cctv cameras': 'fa-video',
    'biometric access': 'fa-fingerprint',
    'gated community': 'fa-door-closed',
    'smart locks': 'fa-key',
    'security alarm system': 'fa-bell',
    'fire extinguishers': 'fa-fire-extinguisher',
    'emergency exit': 'fa-person-running',

    # Outdoor Amenities
    'private swimming pool': 'fa-swimming-pool',
    'shared swimming pool': 'fa-water',
    'dedicated parking spots': 'fa-square-p',
    'visitor parking': 'fa-car-side',
    'garden / compound': 'fa-seedling',
    'children’s play area': 'fa-gamepad',
    'rooftop terrace': 'fa-umbrella-beach',
    'outdoor kitchen': 'fa-fire',
    'bbq area': 'fa-fire-burner',
    'paved compound': 'fa-road',
    'car wash area': 'fa-spray-can-sparkles',

    # Building Features
    'elevator / lift': 'fa-arrows-up-down',
    'staircase access': 'fa-stairs',
    'wheelchair accessibility': 'fa-wheelchair',
    'reception area': 'fa-bell-concierge',
    'gym / fitness center': 'fa-dumbbell',
    'sauna / steam room': 'fa-spa',
    'conference room': 'fa-users-rectangle',
    'common lounge': 'fa-couch',
    'mini supermarket': 'fa-basket-shopping',
    'pharmacy access': 'fa-prescription-bottle-medical',

    # Proximities
    'hospital': 'fa-hospital',
    'clinic': 'fa-house-chimney-medical',
    'pharmacy': 'fa-prescription-bottle-medical',
    'medical center': 'fa-house-medical',
    'market': 'fa-shop',
    'supermarket': 'fa-cart-shopping',
    'shopping mall': 'fa-bag-shopping',
    'convenience store': 'fa-store',
    'hardware shop': 'fa-hammer',
    'main road': 'fa-road',
    'taxi stage': 'fa-van-shuttle',
    'bus terminal': 'fa-bus',
    'boda stage': 'fa-motorcycle',
    'airport': 'fa-plane',
    'restaurant': 'fa-bowl-food',
    'café': 'fa-mug-hot',
    'bar / lounge': 'fa-martini-glass-citrus',
    'cinema': 'fa-film',
    'sports center': 'fa-circle-play',
    'church': 'fa-church',
    'mosque': 'fa-mosque',
    'temple': 'fa-synagogue',
}


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
    
    # Handle form submissions for agents & roles
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add_role':
            role_name = request.POST.get('role_name', '').strip()
            role_description = request.POST.get('role_description', '').strip()
            if role_name:
                try:
                    AgentRole.objects.create(name=role_name, description=role_description)
                    messages.success(request, f"Inspection agent role '{role_name}' has been created successfully!")
                except Exception as e:
                    messages.error(request, f"Error creating role: Role with this name may already exist.")
            else:
                messages.error(request, "Role name cannot be empty.")
            return redirect('/admin-dashboard/?tab=agents')
            
        elif action == 'add_agent':
            agent_name = request.POST.get('agent_name', '').strip()
            agent_email = request.POST.get('agent_email', '').strip()
            agent_phone = request.POST.get('agent_phone', '').strip()
            agent_id_input = request.POST.get('agent_id', '').strip()
            agent_role_id = request.POST.get('agent_role_id')
            agent_image = request.FILES.get('agent_image')
            
            if agent_name and agent_email and agent_phone:
                try:
                    role_obj = None
                    if agent_role_id:
                        role_obj = AgentRole.objects.get(id=agent_role_id)
                    
                    # Validate custom agent ID format (numeric) if provided
                    if agent_id_input and not agent_id_input.isdigit():
                        messages.error(request, "Custom Agent ID must be numeric only.")
                        return redirect('/admin-dashboard/?tab=agents')
                        
                    InspectionAgent.objects.create(
                        name=agent_name,
                        email=agent_email,
                        phone=agent_phone,
                        role=role_obj,
                        image=agent_image,
                        agent_id=agent_id_input if agent_id_input else None
                    )
                    messages.success(request, f"Inspection Agent '{agent_name}' has been registered successfully!")
                except Exception as e:
                    messages.error(request, f"Error registering agent: An agent with this email or ID might already exist.")
            else:
                messages.error(request, "Name, Email, and Phone number are required to register an agent.")
            return redirect('/admin-dashboard/?tab=agents')

        elif action == 'add_amenity':
            name = request.POST.get('name', '').strip()
            category = request.POST.get('category', '').strip()
            layer = request.POST.get('layer', 'luxury')
            if name and category:
                try:
                    PropertyAmenity.objects.get_or_create(name=name, defaults={'category': category, 'layer': layer})
                    messages.success(request, f"Property Amenity '{name}' has been added successfully!")
                except Exception as e:
                    messages.error(request, "Error adding amenity.")
            else:
                messages.error(request, "Name and Category are required.")
            return redirect('/admin-dashboard/?tab=settings')

        elif action == 'toggle_amenity':
            amenity_id = request.POST.get('amenity_id')
            try:
                amenity = PropertyAmenity.objects.get(id=amenity_id)
                amenity.is_active = not amenity.is_active
                amenity.save()
                messages.success(request, f"Amenity '{amenity.name}' active status has been updated!")
            except Exception as e:
                messages.error(request, "Error toggling amenity.")
            return redirect('/admin-dashboard/?tab=settings')

        elif action == 'delete_amenity':
            amenity_id = request.POST.get('amenity_id')
            try:
                amenity = PropertyAmenity.objects.get(id=amenity_id)
                name = amenity.name
                amenity.delete()
                messages.success(request, f"Amenity '{name}' deleted successfully!")
            except Exception as e:
                messages.error(request, "Error deleting amenity.")
            return redirect('/admin-dashboard/?tab=settings')

        elif action == 'add_proximity_category':
            name = request.POST.get('name', '').strip()
            if name:
                try:
                    ProximityCategory.objects.get_or_create(name=name)
                    messages.success(request, f"Proximity Category '{name}' created successfully!")
                except Exception as e:
                    messages.error(request, "Error creating proximity category.")
            else:
                messages.error(request, "Category name cannot be empty.")
            return redirect('/admin-dashboard/?tab=settings')

        elif action == 'add_proximity_item':
            category_id = request.POST.get('category_id')
            name = request.POST.get('name', '').strip()
            if name and category_id:
                try:
                    category = ProximityCategory.objects.get(id=category_id)
                    ProximityItem.objects.get_or_create(category=category, name=name)
                    messages.success(request, f"Proximity service item '{name}' added successfully to category '{category.name}'!")
                except Exception as e:
                    messages.error(request, "Error adding proximity service item.")
            else:
                messages.error(request, "Name and Category are required.")
            return redirect('/admin-dashboard/?tab=settings')

        elif action == 'delete_proximity_item':
            item_id = request.POST.get('item_id')
            try:
                item = ProximityItem.objects.get(id=item_id)
                name = item.name
                item.delete()
                messages.success(request, f"Proximity item '{name}' deleted successfully!")
            except Exception as e:
                messages.error(request, "Error deleting proximity item.")
            return redirect('/admin-dashboard/?tab=settings')

    # Fetch properties based on active tab
    if tab == 'properties':
        properties = Property.objects.all().select_related('owner', 'parent').order_by('-created_at')
    else:
        properties = Property.objects.filter(parent=None).prefetch_related('units').order_by('-created_at')
    
    # Fetch all registered landlords with their profile details
    landlords = User.objects.filter(profile__role='landlord').select_related('profile')
    
    # Fetch agents and roles
    agents = InspectionAgent.objects.all().select_related('role').order_by('-joined_at')
    agent_roles = AgentRole.objects.all().order_by('name')
    inspections = Inspection.objects.all().select_related('property').prefetch_related('reports', 'reports__agent', 'reports__agent__role').order_by('-created_at')
    
    amenities = list(PropertyAmenity.objects.all().order_by('layer', 'category', 'name'))
    for a in amenities:
        key = a.name.strip().lower()
        a.icon_class = AMENITY_ICONS.get(key, 'fa-circle-check')

    proximity_categories = list(ProximityCategory.objects.prefetch_related('items').all().order_by('name'))
    for cat in proximity_categories:
        for item in cat.items.all():
            key = item.name.strip().lower()
            item.icon_class = AMENITY_ICONS.get(key, 'fa-location-dot')

    amenity_categories = [
        {'id': 'indoor', 'name': 'Indoor Comfort', 'icon': 'fa-couch'},
        {'id': 'utilities', 'name': 'Utilities & Infrastructure', 'icon': 'fa-plug'},
        {'id': 'security', 'name': 'Security Features', 'icon': 'fa-shield-halved'},
        {'id': 'outdoor', 'name': 'Outdoor & Paving', 'icon': 'fa-tree'},
        {'id': 'building', 'name': 'Building & Gym', 'icon': 'fa-building'},
    ]

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
        'agents': agents,
        'agent_roles': agent_roles,
        'inspections': inspections,
        'amenities': amenities,
        'proximity_categories': proximity_categories,
        'amenity_categories': amenity_categories,
        'current_tab': tab
    })

def delete_agent(request, agent_id):
    if not request.user.is_authenticated or not request.user.is_superuser:
        messages.error(request, 'Access denied. Only system administrators can perform this action.')
        return redirect('login')
        
    if request.method == 'POST':
        try:
            agent = InspectionAgent.objects.get(id=agent_id)
            name = agent.name
            agent.delete()
            messages.success(request, f"Inspection Agent '{name}' has been permanently deleted.")
        except InspectionAgent.DoesNotExist:
            messages.error(request, "Agent not found.")
            
    return redirect('/admin-dashboard/?tab=agents')

def delete_agent_role(request, role_id):
    if not request.user.is_authenticated or not request.user.is_superuser:
        messages.error(request, 'Access denied. Only system administrators can perform this action.')
        return redirect('login')
        
    if request.method == 'POST':
        try:
            role = AgentRole.objects.get(id=role_id)
            name = role.name
            role.delete()
            messages.success(request, f"Agent Role '{name}' has been permanently deleted.")
        except AgentRole.DoesNotExist:
            messages.error(request, "Role not found.")
            
    return redirect('/admin-dashboard/?tab=agents')

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
        
    if request.method == 'POST':
        title = request.POST.get('property_name')
        category = request.POST.get('category')
        parent_id = request.POST.get('parent_property')
        neighborhood = request.POST.get('neighborhood', '')
        address = request.POST.get('address', '')
        
        # Concatenate neighborhood and address to populate location field
        location = f"{neighborhood.capitalize()}, {address}" if neighborhood else address
        
        # Determine structure class
        is_multi_unit = category in ['apartment_block', 'condo_block', 'flat']
        
        parent = None
        if parent_id:
            try:
                parent = Property.objects.get(id=parent_id)
            except Property.DoesNotExist:
                pass
                
        # Create property listing
        price_per_month = request.POST.get('price_per_month')
        price_per_year = request.POST.get('price_per_year')
        bedrooms_count = request.POST.get('bedrooms_count')
        
        property_obj = Property(
            owner=request.user,
            title=title,
            category=category,
            parent=parent,
            location=location,
            is_multi_unit=is_multi_unit,
            bedrooms=int(bedrooms_count) if (bedrooms_count and bedrooms_count.isdigit()) else None,
            status='pending_verification',  # Marked as pending until admin manually verifies files and approves
            description="Luxury property submitted through the TRUST security protocol.",
            price_per_month=price_per_month if price_per_month else None,
            price_per_year=price_per_year if price_per_year else None,
            price=price_per_month if price_per_month else None
        )
        
        # Handle Images
        if 'hero_image' in request.FILES:
            property_obj.hero_image = request.FILES['hero_image']
        if 'image_1' in request.FILES:
            property_obj.image_1 = request.FILES['image_1']
        if 'image_2' in request.FILES:
            property_obj.image_2 = request.FILES['image_2']
        if 'image_3' in request.FILES:
            property_obj.image_3 = request.FILES['image_3']
            
        # Handle Documents
        if 'building_plans' in request.FILES:
            property_obj.building_plans = request.FILES['building_plans']
        if 'occupancy_permit' in request.FILES:
            property_obj.occupancy_permit = request.FILES['occupancy_permit']
        if 'lc1_letter' in request.FILES:
            property_obj.lc1_letter = request.FILES['lc1_letter']
        if 'tenancy_agreement' in request.FILES:
            property_obj.tenancy_agreement = request.FILES['tenancy_agreement']
        if 'security_agreement' in request.FILES:
            property_obj.security_agreement = request.FILES['security_agreement']
            
        property_obj.save()

        # Handle selected amenities
        amenity_ids = request.POST.getlist('selected_amenities')
        if amenity_ids:
            property_obj.amenities.set(amenity_ids)

        # Handle selected proximity items and their custom distances
        from core.models import ProximityItem, PropertyProximity
        for key, value in request.POST.items():
            if key.startswith('proximity_item_'):
                item_id = key.split('_')[-1]
                distance_val = request.POST.get(f'proximity_distance_{item_id}', '').strip()
                if distance_val:
                    try:
                        item_obj = ProximityItem.objects.get(id=item_id)
                        PropertyProximity.objects.create(
                            property=property_obj,
                            item=item_obj,
                            distance_km=distance_val
                        )
                    except Exception:
                        pass

        messages.success(request, f"Property '{title}' was submitted successfully and is now pending manual security vetting by the TRUST board!")
        return redirect('landlord_dashboard')
        
    buildings = Property.objects.filter(is_multi_unit=True)
    amenities = list(PropertyAmenity.objects.all().order_by('layer', 'category', 'name'))
    for a in amenities:
        key = a.name.strip().lower()
        a.icon_class = AMENITY_ICONS.get(key, 'fa-circle-check')
        
    proximity_categories = list(ProximityCategory.objects.prefetch_related('items').all().order_by('name'))
    for cat in proximity_categories:
        for item in cat.items.all():
            key = item.name.strip().lower()
            item.icon_class = AMENITY_ICONS.get(key, 'fa-location-dot')

    amenity_categories = [
        {'id': 'indoor', 'name': 'Indoor Comfort', 'icon': 'fa-couch'},
        {'id': 'utilities', 'name': 'Utilities & Infrastructure', 'icon': 'fa-plug'},
        {'id': 'security', 'name': 'Security Features', 'icon': 'fa-shield-halved'},
        {'id': 'outdoor', 'name': 'Outdoor & Paving', 'icon': 'fa-tree'},
        {'id': 'building', 'name': 'Building & Gym', 'icon': 'fa-building'},
    ]

    return render(request, 'landlord/add_property.html', {
        'buildings': buildings,
        'amenities': amenities,
        'proximity_categories': proximity_categories,
        'amenity_categories': amenity_categories,
    })

def approve_property(request, property_id):
    if not request.user.is_authenticated or not request.user.is_superuser:
        messages.error(request, 'Access denied. Only system administrators can perform this action.')
        return redirect('login')
        
    if request.method == 'POST':
        try:
            property_obj = Property.objects.get(id=property_id)
            property_obj.status = 'available'
            property_obj.save()
            messages.success(request, f"Property '{property_obj.title}' has been successfully approved and is now live on TRUST!")
        except Property.DoesNotExist:
            messages.error(request, "Property not found.")
            
    return redirect('/admin-dashboard/?tab=properties')

def delete_property(request, property_id):
    if not request.user.is_authenticated:
        messages.error(request, 'Please log in to perform this action.')
        return redirect('login')
        
    try:
        property_obj = Property.objects.get(id=property_id)
        
        # Security check: User must be either the owner of the property OR a superuser/admin
        is_admin = request.user.is_superuser
        is_owner = property_obj.owner == request.user
        
        if not (is_admin or is_owner):
            messages.error(request, 'Access denied. You do not have permission to delete this property.')
            return redirect('home')
            
        if request.method == 'POST':
            title = property_obj.title
            property_obj.delete()
            messages.success(request, f"Property '{title}' has been successfully deleted.")
            
            # Redirect based on user role
            if is_admin:
                return redirect('/admin-dashboard/?tab=properties')
            else:
                return redirect('landlord_dashboard')
                
    except Property.DoesNotExist:
        messages.error(request, 'Property not found.')
        
def admin_property_detail(request, property_id):
    if not request.user.is_authenticated or not request.user.is_superuser:
        messages.error(request, 'Access denied. Only system administrators can access this page.')
        return redirect('login')
        
    try:
        property_obj = Property.objects.select_related('owner', 'parent').get(id=property_id)
        # Fetch any inspection reports associated with this property
        inspection = Inspection.objects.filter(property=property_obj).first()
        reports = []
        if inspection:
            reports = inspection.reports.all().select_related('agent', 'agent__role')
            
        # Fetch dynamic amenities
        property_amenities = list(property_obj.amenities.all())
        for a in property_amenities:
            key = a.name.strip().lower()
            a.icon_class = AMENITY_ICONS.get(key, 'fa-circle-check')

        # Fetch dynamic proximity items with custom distances
        property_proximities = list(property_obj.proximities.all().select_related('item', 'item__category'))
        for px in property_proximities:
            key = px.item.name.strip().lower()
            px.icon_class = AMENITY_ICONS.get(key, 'fa-location-dot')

        return render(request, 'admin/property_detail.html', {
            'property': property_obj,
            'inspection': inspection,
            'reports': reports,
            'property_amenities': property_amenities,
            'property_proximities': property_proximities,
        })
    except Property.DoesNotExist:
        messages.error(request, 'Property not found.')
        return redirect('/admin-dashboard/?tab=properties')

def submit_property_inspection(request, property_id):
    if not request.user.is_authenticated or not request.user.is_superuser:
        messages.error(request, 'Access denied. Only system administrators can perform this action.')
        return redirect('login')
        
    if request.method == 'POST':
        try:
            property_obj = Property.objects.get(id=property_id)
            property_obj.status = 'under_inspection'
            property_obj.save()
            
            # Create inspection record
            inspection, created = Inspection.objects.get_or_create(property=property_obj, defaults={'status': 'in_progress'})
            
            # If reports do not exist, pre-populate beautiful, rich safety & title mock reports!
            if not inspection.reports.exists():
                roles_data = [
                    ("Structural Engineering Inspector", "Vets structural soundness, foundation, load limits, and building plan compliance."),
                    ("Legal Title Vetting Counsel", "Reviews land registry title details, identity documents, and LC1 residency clearance letters."),
                    ("Fire & Safety Officer", "Vets fire escapes, CCTV security coverage, occupancy safety and hazard compliance.")
                ]
                
                agents_data = [
                    ("Eng. Samuel Ssewankambo", "samuel@trustrentug.com", "+256 772 456789", "Structural Engineering Inspector",
                     f"Foundation and concrete core integrity evaluated for '{property_obj.title}'. Verified that the column reinforcements align with the approved structural drawings. Fire-resistant material coatings are compliant with building standards. No structural spalling or load-bearing distress identified. Pass."),
                     
                    ("Counsel Martha Namubiru", "martha@trustrentug.com", "+256 701 987654", "Legal Title Vetting Counsel",
                     f"Title deed search completed at the Ministry of Lands, Housing and Urban Development. The land registry confirms undisputed, clean ownership under the landlord's profile credentials. LC1 verification letter from local council authorities verified as authentic. Pass."),
                     
                    ("Inspector Chief Ronald Okello", "ronald@trustrentug.com", "+256 752 112233", "Fire & Safety Officer",
                     f"Physical security audit executed. Dual fire exit pathways are completely clear of obstructions. First-tier fire extinguishers and smoke detectors installed correctly on each floor level. Verified that CCTV surveillance cameras properly cover all external parking zones. Pass.")
                ]
                
                for role_name, desc in roles_data:
                    AgentRole.objects.get_or_create(name=role_name, defaults={'description': desc})
                    
                for name, email, phone, r_name, findings_txt in agents_data:
                    role_obj = AgentRole.objects.get(name=r_name)
                    agent_obj, _ = InspectionAgent.objects.get_or_create(
                        email=email,
                        defaults={
                            'name': name,
                            'phone': phone,
                            'role': role_obj
                        }
                    )
                    InspectionReport.objects.create(
                        inspection=inspection,
                        agent=agent_obj,
                        findings=findings_txt,
                        status='approved'
                    )
            
            messages.success(request, f"Property '{property_obj.title}' has been successfully submitted for physical safety and legal title inspection!")
        except Property.DoesNotExist:
            messages.error(request, 'Property not found.')
            
    return redirect(f'/admin-dashboard/property/view/{property_id}/')

def home_view(request):
    # Fetch parent (standalone or building) properties that are approved/available, newest first
    properties = Property.objects.filter(parent=None, status='available').prefetch_related('units').order_by('-created_at')
    return render(request, 'index.html', {'properties': properties})

def search_view(request):
    # Only show available properties that are parent listings or individual standalone properties
    properties = Property.objects.filter(status='available', parent=None)
    
    # 1. Location search
    q = request.GET.get('q', '').strip()
    if q:
        properties = properties.filter(Q(location__icontains=q) | Q(title__icontains=q))
        
    # 2. Type search
    p_type = request.GET.get('type', '').strip().lower()
    if p_type and p_type != 'all types':
        if p_type == 'apartment':
            properties = properties.filter(category__in=['studio', '1_bed', '2_bed', '3_plus_bed', 'apartment_block', 'flat'])
        elif p_type == 'villa':
            properties = properties.filter(category__in=['bungalow', 'standalone'])
        elif p_type == 'condo':
            properties = properties.filter(category__in=['condo_block'])
            
    # 3. Price filters (min_price, max_price)
    min_price = request.GET.get('min_price', '').strip()
    if min_price and min_price.isdigit():
        properties = properties.filter(price__gte=int(min_price))
        
    max_price = request.GET.get('max_price', '').strip()
    if max_price and max_price.isdigit():
        properties = properties.filter(price__lte=int(max_price))
        
    # 4. Amenities filters
    selected_amenities = []
    if request.GET.get('pool') == 'on':
        properties = properties.filter(amenities__name__icontains='pool')
        selected_amenities.append('pool')
    if request.GET.get('power') == 'on':
        properties = properties.filter(Q(amenities__name__icontains='power') | Q(amenities__name__icontains='generator'))
        selected_amenities.append('power')
    if request.GET.get('gym') == 'on':
        properties = properties.filter(amenities__name__icontains='gym')
        selected_amenities.append('gym')
    if request.GET.get('security') == 'on':
        properties = properties.filter(Q(amenities__name__icontains='security') | Q(amenities__name__icontains='guard') | Q(amenities__name__icontains='cctv'))
        selected_amenities.append('security')
        
    properties = properties.distinct().order_by('-created_at')
    total_count = properties.count()
    
    return render(request, 'tenant/search.html', {
        'properties': properties,
        'total_count': total_count,
        'q': q,
        'type': p_type,
        'min_price': min_price,
        'max_price': max_price,
        'selected_amenities': selected_amenities
    })

def property_detail_view(request, property_id):
    property_obj = get_object_or_404(Property, id=property_id)
    
    # Fetch dynamic amenities
    property_amenities = list(property_obj.amenities.all())
    for a in property_amenities:
        key = a.name.strip().lower()
        a.icon_class = AMENITY_ICONS.get(key, 'fa-circle-check')
        
    # Fetch dynamic proximity items with custom distances
    property_proximities = list(property_obj.proximities.all().select_related('item', 'item__category'))
    for px in property_proximities:
        key = px.item.name.strip().lower()
        px.icon_class = AMENITY_ICONS.get(key, 'fa-location-dot')
        
    # Get first inspection (reports)
    inspection = Inspection.objects.filter(property=property_obj).first()
    reports = []
    if inspection:
        reports = inspection.reports.all().select_related('agent', 'agent__role')
        
    return render(request, 'tenant/property_detail.html', {
        'property': property_obj,
        'property_amenities': property_amenities,
        'property_proximities': property_proximities,
        'inspection': inspection,
        'reports': reports,
    })

def checkout_view(request, property_id):
    property_obj = get_object_or_404(Property, id=property_id)
    
    # Pre-calculate prices
    price = property_obj.price or 0
    security_deposit = price * 0.1
    pipeline_fee = price * 0.01
    total_escrow = price + security_deposit + pipeline_fee
    
    # Make pretty currency formats
    def format_ugx(val):
        if val >= 1000000:
            return f"UGX {val/1000000:.2f}M".replace('.00M', 'M')
        elif val >= 1000:
            return f"UGX {val/1000:.0f}K"
        return f"UGX {val:.0f}"
        
    context = {
        'property': property_obj,
        'price_formatted': format_ugx(price),
        'security_deposit_formatted': format_ugx(security_deposit),
        'pipeline_fee_formatted': format_ugx(pipeline_fee),
        'total_escrow_formatted': format_ugx(total_escrow)
    }
    return render(request, 'tenant/checkout.html', context)

def agent_report_auth(request):
    if request.method == 'POST':
        agent_id = request.POST.get('agent_id', '').strip()
        phone = request.POST.get('phone', '').strip()
        email = request.POST.get('email', '').strip()
        
        agent = InspectionAgent.objects.filter(agent_id__iexact=agent_id).select_related('role').first()
        
        if agent:
            # Flexible case-insensitive email match
            email_matches = agent.email.strip().lower() == email.lower()
            
            # Flexible phone matching that ignores spaces, country code formats, etc.
            def clean_phone(p_str):
                return "".join(c for c in p_str if c.isdigit())
            
            input_phone_clean = clean_phone(phone)
            db_phone_clean = clean_phone(agent.phone)
            
            phone_matches = False
            if input_phone_clean and db_phone_clean:
                if input_phone_clean == db_phone_clean:
                    phone_matches = True
                elif input_phone_clean.endswith(db_phone_clean) or db_phone_clean.endswith(input_phone_clean):
                    if len(input_phone_clean) >= 9 and len(db_phone_clean) >= 9:
                        phone_matches = input_phone_clean[-9:] == db_phone_clean[-9:]
            
            if email_matches and phone_matches:
                request.session['verified_agent_id'] = agent.id
                messages.success(request, f"Welcome back, Inspector {agent.name}! Credentials successfully verified.")
                return redirect('agent_submit_report')
            else:
                messages.error(request, "Access Denied: Invalid Agent credentials. Please verify your ID, Phone, and Email address.")
        else:
            messages.error(request, "Access Denied: Invalid Agent ID. Please check the ID provided by the TRUST administrator.")
            
    return render(request, 'agent/auth_report.html')

def agent_submit_report(request):
    agent_id = request.session.get('verified_agent_id')
    if not agent_id:
        messages.error(request, "Please verify your Agent Credentials to access the Report Portal.")
        return redirect('agent_report_auth')
        
    try:
        agent = InspectionAgent.objects.select_related('role').get(id=agent_id)
    except InspectionAgent.DoesNotExist:
        request.session.pop('verified_agent_id', None)
        messages.error(request, "Agent profile not found.")
        return redirect('agent_report_auth')
        
    if request.method == 'POST':
        property_id = request.POST.get('property_id', '').strip()
        findings = request.POST.get('findings', '').strip()
        status = request.POST.get('status', 'approved')
        
        property_obj = Property.objects.filter(property_id__iexact=property_id).first()
        if not property_obj:
            messages.error(request, f"Property ID '{property_id}' not found in the TRUST database. Please verify the code and try again.")
        else:
            # Create inspection and report
            inspection, created = Inspection.objects.get_or_create(
                property=property_obj,
                defaults={'status': 'in_progress'}
            )
            
            # Update status to under_inspection if it was pending
            if property_obj.status == 'pending_verification':
                property_obj.status = 'under_inspection'
                property_obj.save()
                
            InspectionReport.objects.create(
                inspection=inspection,
                agent=agent,
                findings=findings,
                status=status
            )
            
            messages.success(request, f"Thank you, {agent.name}! Your {agent.role.name if agent.role else 'Inspector'} report for Property '{property_obj.title}' (ID: {property_obj.property_id}) has been recorded successfully.")
            # Clear authentication session after successful logging
            request.session.pop('verified_agent_id', None)
            return redirect('agent_report_auth')
            
    return render(request, 'agent/submit_report.html', {'agent': agent})
