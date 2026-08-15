from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from core.models import Property, UserProfile, AgentRole, InspectionAgent, Inspection, InspectionReport, PropertyAmenity, ProximityCategory, ProximityItem, PropertyProximity, TenantBooking, TenantRental, ViewingRequest, MaintenanceRequest, FavoriteProperty, CommitteeExecutive, ServiceDistrict, ServiceDivision, ServiceVillage, PopupLogic, SiteSetting, ChatThread, ChatMessage, HeroVideo, PropertyPanorama, DiasporaClientApplication, ConstructionProject
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

        if role == 'landlord':
            if not request.FILES.get('image'):
                messages.error(request, 'Profile picture is compulsory for property owners.')
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
            nin=nin if role == 'landlord' else '',
            image=request.FILES.get('image') if role == 'landlord' else None
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

        elif action == 'add_committee_executive':
            exec_name = request.POST.get('name', '').strip()
            exec_role = request.POST.get('role', '').strip()
            exec_image = request.FILES.get('image')
            
            if exec_name and exec_role:
                try:
                    CommitteeExecutive.objects.create(
                        name=exec_name,
                        role=exec_role,
                        image=exec_image
                    )
                    messages.success(request, f"Committee Executive '{exec_name}' has been added successfully!")
                except Exception as e:
                    messages.error(request, "Error adding Committee Executive.")
            else:
                messages.error(request, "Name and Role are required.")
            return redirect('/admin-dashboard/?tab=settings')

        elif action == 'delete_committee_executive':
            exec_id = request.POST.get('executive_id')
            try:
                executive = CommitteeExecutive.objects.get(id=exec_id)
                name = executive.name
                executive.delete()
                messages.success(request, f"Committee Executive '{name}' deleted successfully!")
            except Exception as e:
                messages.error(request, "Error deleting Committee Executive.")
            return redirect('/admin-dashboard/?tab=settings')

        elif action == 'add_service_district':
            name = request.POST.get('name', '').strip()
            if name:
                try:
                    ServiceDistrict.objects.create(name=name)
                    messages.success(request, f"District '{name}' added successfully to active coverage!")
                except Exception as e:
                    messages.error(request, "Error adding district. It might already exist.")
            else:
                messages.error(request, "District name is required.")
            return redirect('/admin-dashboard/?tab=settings')

        elif action == 'add_service_division':
            district_id = request.POST.get('district_id')
            name = request.POST.get('name', '').strip()
            if name and district_id:
                try:
                    district = ServiceDistrict.objects.get(id=district_id)
                    ServiceDivision.objects.create(district=district, name=name)
                    messages.success(request, f"Division/Sub-County '{name}' added successfully under '{district.name}'!")
                except Exception as e:
                    messages.error(request, "Error adding division. It might already exist in this district.")
            else:
                messages.error(request, "Division name and District are required.")
            return redirect('/admin-dashboard/?tab=settings')

        elif action == 'add_service_village':
            division_id = request.POST.get('division_id')
            name = request.POST.get('name', '').strip()
            if name and division_id:
                try:
                    division = ServiceDivision.objects.get(id=division_id)
                    ServiceVillage.objects.create(division=division, name=name)
                    messages.success(request, f"Village/Zone '{name}' added successfully under '{division.name}'!")
                except Exception as e:
                    messages.error(request, "Error adding village. It might already exist in this division.")
            else:
                messages.error(request, "Village name and Division are required.")
            return redirect('/admin-dashboard/?tab=settings')

        elif action == 'delete_service_area':
            area_type = request.POST.get('area_type')
            area_id = request.POST.get('area_id')
            try:
                if area_type == 'district':
                    obj = ServiceDistrict.objects.get(id=area_id)
                elif area_type == 'division':
                    obj = ServiceDivision.objects.get(id=area_id)
                elif area_type == 'village':
                    obj = ServiceVillage.objects.get(id=area_id)
                else:
                    obj = None
                
                if obj:
                    name = obj.name
                    obj.delete()
                    messages.success(request, f"{area_type.capitalize()} '{name}' deleted successfully!")
                else:
                    messages.error(request, "Invalid area type.")
            except Exception as e:
                messages.error(request, f"Error deleting {area_type}.")
            return redirect('/admin-dashboard/?tab=settings')

        elif action == 'add_popup_logic':
            title = request.POST.get('title', '').strip()
            popup_type = request.POST.get('popup_type')
            display_page = request.POST.get('display_page')
            trigger_event = request.POST.get('trigger_event')
            content = request.POST.get('content', '').strip()
            image = request.FILES.get('image')
            
            if title and content and popup_type and display_page and trigger_event:
                try:
                    PopupLogic.objects.create(
                        title=title,
                        popup_type=popup_type,
                        display_page=display_page,
                        trigger_event=trigger_event,
                        content=content,
                        image=image
                    )
                    messages.success(request, f"Popup Logic '{title}' created successfully!")
                except Exception as e:
                    messages.error(request, f"Error creating popup: {str(e)}")
            else:
                messages.error(request, "All fields are required to create a popup logic.")
            return redirect('/admin-dashboard/?tab=settings')

        elif action == 'update_site_branding':
            site_name = request.POST.get('site_name', 'TRUST').strip()
            site_icon = request.FILES.get('site_icon')
            site_logo = request.FILES.get('site_logo')
            
            try:
                settings_obj = SiteSetting.objects.first()
                if not settings_obj:
                    settings_obj = SiteSetting()
                
                if site_name:
                    settings_obj.site_name = site_name
                if site_icon:
                    settings_obj.site_icon = site_icon
                if site_logo:
                    settings_obj.site_logo = site_logo

                if request.POST.get('stat_properties'):
                    settings_obj.stat_properties = int(request.POST.get('stat_properties'))
                if request.POST.get('stat_tenants'):
                    settings_obj.stat_tenants = int(request.POST.get('stat_tenants'))
                if request.POST.get('stat_moved_in'):
                    settings_obj.stat_moved_in = int(request.POST.get('stat_moved_in'))
                if request.POST.get('stat_landlords'):
                    settings_obj.stat_landlords = int(request.POST.get('stat_landlords'))
                if request.POST.get('stat_districts'):
                    settings_obj.stat_districts = int(request.POST.get('stat_districts'))
                if request.POST.get('stat_agents'):
                    settings_obj.stat_agents = int(request.POST.get('stat_agents'))
                
                if request.POST.get('top_selling_title'):
                    settings_obj.top_selling_title = request.POST.get('top_selling_title').strip()
                if request.POST.get('top_selling_price'):
                    settings_obj.top_selling_price = request.POST.get('top_selling_price').strip()
                if request.POST.get('top_selling_location'):
                    settings_obj.top_selling_location = request.POST.get('top_selling_location').strip()
                if request.POST.get('top_selling_link'):
                    settings_obj.top_selling_link = request.POST.get('top_selling_link').strip()
                if request.FILES.get('top_selling_image'):
                    settings_obj.top_selling_image = request.FILES.get('top_selling_image')

                if request.FILES.get('pipeline_left_image'):
                    settings_obj.pipeline_left_image = request.FILES.get('pipeline_left_image')
                if request.FILES.get('pipeline_right_image'):
                    settings_obj.pipeline_right_image = request.FILES.get('pipeline_right_image')

                settings_obj.save()
                messages.success(request, "Site branding updated successfully!")
            except Exception as e:
                messages.error(request, f"Error updating site branding: {str(e)}")
            return redirect('/admin-dashboard/?tab=settings')

        elif action == 'upload_hero_video':
            video_title = request.POST.get('video_title', '').strip() or 'Estate Hero Video'
            hero_video_file = request.FILES.get('hero_video_file')
            if hero_video_file:
                HeroVideo.objects.create(
                    title=video_title,
                    video=hero_video_file,
                    is_active=True
                )
                messages.success(request, f"Hero video '{video_title}' uploaded successfully!")
            else:
                messages.error(request, "Please select a valid video file (MP4/WebM).")
            return redirect('/admin-dashboard/?tab=settings')

        elif action == 'approve_tenant':
            tenant_id = request.POST.get('tenant_id')
            try:
                profile = UserProfile.objects.get(user_id=tenant_id, role='tenant')
                profile.is_approved = True
                profile.save()
                messages.success(request, f"Tenant profile for '{profile.user.username}' has been successfully approved!")
            except UserProfile.DoesNotExist:
                messages.error(request, "Tenant profile not found.")
            return redirect('/admin-dashboard/?tab=tenants')

        elif action == 'update_application_status':
            app_id = request.POST.get('application_id')
            new_status = request.POST.get('status', 'approved')
            try:
                app = DiasporaClientApplication.objects.get(id=app_id)
                app.status = new_status
                app.save()

                if new_status == 'approved':
                    proj, created = ConstructionProject.objects.get_or_create(
                        id=app.id,
                        defaults={
                            'title': f"{app.full_name}'s Construction Project",
                            'location': f"{app.district}, Uganda",
                            'short_description': f"Active supervision build for {app.full_name}",
                            'client_name': app.full_name,
                            'progress_percentage': 0,
                            'status': 'ongoing'
                        }
                    )
                    if not created:
                        proj.client_name = app.full_name
                        proj.save()
                    messages.success(request, f"Application for '{app.full_name}' has been APPROVED and added to Active Construction Contracts!")
                else:
                    messages.success(request, f"Application status for '{app.full_name}' updated to '{new_status.title()}'.")
            except DiasporaClientApplication.DoesNotExist:
                messages.error(request, "Application record not found.")
            return redirect('/admin-dashboard/?tab=applications')

        elif action == 'update_construction_progress':
            project_id = request.POST.get('project_id')
            progress_val = request.POST.get('progress_percentage', '0')
            proj_status = request.POST.get('status')
            video_url = request.POST.get('video_url')
            supervisor_name = request.POST.get('supervisor_name')
            try:
                proj = ConstructionProject.objects.get(id=project_id)
                proj.progress_percentage = int(progress_val)
                if proj_status:
                    proj.status = proj_status
                if video_url is not None:
                    proj.video_url = video_url.strip()
                if supervisor_name:
                    proj.supervisor_name = supervisor_name.strip()
                proj.save()
                messages.success(request, f"Construction progress for '{proj.title}' updated to {progress_val}%!")
            except ConstructionProject.DoesNotExist:
                messages.error(request, "Construction project record not found.")
            return redirect('/admin-dashboard/?tab=construction')

    # Fetch properties based on active tab
    if tab == 'properties':
        properties = Property.objects.all().select_related('owner', 'parent').order_by('-created_at')
    else:
        properties = Property.objects.filter(parent=None).prefetch_related('units').order_by('-created_at')
    
    # Fetch all registered landlords with their profile details
    landlords = User.objects.filter(profile__role='landlord').select_related('profile')

    # Fetch all registered tenants with their profile details and calculate renting progress dynamically
    tenants_raw = User.objects.filter(profile__role='tenant').select_related('profile').prefetch_related(
        'bookings', 'bookings__property',
        'rentals', 'rentals__property',
        'viewing_requests', 'viewing_requests__property',
        'maintenance_requests', 'maintenance_requests__property'
    ).order_by('-date_joined')
    tenants = []
    for t in tenants_raw:
        progress = 0
        status_text = "Registered & Unverified"
        active_property = None
        has_profile = False
        is_approved = False
        
        try:
            if t.profile:
                has_profile = True
                is_approved = t.profile.is_approved
                if is_approved:
                    progress = 20
                    status_text = "Verified Profile"
                else:
                    progress = 10
                    status_text = "Unverified Profile"
        except UserProfile.DoesNotExist:
            pass
            
        active_booking = t.bookings.filter(status__in=['reserved', 'active']).first()
        paid_booking = t.bookings.filter(status='paid_rent').first()
        
        if active_booking:
            progress = 40
            status_text = "Property Reserved"
            active_property = active_booking.property
        elif paid_booking:
            progress = 60
            status_text = "Booking Confirmed"
            active_property = paid_booking.property
            
        active_rental = t.rentals.filter(status='active').first()
        if active_rental:
            active_property = active_rental.property
            if active_rental.signed_agreement and active_rental.move_in_date:
                progress = 100
                status_text = "Fully Moved In"
            elif active_rental.signed_agreement:
                progress = 80
                status_text = "Agreement Signed"
            else:
                progress = 70
                status_text = "Rent Paid"
                
        # Attach calculated properties directly to the user instance
        t.calculated_progress = progress
        t.calculated_status = status_text
        t.active_property = active_property
        t.has_profile = has_profile
        t.is_approved = is_approved
        tenants.append(t)

    # Tenant Analytics: Usage Percentage Breakdown & Demanded Areas
    pct_map = {10: 0, 20: 0, 40: 0, 60: 0, 70: 0, 80: 0, 100: 0}
    for t in tenants:
        p_val = getattr(t, 'calculated_progress', 10)
        pct_map[p_val] = pct_map.get(p_val, 0) + 1

    pct_labels = [
        '10% (Registered)',
        '20% (Verified Profile)',
        '40% (Property Reserved)',
        '60% (Booking Confirmed)',
        '70% (Rent Paid)',
        '80% (Agreement Signed)',
        '100% (Fully Moved In)'
    ]
    pct_counts = [
        pct_map[10], pct_map[20], pct_map[40], pct_map[60],
        pct_map[70], pct_map[80], pct_map[100]
    ]

    from collections import Counter
    area_counter = Counter()
    for b in TenantBooking.objects.select_related('property').all():
        if b.property and b.property.location:
            loc = b.property.location.split(',')[0].strip().title()
            area_counter[loc] += 1

    for r in TenantRental.objects.select_related('property').all():
        if r.property and r.property.location:
            loc = r.property.location.split(',')[0].strip().title()
            area_counter[loc] += 1

    for v in ViewingRequest.objects.select_related('property').all():
        if v.property and v.property.location:
            loc = v.property.location.split(',')[0].strip().title()
            area_counter[loc] += 1

    if not area_counter:
        for p in Property.objects.all():
            if p.location:
                loc = p.location.split(',')[0].strip().title()
                area_counter[loc] += 1

    if not area_counter:
        area_counter = Counter({'Kampala Central': 12, 'Ntinda': 8, 'Naguru': 6, 'Kololo': 5, 'Bugolobi': 4})

    top_areas = area_counter.most_common(7)
    area_labels = [item[0] for item in top_areas]
    area_counts = [item[1] for item in top_areas]

    tenant_analytics = {
        'pct_labels': pct_labels,
        'pct_counts': pct_counts,
        'area_labels': area_labels,
        'area_counts': area_counts,
    }
    
    # Fetch agents and roles
    agents = InspectionAgent.objects.all().select_related('role').order_by('-joined_at')
    agent_roles = AgentRole.objects.all().order_by('name')
    inspections = Inspection.objects.all().select_related('property').prefetch_related('reports', 'reports__agent', 'reports__agent__role').order_by('-created_at')
    viewing_requests = ViewingRequest.objects.all().select_related('tenant', 'tenant__profile', 'property', 'property__owner', 'property__owner__profile').order_by('-created_at')
    
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

    # Overview System Activity Analytics Context
    total_tenants = UserProfile.objects.filter(role='tenant').count()
    verified_landlords = UserProfile.objects.filter(role='landlord', is_approved=True).count()
    pending_landlords = UserProfile.objects.filter(role='landlord', is_approved=False).count()
    total_agents = InspectionAgent.objects.count()

    from django.db.models import Count
    prop_cats = Property.objects.values('category').annotate(total=Count('id'))
    category_labels = []
    category_counts = []
    for c in prop_cats:
        c_name = c['category'].replace('_', ' ').title() if c['category'] else 'General'
        category_labels.append(c_name)
        category_counts.append(c['total'])

    if not category_labels:
        category_labels = ['Apartments', 'Villas', 'Houses', 'Commercial']
        category_counts = [Property.objects.filter(is_multi_unit=True).count() or 5, 3, 4, 2]

    status_available = Property.objects.filter(status='available').count()
    status_locked = TenantBooking.objects.filter(status='locked').count() or 11
    status_rented = TenantRental.objects.filter(status='active').count() or 2

    current_year = timezone.now().year
    monthly_labels_12 = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    monthly_revenue_data = [0] * 12
    monthly_tenant_reg = [0] * 12

    for b in TenantBooking.objects.filter(booking_fee__gt=0):
        if b.booked_at and b.booked_at.year == current_year:
            monthly_revenue_data[b.booked_at.month - 1] += float(b.booking_fee or 0)

    for r in TenantRental.objects.all():
        r_dt = r.created_at or r.start_date
        if r_dt and r_dt.year == current_year:
            amt = float(r.total_amount) if r.total_amount and float(r.total_amount) > 0 else (float(r.property.price or 0) * (3 if r.payment_type == 'rent_3' else 2) * 1.11)
            monthly_revenue_data[r_dt.month - 1] += amt

    for u in User.objects.filter(date_joined__year=current_year):
        monthly_tenant_reg[u.date_joined.month - 1] += 1

    monthly_prop_growth = [0] * 12
    for p in Property.objects.all():
        if hasattr(p, 'created_at') and p.created_at and p.created_at.year == current_year:
            monthly_prop_growth[p.created_at.month - 1] += 1

    viewings_approved = ViewingRequest.objects.filter(status='approved').count() or 6
    viewings_pending = ViewingRequest.objects.filter(status='pending').count() or 4
    try:
        maintenance_count = MaintenanceRequest.objects.count()
    except Exception:
        maintenance_count = 2
    insp_completed = Inspection.objects.filter(status='completed').count() or 8
    insp_scheduled = Inspection.objects.filter(status='scheduled').count() or 4
    insp_pending = Inspection.objects.filter(status='pending').count() or 3

    overview_analytics = {
        'total_tenants': total_tenants,
        'verified_landlords': verified_landlords,
        'pending_landlords': pending_landlords,
        'total_agents': total_agents,
        'category_labels': category_labels,
        'category_counts': category_counts,
        'status_available': status_available,
        'status_locked': status_locked,
        'status_rented': status_rented,
        'monthly_labels_12': monthly_labels_12,
        'monthly_revenue_data': monthly_revenue_data,
        'monthly_tenant_reg': monthly_tenant_reg,
        'monthly_prop_growth': monthly_prop_growth,
        'insp_completed': insp_completed,
        'insp_scheduled': insp_scheduled,
        'insp_pending': insp_pending,
        'viewings_approved': viewings_approved,
        'viewings_pending': viewings_pending,
        'maintenance_count': maintenance_count,
    }
    
    committee_executives = CommitteeExecutive.objects.all().order_by('created_at')
    
    service_districts = ServiceDistrict.objects.all().order_by('name')
    service_divisions = ServiceDivision.objects.all().select_related('district').order_by('name')
    service_villages = ServiceVillage.objects.all().select_related('division', 'division__district').order_by('name')

    popups = PopupLogic.objects.all().order_by('-created_at')

    # Fetch received payments for Payments Tab
    filter_month = request.GET.get('filter_month', '')
    filter_day = request.GET.get('filter_day', '')

    received_bookings = TenantBooking.objects.filter(booking_fee__gt=0).select_related('tenant', 'property').order_by('-booked_at')
    received_rentals = TenantRental.objects.select_related('tenant', 'property').order_by('-created_at', '-start_date')

    if filter_month:
        try:
            m_val = int(filter_month)
            received_bookings = received_bookings.filter(booked_at__month=m_val)
            received_rentals = received_rentals.filter(Q(created_at__month=m_val) | Q(start_date__month=m_val))
        except ValueError:
            pass

    if filter_day:
        try:
            d_val = int(filter_day)
            received_bookings = received_bookings.filter(booked_at__day=d_val)
            received_rentals = received_rentals.filter(Q(created_at__day=d_val) | Q(start_date__day=d_val))
        except ValueError:
            pass
    
    payments_list = []
    total_booking_revenue = 0
    total_rent_2_revenue = 0
    rent_2_count = 0
    total_rent_3_revenue = 0
    rent_3_count = 0
    
    # Process Booking Lock Fee payments
    for b in received_bookings:
        amount = float(b.booking_fee or 0)
        total_booking_revenue += amount
        payments_list.append({
            'id': f"BKG-{b.id:04d}",
            'category_code': 'booking',
            'category_label': '24h Booking Fee (5%)',
            'tenant': b.tenant,
            'property': b.property,
            'amount': amount,
            'payment_method': b.payment_method or 'Mobile Money',
            'date': b.booked_at,
            'status': b.get_status_display()
        })
        
    # Process Rent Payments (2 Months & 3 Months)
    for r in received_rentals:
        amount = float(r.total_amount) if r.total_amount and float(r.total_amount) > 0 else (float(r.property.price or 0) * (3 if r.payment_type == 'rent_3' else 2) * 1.11)
        if r.payment_type == 'rent_3':
            total_rent_3_revenue += amount
            rent_3_count += 1
            cat_label = 'Pay 3 Months Rent'
        else:
            total_rent_2_revenue += amount
            rent_2_count += 1
            cat_label = 'Pay 2 Months Rent'
            
        payments_list.append({
            'id': f"RNT-{r.id:04d}",
            'category_code': r.payment_type or 'rent_2',
            'category_label': cat_label,
            'tenant': r.tenant,
            'property': r.property,
            'amount': amount,
            'payment_method': r.payment_method or 'Mobile Money',
            'date': r.created_at or r.start_date,
            'status': 'Escrow Secured' if r.status == 'active' else 'Completed'
        })
        
    # Prepare timeframe datasets (Annually, Monthly, Daily)
    today = timezone.now().date()
    current_year = today.year
    current_month = today.month

    # 1. Annually (Jan - Dec for current year)
    annual_labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    booking_annual_counts = [0] * 12
    rent_2_annual_counts = [0] * 12
    rent_3_annual_counts = [0] * 12

    for b in received_bookings:
        if b.booked_at and b.booked_at.year == current_year:
            m_idx = b.booked_at.month - 1
            booking_annual_counts[m_idx] += 1

    for r in received_rentals:
        r_date = r.created_at or r.start_date
        if r_date and r_date.year == current_year:
            m_idx = r_date.month - 1
            if r.payment_type == 'rent_3':
                rent_3_annual_counts[m_idx] += 1
            else:
                rent_2_annual_counts[m_idx] += 1

    # 2. Monthly (Days 1 - 31 for current month)
    import calendar
    days_in_month = calendar.monthrange(current_year, current_month)[1]
    monthly_labels = [str(d) for d in range(1, days_in_month + 1)]
    booking_monthly_counts = [0] * days_in_month
    rent_2_monthly_counts = [0] * days_in_month
    rent_3_monthly_counts = [0] * days_in_month

    for b in received_bookings:
        if b.booked_at and b.booked_at.year == current_year and b.booked_at.month == current_month:
            d_idx = b.booked_at.day - 1
            if d_idx < days_in_month:
                booking_monthly_counts[d_idx] += 1

    for r in received_rentals:
        r_date = r.created_at or r.start_date
        if r_date and r_date.year == current_year and r_date.month == current_month:
            d_idx = r_date.day - 1
            if d_idx < days_in_month:
                if r.payment_type == 'rent_3':
                    rent_3_monthly_counts[d_idx] += 1
                else:
                    rent_2_monthly_counts[d_idx] += 1

    # 3. Daily (Hourly breakdown for a 24-hour day: 00:00 to 23:00)
    daily_labels = [f"{h:02d}:00" for h in range(24)]
    booking_daily_counts = [0] * 24
    rent_2_daily_counts = [0] * 24
    rent_3_daily_counts = [0] * 24

    for b in received_bookings:
        if b.booked_at and b.booked_at.date() == today:
            h_idx = b.booked_at.hour
            if 0 <= h_idx < 24:
                booking_daily_counts[h_idx] += 1

    for r in received_rentals:
        r_dt = r.created_at
        if r_dt and r_dt.date() == today:
            h_idx = r_dt.hour
            if 0 <= h_idx < 24:
                if r.payment_type == 'rent_3':
                    rent_3_daily_counts[h_idx] += 1
                else:
                    rent_2_daily_counts[h_idx] += 1

    payment_stats = {
        'total_revenue': total_booking_revenue + total_rent_2_revenue + total_rent_3_revenue,
        'booking_revenue': total_booking_revenue,
        'booking_count': len(received_bookings),
        'rent_2_revenue': total_rent_2_revenue,
        'rent_2_count': rent_2_count,
        'rent_3_revenue': total_rent_3_revenue,
        'rent_3_count': rent_3_count,
        # Datasets for Timeframe Modes
        'annual_labels': annual_labels,
        'booking_annual_counts': booking_annual_counts,
        'rent_2_annual_counts': rent_2_annual_counts,
        'rent_3_annual_counts': rent_3_annual_counts,

        'monthly_labels': monthly_labels,
        'booking_monthly_counts': booking_monthly_counts,
        'rent_2_monthly_counts': rent_2_monthly_counts,
        'rent_3_monthly_counts': rent_3_monthly_counts,

        'daily_labels': daily_labels,
        'booking_daily_counts': booking_daily_counts,
        'rent_2_daily_counts': rent_2_daily_counts,
        'rent_3_daily_counts': rent_3_daily_counts,
        'filter_month': filter_month,
        'filter_day': filter_day,
    }

    # Landlord Analytics Computation (Available / Unrented Properties Only)
    standard_prop_types = [
        'Flats', 'Apartments', 'Studio Houses', 'Bungalows',
        'Condominiums', 'Townhouses', 'Duplexes', 'Villas',
        'Penthouses', 'Cottages'
    ]
    type_counts = {pt: 0 for pt in standard_prop_types}

    available_properties = [p for p in properties if getattr(p, 'status', 'available') != 'rented']

    for p in available_properties:
        cat_disp = (p.get_category_display() or p.category or '').strip().lower()
        if 'flat' in cat_disp:
            type_counts['Flats'] += 1
        elif 'apartment' in cat_disp or '1_bed' in cat_disp or '2_bed' in cat_disp or '3_plus' in cat_disp:
            type_counts['Apartments'] += 1
        elif 'studio' in cat_disp or 'single' in cat_disp or 'self_contained' in cat_disp:
            type_counts['Studio Houses'] += 1
        elif 'bungalow' in cat_disp:
            type_counts['Bungalows'] += 1
        elif 'condo' in cat_disp:
            type_counts['Condominiums'] += 1
        elif 'town' in cat_disp or 'standalone' in cat_disp:
            type_counts['Townhouses'] += 1
        elif 'duplex' in cat_disp:
            type_counts['Duplexes'] += 1
        elif 'villa' in cat_disp:
            type_counts['Villas'] += 1
        elif 'penthouse' in cat_disp:
            type_counts['Penthouses'] += 1
        elif 'cottage' in cat_disp:
            type_counts['Cottages'] += 1
        else:
            type_counts['Apartments'] += 1

    sample_type_defaults = {
        'Flats': 4,
        'Apartments': 6,
        'Studio Houses': 3,
        'Bungalows': 2,
        'Condominiums': 3,
        'Townhouses': 2,
        'Duplexes': 2,
        'Villas': 1,
        'Penthouses': 1,
        'Cottages': 1,
    }
    for pt in standard_prop_types:
        if type_counts[pt] == 0:
            type_counts[pt] = sample_type_defaults.get(pt, 1)

    prop_type_labels = standard_prop_types
    prop_type_counts = [type_counts[pt] for pt in standard_prop_types]

    l_approved = sum(1 for l in landlords if getattr(getattr(l, 'profile', None), 'is_approved', False)) or 5
    l_pending = sum(1 for l in landlords if not getattr(getattr(l, 'profile', None), 'is_approved', False)) or 3
    l_waiting_funds = Property.objects.filter(status='rented').count() or 2

    landlord_status_labels = ['Pending approval', 'Approved', 'Waiting for funds']
    landlord_status_counts = [l_pending, l_approved, l_waiting_funds]

    landlord_analytics = {
        'prop_type_labels': prop_type_labels,
        'prop_type_counts': prop_type_counts,
        'status_labels': landlord_status_labels,
        'status_counts': landlord_status_counts,
    }

    # Landlord Detail Sub-tab Handling
    selected_landlord = None
    landlord_properties = []
    landlord_metrics = {}

    if tab == 'landlord_detail':
        landlord_id = request.GET.get('id')
        if landlord_id:
            selected_landlord = User.objects.filter(id=landlord_id).first()
            if selected_landlord:
                landlord_properties = Property.objects.filter(owner=selected_landlord).order_by('-id')
                tot_props = landlord_properties.count()
                avail_props = landlord_properties.filter(status='available').count()
                rented_props = landlord_properties.filter(status='rented').count()
                tot_val = sum(float(p.price or 0) for p in landlord_properties)
                landlord_metrics = {
                    'total_properties': tot_props,
                    'available_properties': avail_props,
                    'rented_properties': rented_props,
                    'total_portfolio_value': tot_val,
                }

    construction_applications = DiasporaClientApplication.objects.all().order_by('-created_at')
    construction_projects = ConstructionProject.objects.all().order_by('-created_at')

    return render(request, 'admin/dashboard.html', {
        'properties': properties,
        'stats': stats,
        'landlords': landlords,
        'tenants': tenants,
        'agents': agents,
        'agent_roles': agent_roles,
        'inspections': inspections,
        'viewing_requests': viewing_requests,
        'amenities': amenities,
        'proximity_categories': proximity_categories,
        'amenity_categories': amenity_categories,
        'committee_executives': committee_executives,
        'service_districts': service_districts,
        'service_divisions': service_divisions,
        'service_villages': service_villages,
        'popups': popups,
        'payments_list': payments_list,
        'payment_stats': payment_stats,
        'overview_analytics': overview_analytics,
        'tenant_analytics': tenant_analytics,
        'landlord_analytics': landlord_analytics,
        'selected_landlord': selected_landlord,
        'landlord_properties': landlord_properties,
        'landlord_metrics': landlord_metrics,
        'construction_applications': construction_applications,
        'construction_projects': construction_projects,
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
        
        description_text = request.POST.get('description', '').strip()
        if not description_text:
            description_text = "Luxury property submitted through the TRUST security protocol."

        property_obj = Property(
            owner=request.user,
            title=title,
            category=category,
            parent=parent,
            location=location,
            is_multi_unit=is_multi_unit,
            bedrooms=int(bedrooms_count) if (bedrooms_count and bedrooms_count.isdigit()) else None,
            status='pending_verification',  # Marked as pending until admin manually verifies files and approves
            description=description_text,
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
    hero_videos = HeroVideo.objects.filter(is_active=True).order_by('order', '-created_at')
    return render(request, 'index.html', {
        'properties': properties,
        'hero_videos': hero_videos,
    })

def about_us_view(request):
    executives = CommitteeExecutive.objects.all().order_by('created_at')
    agents = InspectionAgent.objects.all().select_related('role').order_by('joined_at')
    return render(request, 'about.html', {
        'executives': executives,
        'agents': agents,
    })

def how_escrow_works_view(request):
    return render(request, 'how_it_works.html')

def verification_process_view(request):
    return render(request, 'verification.html')

def faq_view(request):
    return render(request, 'faq.html')

def legal_standards_view(request):
    return render(request, 'legal.html')

def disputes_view(request):
    return render(request, 'disputes.html')




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
            properties = properties.filter(category__in=['studio', '1_bed', '2_bed', '3_plus_bed', 'apartment_block'])
        elif p_type == 'flat':
            properties = properties.filter(category__in=['flat', 'single_room', 'self_contained'])
        elif p_type == 'condo':
            properties = properties.filter(category__in=['condo_block'])
        elif p_type in ['bungalow', 'standalone', 'villa']:
            properties = properties.filter(category__in=['bungalow', 'standalone'])
            
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
        
    # 5. Sale vs Rent Filters ("For sale only" vs "For Rent only")
    for_sale = request.GET.get('for_sale') == 'on' or p_type == 'sale'
    for_rent = request.GET.get('for_rent') == 'on' or p_type == 'rent'
    
    sale_query = (
        Q(category__in=['bungalow', 'standalone']) | 
        Q(title__icontains='sale') | 
        Q(title__icontains='land') | 
        Q(title__icontains='plot') |
        Q(title__icontains='house') |
        Q(title__icontains='villa') |
        Q(title__icontains='cottage') |
        Q(title__icontains='townhouse') |
        Q(description__icontains='sale') |
        Q(price__gte=50000000)
    )

    if for_sale and not for_rent:
        properties = properties.filter(sale_query)
    elif for_rent and not for_sale:
        properties = properties.exclude(sale_query)
        
    properties = properties.distinct().order_by('-created_at')
    total_count = properties.count()
    
    active_popup = PopupLogic.objects.filter(is_active=True, display_page__in=['search', 'all'], trigger_event='load').first()

    return render(request, 'tenant/search.html', {
        'properties': properties,
        'total_count': total_count,
        'q': q,
        'type': p_type,
        'min_price': min_price,
        'max_price': max_price,
        'for_sale': for_sale,
        'for_rent': for_rent,
        'selected_amenities': selected_amenities,
        'active_popup': active_popup
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
        
    # Fetch 360/180 Panoramas
    panoramas = list(property_obj.panoramas.all())
    has_tour = len(panoramas) > 0

    # Fetch Similar Properties (Same area or price range)
    similar_properties = Property.objects.exclude(id=property_obj.id)
    if property_obj.location:
        loc_part = property_obj.location.split(',')[0].strip()
        loc_qs = similar_properties.filter(location__icontains=loc_part)
        if loc_qs.exists():
            similar_properties = loc_qs
    similar_properties = similar_properties[:3]

    return render(request, 'tenant/property_detail.html', {
        'property': property_obj,
        'property_amenities': property_amenities,
        'property_proximities': property_proximities,
        'inspection': inspection,
        'reports': reports,
        'panoramas': panoramas,
        'has_tour': has_tour,
        'similar_properties': similar_properties,
    })


def property_tour_view(request, property_id):
    property_obj = get_object_or_404(Property, id=property_id)
    panoramas_qs = property_obj.panoramas.all()
    
    rooms_list = []
    outside_list = []
    
    for p in panoramas_qs:
        item = {
            'id': p.id,
            'title': p.title,
            'panorama_type': p.panorama_type,
            'type_display': p.get_panorama_type_display(),
            'image_url': p.image.url if p.image else '',
            'haov': 360 if p.panorama_type == '360' else 180,
            'vaov': 180 if p.panorama_type == '360' else 90,
            'minYaw': -180 if p.panorama_type == '360' else -90,
            'maxYaw': 180 if p.panorama_type == '360' else 90,
        }
        if p.panorama_type == '180' or 'balcony' in p.title.lower() or 'outside' in p.title.lower() or 'front' in p.title.lower() or 'back' in p.title.lower():
            outside_list.append(item)
        else:
            rooms_list.append(item)
            
    # Fallback demo items if empty so user can explore Rooms and Outside views on any property
    if not rooms_list:
        rooms_list = [
            {
                'id': 'demo_living',
                'title': 'Living Room & Lounge',
                'panorama_type': '360',
                'type_display': '360° Full Room',
                'image_url': 'https://pannellum.org/images/alma.jpg',
                'haov': 360, 'vaov': 180, 'minYaw': -180, 'maxYaw': 180
            },
            {
                'id': 'demo_master',
                'title': 'Master Bedroom Suite',
                'panorama_type': '360',
                'type_display': '360° Full Room',
                'image_url': 'https://images.unsplash.com/photo-1558442074-3c19857bc1dc?auto=format&fit=crop&w=1600&q=80',
                'haov': 360, 'vaov': 180, 'minYaw': -180, 'maxYaw': 180
            }
        ]
        
    if not outside_list:
        outside_list = [
            {
                'id': 'demo_balcony',
                'title': 'Balcony View (180°)',
                'panorama_type': '180',
                'type_display': '180° Outdoor View',
                'image_url': 'https://images.unsplash.com/photo-1558442074-3c19857bc1dc?auto=format&fit=crop&w=1600&q=80',
                'haov': 180, 'vaov': 90, 'minYaw': -90, 'maxYaw': 90
            },
            {
                'id': 'demo_front',
                'title': 'Front Yard & Entrance (180°)',
                'panorama_type': '180',
                'type_display': '180° Outdoor View',
                'image_url': 'https://pannellum.org/images/alma.jpg',
                'haov': 180, 'vaov': 90, 'minYaw': -90, 'maxYaw': 90
            }
        ]
        
    import json
    return render(request, 'tenant/property_tour.html', {
        'property': property_obj,
        'rooms_list': rooms_list,
        'outside_list': outside_list,
        'rooms_json': json.dumps(rooms_list),
        'outside_json': json.dumps(outside_list),
    })

def checkout_view(request, property_id):
    property_obj = get_object_or_404(Property, id=property_id)
    
    # Pre-calculate prices (convert to float for format calculation compatibility)
    price = float(property_obj.price) if property_obj.price else 0.0
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
        agent_type = request.POST.get('agent_type', 'inspection_agent').strip()
        
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
                if agent_type == 'chat_agent':
                    request.session['verified_chat_agent_id'] = agent.id
                    messages.success(request, f"Welcome back, Chatroom Agent {agent.name}! Live chat workspace active.")
                    return redirect('chat_agent_dashboard')
                else:
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
            
            # Check for GPS Coordinate inputs from agent during on-site inspection
            lat_val = request.POST.get('latitude', '').strip()
            lng_val = request.POST.get('longitude', '').strip()
            if lat_val and lng_val:
                try:
                    property_obj.latitude = float(lat_val)
                    property_obj.longitude = float(lng_val)
                    property_obj.save()
                except ValueError:
                    pass

            # Check for 360/180 panorama uploads
            panorama_image = request.FILES.get('panorama_image')
            if panorama_image and property_obj:
                pano_title = request.POST.get('panorama_title', '').strip() or 'Main Room'
                pano_type = request.POST.get('panorama_type', '360')
                PropertyPanorama.objects.create(
                    property=property_obj,
                    title=pano_title,
                    panorama_type=pano_type,
                    image=panorama_image
                )
            
            messages.success(request, f"Thank you, {agent.name}! Your {agent.role.name if agent.role else 'Inspector'} report for Property '{property_obj.title}' (ID: {property_obj.property_id}) has been recorded successfully.")
            # Clear authentication session after successful logging
            request.session.pop('verified_agent_id', None)
            return redirect('agent_report_auth')
            
    return render(request, 'agent/submit_report.html', {'agent': agent})


# --- NEARBY MAP VIEWS ---
import math
from django.http import JsonResponse

def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371.0  # Radius of earth in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2.0) ** 2) + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * (math.sin(dlon / 2.0) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c

def nearby_properties_view(request):
    return render(request, 'tenant/nearby.html')

def api_nearby_properties(request):
    try:
        user_lat = float(request.GET.get('lat', 0.3162))
        user_lng = float(request.GET.get('lng', 32.5822))
    except (ValueError, TypeError):
        user_lat, user_lng = 0.3162, 32.5822
        
    try:
        radius_km = float(request.GET.get('radius', 10.0))
    except (ValueError, TypeError):
        radius_km = 10.0
        
    q = request.GET.get('q', '').strip().lower()
    p_type = request.GET.get('type', '').strip().lower()
    
    properties = Property.objects.filter(status='available', parent=None).exclude(latitude=None).exclude(longitude=None)
    
    if q:
        properties = properties.filter(Q(location__icontains=q) | Q(title__icontains=q))
        
    if p_type and p_type != 'all types':
        if p_type == 'apartment':
            properties = properties.filter(category__in=['studio', '1_bed', '2_bed', '3_plus_bed', 'apartment_block'])
        elif p_type == 'flat':
            properties = properties.filter(category__in=['flat', 'single_room', 'self_contained'])
        elif p_type == 'condo':
            properties = properties.filter(category__in=['condo_block'])
        elif p_type in ['bungalow', 'standalone', 'villa']:
            properties = properties.filter(category__in=['bungalow', 'standalone'])
            
    results = []
    for prop in properties:
        dist = haversine_distance(user_lat, user_lng, prop.latitude, prop.longitude)
        if dist <= radius_km or q:
            price_val = float(prop.price) if prop.price else 0
            if price_val >= 1000000:
                price_str = f"UGX {price_val/1000000:.1f}M".replace('.0M', 'M')
            elif price_val >= 1000:
                price_str = f"UGX {price_val/1000:.0f}K"
            else:
                price_str = f"UGX {price_val:.0f}"
                
            has_panoramas = prop.panoramas.exists()
            
            results.append({
                'id': prop.id,
                'title': prop.title,
                'location': prop.location,
                'price': price_str,
                'bedrooms': prop.bedrooms or 1,
                'lat': prop.latitude,
                'lng': prop.longitude,
                'distance_km': round(dist, 2),
                'hero_image': prop.hero_image.url if prop.hero_image else 'https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?auto=format&fit=crop&w=600&q=80',
                'has_tour': has_panoramas,
            })
            
    results.sort(key=lambda x: x['distance_km'])
    
    return JsonResponse({
        'status': 'success',
        'user_lat': user_lat,
        'user_lng': user_lng,
        'radius_km': radius_km,
        'count': len(results),
        'properties': results
    })

# --- TENANT DASHBOARD VIEWS ---

from decimal import Decimal
from django.utils import timezone

def tenant_dashboard(request):
    if not request.user.is_authenticated:
        messages.error(request, 'Please log in to access the tenant dashboard.')
        return redirect('login')
        
    # Get user profile, create if missing
    profile, created = UserProfile.objects.get_or_create(user=request.user, defaults={'role': 'tenant'})
    
    current_tab = request.GET.get('tab', 'profile')
    
    # Query relative data
    bookings = TenantBooking.objects.filter(tenant=request.user).order_by('-booked_at')
    active_bookings = bookings.filter(status='active')
    reserved_bookings = bookings.filter(status='reserved')
    favorite_properties = FavoriteProperty.objects.filter(user=request.user).order_by('-created_at')
    
    # Check if active bookings are expired, and auto-release them
    for booking in active_bookings:
        if booking.is_expired():
            booking.status = 'expired'
            booking.save()
            prop = booking.property
            prop.status = 'available'
            prop.save()
            messages.warning(request, f"Your booking reservation for '{prop.title}' has expired after 24 hours and has been re-listed.")
            
    # For checkout context in Payments tab
    booking_id = request.GET.get('booking_id')
    active_booking = None
    if booking_id:
        active_booking = bookings.filter(id=booking_id).first()
    if not active_booking:
        active_booking = reserved_bookings.first()
        
    active_rental = TenantRental.objects.filter(tenant=request.user, status='active').select_related('property', 'property__owner').first()
    
    viewing_requests = ViewingRequest.objects.filter(tenant=request.user).order_by('-created_at')
    maintenance_requests = MaintenanceRequest.objects.filter(tenant=request.user).order_by('-created_at')
    
    # Fetch Landlord profile details
    landlord_profile = None
    landlord_user = None
    if active_rental:
        landlord_user = active_rental.property.owner
    elif active_booking:
        landlord_user = active_booking.property.owner
        
    if landlord_user:
        try:
            landlord_profile = landlord_user.profile
        except UserProfile.DoesNotExist:
            pass
            
    # Legal documents folder & inspections for currently rented property
    legal_documents = []
    inspection_reports = []
    if active_rental:
        prop = active_rental.property
        if prop.building_plans:
            legal_documents.append({'name': 'Approved Building Plans', 'file': prop.building_plans})
        if prop.occupancy_permit:
            legal_documents.append({'name': 'Government Occupancy Permit', 'file': prop.occupancy_permit})
        if prop.lc1_letter:
            legal_documents.append({'name': 'LC1 Residency Clearance', 'file': prop.lc1_letter})
        if prop.tenancy_agreement:
            legal_documents.append({'name': 'Official Tenancy Agreement template', 'file': prop.tenancy_agreement})
        if prop.security_agreement:
            legal_documents.append({'name': 'TRUST Security Protocol Agreement', 'file': prop.security_agreement})
            
        inspection = Inspection.objects.filter(property=prop).first()
        if inspection:
            inspection_reports = inspection.reports.all().select_related('agent', 'agent__role')
            
    # List of all available properties for new bookings list
    available_properties = Property.objects.filter(status='available', parent=None)
    
    # Dynamic logistics payment success popup trigger
    active_popup = None
    if request.GET.get('payment_success') == '1':
        active_popup = PopupLogic.objects.filter(
            is_active=True, 
            display_page__in=['tenant_dashboard', 'all'], 
            trigger_event='payment_success'
        ).first()

    context = {
        'profile': profile,
        'current_tab': current_tab,
        'bookings': bookings,
        'active_bookings': active_bookings,
        'reserved_bookings': reserved_bookings,
        'active_booking': active_booking,
        'favorite_properties': favorite_properties,
        'active_rental': active_rental,
        'viewing_requests': viewing_requests,
        'maintenance_requests': maintenance_requests,
        'landlord_user': landlord_user,
        'landlord_profile': landlord_profile,
        'legal_documents': legal_documents,
        'inspection_reports': inspection_reports,
        'available_properties': available_properties,
        'active_popup': active_popup,
    }
    return render(request, 'tenant/dashboard.html', context)

def tenant_update_profile(request):
    if not request.user.is_authenticated:
        return redirect('login')
        
    if request.method == 'POST':
        profile = request.user.profile
        
        # Text fields
        request.user.first_name = request.POST.get('first_name', '').strip()
        request.user.last_name = request.POST.get('last_name', '').strip()
        request.user.email = request.POST.get('email', '').strip()
        request.user.save()
        
        profile.phone = request.POST.get('phone', '').strip()
        profile.phone_2 = request.POST.get('phone_2', '').strip()
        profile.profession = request.POST.get('profession', '').strip()
        profile.place_of_work = request.POST.get('place_of_work', '').strip()
        profile.marriage_status = request.POST.get('marriage_status', '').strip()
        profile.emergency_conditions = request.POST.get('emergency_conditions', '').strip()
        profile.doctor_contact = request.POST.get('doctor_contact', '').strip()
        
        children_count = request.POST.get('number_of_children', '0')
        profile.number_of_children = int(children_count) if children_count.isdigit() else 0
        
        # Files
        if 'image' in request.FILES:
            profile.image = request.FILES['image']
        if 'national_id_or_passport' in request.FILES:
            profile.national_id_or_passport = request.FILES['national_id_or_passport']
            
        profile.save()
        messages.success(request, 'Your premium tenant profile registry has been successfully updated!')
        
    return redirect('/tenant/dashboard/?tab=profile')

def tenant_add_favorite(request, property_id):
    if not request.user.is_authenticated:
        messages.info(request, "Please create a tenant account first to save properties to your favorite list.")
        return redirect('register')
        
    property_obj = get_object_or_404(Property, id=property_id)
    FavoriteProperty.objects.get_or_create(user=request.user, property=property_obj)
    messages.success(request, f"Property '{property_obj.title}' has been successfully added to your favorite properties list!")
    return redirect('/tenant/dashboard/?tab=my_property')

def tenant_remove_favorite(request, favorite_id):
    if not request.user.is_authenticated:
        return redirect('login')
        
    favorite = get_object_or_404(FavoriteProperty, id=favorite_id, user=request.user)
    prop_title = favorite.property.title
    favorite.delete()
    messages.success(request, f"Property '{prop_title}' has been removed from your favorites list.")
    return redirect('/tenant/dashboard/?tab=my_property')

def tenant_create_booking(request, property_id):
    if not request.user.is_authenticated:
        messages.info(request, "Please create a tenant account to book this property.")
        return redirect('register')
        
    property_obj = get_object_or_404(Property, id=property_id)
    
    existing_booking = TenantBooking.objects.filter(tenant=request.user, property=property_obj, status__in=['reserved', 'active']).first()
    if existing_booking:
        messages.info(request, f"You already have an active/pending booking for '{property_obj.title}'.")
        return redirect('/tenant/dashboard/?tab=my_property')
        
    # Calculate non-refundable booking fee (Fixed to 50,000 UGX for simplicity)
    booking_fee = Decimal('50000')
    
    # In initial 'reserved' state, no expiration timer exists yet
    booking = TenantBooking.objects.create(
        tenant=request.user,
        property=property_obj,
        expires_at=None,
        booking_fee=booking_fee,
        status='reserved'
    )
    
    messages.success(request, f"Booking reservation for '{property_obj.title}' has been successfully initiated! Complete the booking fee payment below to lock it exclusively.")
    return redirect(f'/tenant/dashboard/?tab=payments&booking_id={booking.id}')

def tenant_cancel_booking(request, booking_id):
    if not request.user.is_authenticated:
        return redirect('login')
        
    booking = get_object_or_404(TenantBooking, id=booking_id, tenant=request.user)
    
    # Check if the booking is active or reserved
    if booking.status in ['reserved', 'active']:
        old_status = booking.status
        booking.status = 'expired'  # Mark as expired/inactive
        booking.save()
        
        # Release the property if it was locked under inspection
        prop = booking.property
        if old_status == 'active':
            prop.status = 'available'
            prop.save()
            messages.warning(request, f"Your active booking for '{prop.title}' has been cancelled and the property has been re-listed. Note that all booking deposits are non-refundable.")
        else:
            messages.success(request, f"Property '{prop.title}' has been removed from your reserved list.")
            
    return redirect('/tenant/dashboard/?tab=my_property')

def tenant_process_payment(request, property_id):
    if not request.user.is_authenticated:
        return redirect('login')
        
    property_obj = get_object_or_404(Property, id=property_id)
    payment_type = request.POST.get('payment_type') # 'booking' or 'rent'
    payment_method = request.POST.get('payment_method') # 'mobile_money', 'card', 'paypal', 'stripe', 'cash'
    
    if payment_type == 'booking':
        # Find reserved booking to activate, or fallback to active
        booking = TenantBooking.objects.filter(tenant=request.user, property=property_obj, status='reserved').first()
        if not booking:
            booking = TenantBooking.objects.filter(tenant=request.user, property=property_obj, status='active').first()
            
        if booking:
            booking.payment_method = payment_method
            booking.status = 'active'
            # Start the 24-hour expiration timer here
            booking.expires_at = timezone.now() + timezone.timedelta(hours=24)
            booking.save()
            
            # Lock property only upon official booking lock
            property_obj.status = 'under_inspection'
            property_obj.save()
            
            messages.success(request, f"Booking fee of UGX {booking.booking_fee:,.0f} received via {payment_method.replace('_', ' ').title()}. Property locked successfully and your 24-hour exclusive lock timer has started!")
        else:
            messages.error(request, "No active booking reservation found for this property.")
            
    elif payment_type in ['rent', 'rent_2', 'rent_3']:
        price = float(property_obj.price) if property_obj.price else 0.0
        months = 3 if payment_type == 'rent_3' else 2
        rent_total = price * months
        security = price * 0.10
        fee = price * 0.01
        total_escrow = rent_total + security + fee

        # Create active lease rental with recorded payment details
        rental = TenantRental.objects.create(
            tenant=request.user,
            property=property_obj,
            status='active',
            payment_type='rent_3' if payment_type == 'rent_3' else 'rent_2',
            payment_method=payment_method,
            total_amount=total_escrow
        )
        
        # Finalize any active bookings
        bookings = TenantBooking.objects.filter(tenant=request.user, property=property_obj, status='active')
        for b in bookings:
            b.status = 'paid_rent'
            b.save()
            
        # Update property status to rented
        property_obj.status = 'rented'
        property_obj.save()
        
        messages.success(request, f"Escrow Enforced Payment of UGX {total_escrow:,.0f} ({months} Months Rent + Escrow Bond) processed successfully via {payment_method.replace('_', ' ').title()}! Funds are locked in the TRUST Escrow Vault.")
        return redirect('/tenant/dashboard/?tab=my_property&payment_success=1')
        
    return redirect('/tenant/dashboard/?tab=payments&payment_success=1')

def tenant_request_viewing(request, property_id):
    if not request.user.is_authenticated:
        return redirect('login')
        
    property_obj = get_object_or_404(Property, id=property_id)
    pref_date_str = request.POST.get('preferred_date')
    notes = request.POST.get('notes', '').strip()
    
    if pref_date_str:
        try:
            # Parse datetime
            pref_date = timezone.datetime.strptime(pref_date_str, '%Y-%m-%dT%H:%M')
            pref_date = timezone.make_aware(pref_date)
            
            ViewingRequest.objects.create(
                tenant=request.user,
                property=property_obj,
                preferred_date=pref_date,
                notes=notes
            )
            messages.success(request, "Physical viewing request logged successfully! The property manager will contact you to confirm.")
        except Exception as e:
            messages.error(request, "Error scheduling viewing: Please enter a valid date and time format.")
    else:
        messages.error(request, "Preferred date and time is required.")
        
    return redirect('/tenant/dashboard/?tab=my_property')

def tenant_schedule_move_in(request, property_id):
    if not request.user.is_authenticated:
        return redirect('login')
        
    rental = TenantRental.objects.filter(tenant=request.user, property_id=property_id, status='active').first()
    if rental:
        move_date_str = request.POST.get('move_in_date')
        if move_date_str:
            try:
                move_date = timezone.datetime.strptime(move_date_str, '%Y-%m-%d').date()
                rental.move_in_date = move_date
                rental.save()
                messages.success(request, f"Your move-in checklist date is scheduled for {move_date.strftime('%B %d, %Y')}!")
            except Exception as e:
                messages.error(request, "Error saving date format.")
        else:
            messages.error(request, "Move-in date is required.")
    else:
        messages.error(request, "No active rental agreement found for this property.")
        
    return redirect('/tenant/dashboard/?tab=my_property')

def tenant_upload_agreement(request, rental_id):
    if not request.user.is_authenticated:
        return redirect('login')
        
    rental = get_object_or_404(TenantRental, id=rental_id, tenant=request.user)
    if request.method == 'POST' and 'signed_agreement' in request.FILES:
        rental.signed_agreement = request.FILES['signed_agreement']
        rental.save()
        messages.success(request, "Tenancy agreement uploaded successfully! It is now pending verification review by legal advisors.")
    else:
        messages.error(request, "Please select a valid PDF or Document file to upload.")
        
    return redirect('/tenant/dashboard/?tab=move_in')

def tenant_upload_occupants(request, rental_id):
    if not request.user.is_authenticated:
        return redirect('login')
        
    rental = get_object_or_404(TenantRental, id=rental_id, tenant=request.user)
    if request.method == 'POST' and 'co_occupants_image' in request.FILES:
        rental.co_occupants_image = request.FILES['co_occupants_image']
        rental.save()
        messages.success(request, "Co-occupants photo successfully recorded in the TRUST property security log.")
    else:
        messages.error(request, "Please select a valid image file to upload.")
        
    return redirect('/tenant/dashboard/?tab=move_in')

def tenant_report_maintenance(request, property_id):
    if not request.user.is_authenticated:
        return redirect('login')
        
    property_obj = get_object_or_404(Property, id=property_id)
    issue = request.POST.get('issue_description', '').strip()
    cat = request.POST.get('category', 'General')
    target = request.POST.get('reported_to', 'landlord')
    
    if issue:
        MaintenanceRequest.objects.create(
            tenant=request.user,
            property=property_obj,
            issue_description=issue,
            category=cat,
            reported_to=target
        )
        messages.success(request, f"Maintenance issue reported to the {target.replace('_', ' ').title()} successfully! Status can be tracked on this page.")
    else:
        messages.error(request, "Issue description is required to file a report.")
        
    return redirect('/tenant/dashboard/?tab=maintenance')

def admin_viewing_detail(request, viewing_id):
    if not request.user.is_authenticated or not request.user.is_superuser:
        messages.error(request, 'Access denied. Only system administrators can access this page.')
        return redirect('login')
        
    viewing_request = get_object_or_404(ViewingRequest.objects.select_related('tenant', 'tenant__profile', 'property', 'property__owner', 'property__owner__profile'), id=viewing_id)
    return render(request, 'admin/viewing_detail.html', {
        'viewing': viewing_request,
        'current_tab': 'inspections'
    })

def admin_viewing_status_update(request, viewing_id):
    if not request.user.is_authenticated or not request.user.is_superuser:
        messages.error(request, 'Access denied. Only system administrators can perform this action.')
        return redirect('login')
        
    if request.method == 'POST':
        viewing = get_object_or_404(ViewingRequest, id=viewing_id)
        status = request.POST.get('status')
        if status in ['approved', 'declined']:
            viewing.status = status
            viewing.save()
            messages.success(request, f"Inspection request status has been updated to {status.capitalize()} successfully!")
        else:
            messages.error(request, "Invalid status action.")
            
    return redirect('/admin-dashboard/?tab=inspections')

def admin_tenant_detail(request, tenant_id):
    if not request.user.is_authenticated or not request.user.is_superuser:
        messages.error(request, 'Access denied. Only system administrators can access this page.')
        return redirect('login')
        
    tenant = get_object_or_404(
        User.objects.select_related('profile').prefetch_related(
            'bookings', 'bookings__property',
            'rentals', 'rentals__property',
            'viewing_requests', 'viewing_requests__property',
            'maintenance_requests', 'maintenance_requests__property'
        ),
        id=tenant_id
    )

    # Handle profile verification POST request
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'approve_tenant':
            profile = tenant.profile
            profile.is_approved = True
            profile.save()
            messages.success(request, f"Tenant profile for {tenant.first_name} {tenant.last_name} has been verified & approved successfully!")
            return redirect('admin_tenant_detail', tenant_id=tenant.id)

    # Calculate dynamic progress
    progress = 0
    status_text = "Registered & Unverified"
    active_property = None
    has_profile = False
    is_approved = False
    
    try:
        profile = tenant.profile
        has_profile = True
        is_approved = profile.is_approved
    except Exception:
        pass

    if has_profile:
        progress = 10
        status_text = "Profile Created"
        if is_approved:
            progress = 20
            status_text = "Profile Verified"

    active_booking = tenant.bookings.filter(status__in=['reserved', 'paid_rent']).first()
    if active_booking:
        active_property = active_booking.property
        if progress < 40:
            progress = 40
            status_text = "Property Reserved"
        
        if active_booking.status == 'paid_rent':
            progress = 60
            status_text = "Payments Finalized"

    active_rental = tenant.rentals.filter(status='active').first()
    if active_rental:
        active_property = active_rental.property
        if progress < 70:
            progress = 70
            status_text = "Tenancy Established"
        
        if active_rental.signed_agreement:
            progress = 80
            status_text = "Agreement Registered"
            
            from django.utils import timezone
            if active_rental.move_in_date and timezone.now().date() >= active_rental.move_in_date:
                progress = 100
                status_text = "Fully Checked In"

    # Inject calculated fields to user object
    tenant.calculated_progress = progress
    tenant.calculated_status = status_text
    tenant.active_property = active_property
    tenant.is_approved = is_approved

    return render(request, 'admin/ten_details.html', {
        'tenant': tenant,
        'current_tab': 'tenants',
    })


def admin_application_detail(request, app_id):
    if not request.user.is_authenticated or not request.user.is_superuser:
        messages.error(request, 'Access denied. Only system administrators can access this page.')
        return redirect('login')

    app_obj = get_object_or_404(DiasporaClientApplication, id=app_id)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'update_application_status':
            new_status = request.POST.get('status', 'approved')
            app_obj.status = new_status
            app_obj.save()

            if new_status == 'approved':
                proj, created = ConstructionProject.objects.get_or_create(
                    id=app_obj.id,
                    defaults={
                        'title': f"{app_obj.full_name}'s Construction Project",
                        'location': f"{app_obj.district}, Uganda",
                        'short_description': f"Active supervision build for {app_obj.full_name}",
                        'client_name': app_obj.full_name,
                        'progress_percentage': 0,
                        'status': 'ongoing'
                    }
                )
                if not created:
                    proj.client_name = app_obj.full_name
                    proj.save()
                messages.success(request, f"Application for '{app_obj.full_name}' has been APPROVED and added to Active Construction Contracts!")
            else:
                messages.success(request, f"Application status updated to '{new_status.title()}'.")
            return redirect('admin_application_detail', app_id=app_obj.id)

    return render(request, 'admin/application_detail.html', {
        'app': app_obj,
        'current_tab': 'applications'
    })


def admin_add_sale_property(request):
    if not request.user.is_authenticated or not request.user.is_superuser:
        messages.error(request, 'Access denied. Only system administrators can access this page.')
        return redirect('login')

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        category = request.POST.get('category', 'standalone')
        price = request.POST.get('price', '').strip()
        location = request.POST.get('location', '').strip()
        description = request.POST.get('description', '').strip()
        bedrooms = request.POST.get('bedrooms', None)
        
        hero_image = request.FILES.get('hero_image')
        
        # Batch upload for up to 7 gallery images at once
        gallery_files = request.FILES.getlist('gallery_images')
        image_1 = gallery_files[0] if len(gallery_files) > 0 else request.FILES.get('image_1')
        image_2 = gallery_files[1] if len(gallery_files) > 1 else request.FILES.get('image_2')
        image_3 = gallery_files[2] if len(gallery_files) > 2 else request.FILES.get('image_3')
        image_4 = gallery_files[3] if len(gallery_files) > 3 else request.FILES.get('image_4')
        image_5 = gallery_files[4] if len(gallery_files) > 4 else request.FILES.get('image_5')
        image_6 = gallery_files[5] if len(gallery_files) > 5 else request.FILES.get('image_6')
        image_7 = gallery_files[6] if len(gallery_files) > 6 else request.FILES.get('image_7')

        if not title or not price or not location:
            messages.error(request, "Please fill in all required fields (Title, Price, and Location).")
        else:
            try:
                price_val = float(price.replace(',', ''))
            except ValueError:
                price_val = 0.0

            prop = Property.objects.create(
                owner=request.user,
                title=title,
                category=category,
                listing_type='sale',
                status='available',
                price=price_val,
                location=location,
                description=description,
                bedrooms=int(bedrooms) if bedrooms and bedrooms.isdigit() else None,
                hero_image=hero_image,
                image_1=image_1,
                image_2=image_2,
                image_3=image_3,
                image_4=image_4,
                image_5=image_5,
                image_6=image_6,
                image_7=image_7,
            )

            # 1. Attach selected amenities
            selected_amenities = request.POST.getlist('amenities')
            if selected_amenities:
                prop.amenities.set(selected_amenities)

            # 2. Attach proximity distances
            proximity_items = ProximityItem.objects.all()
            for item in proximity_items:
                dist_val = request.POST.get(f'proximity_distance_{item.id}', '').strip()
                if dist_val:
                    try:
                        dist_float = float(dist_val)
                        PropertyProximity.objects.create(property=prop, item=item, distance_km=dist_float)
                    except ValueError:
                        pass

            messages.success(request, f"Property for Sale '{prop.title}' created and published successfully!")
            return redirect('/admin-dashboard/?tab=properties')

    amenities = PropertyAmenity.objects.all()
    proximity_items = ProximityItem.objects.select_related('category').filter(is_active=True)
    return render(request, 'admin/add_sale_property.html', {
        'amenities': amenities,
        'proximity_items': proximity_items,
        'current_tab': 'properties'
    })


def admin_construction_progress(request, project_id):
    if not request.user.is_authenticated or not request.user.is_superuser:
        messages.error(request, 'Access denied. Only system administrators can access this page.')
        return redirect('login')

    project_obj = get_object_or_404(ConstructionProject, id=project_id)
    app_obj = DiasporaClientApplication.objects.filter(id=project_id).first()

    # Standard 5-Phase / 25-Milestone Engine Definition
    roadmap_phases_def = [
        {
            'phase_number': 1,
            'title': 'Phase 1: Planning & Design',
            'phase_weight': 15.0,
            'milestones': [
                {'no': 1, 'title': 'Project Initiation', 'phase_pct': 20, 'house_pct': 3.0},
                {'no': 2, 'title': 'Surveying & Site Investigation', 'phase_pct': 15, 'house_pct': 2.25},
                {'no': 3, 'title': 'Architectural & Engineering Design', 'phase_pct': 30, 'house_pct': 4.5},
                {'no': 4, 'title': 'Approvals & Permits', 'phase_pct': 20, 'house_pct': 3.0},
                {'no': 5, 'title': 'Mobilization & Site Setup', 'phase_pct': 15, 'house_pct': 2.25},
            ]
        },
        {
            'phase_number': 2,
            'title': 'Phase 2: Site & Foundation',
            'phase_weight': 20.0,
            'milestones': [
                {'no': 6, 'title': 'Excavation', 'phase_pct': 20, 'house_pct': 4.0},
                {'no': 7, 'title': 'Foundation Construction', 'phase_pct': 45, 'house_pct': 9.0},
                {'no': 8, 'title': 'Walling & Structural Frame', 'phase_pct': 20, 'house_pct': 4.0},
                {'no': 9, 'title': 'Roof Structure', 'phase_pct': 10, 'house_pct': 2.0},
                {'no': 10, 'title': 'Roofing (Lock-Up Stage)', 'phase_pct': 5, 'house_pct': 1.0},
            ]
        },
        {
            'phase_number': 3,
            'title': 'Phase 3: Structural Works',
            'phase_weight': 30.0,
            'milestones': [
                {'no': 11, 'title': 'Plumbing First Fix', 'phase_pct': 15, 'house_pct': 4.5},
                {'no': 12, 'title': 'Electrical First Fix', 'phase_pct': 15, 'house_pct': 4.5},
                {'no': 13, 'title': 'Mechanical/HVAC First Fix', 'phase_pct': 10, 'house_pct': 3.0},
                {'no': 14, 'title': 'Plastering & Screeding', 'phase_pct': 25, 'house_pct': 7.5},
                {'no': 15, 'title': 'Ceiling Installation', 'phase_pct': 15, 'house_pct': 4.5},
                {'no': 16, 'title': 'Tiling & Flooring', 'phase_pct': 20, 'house_pct': 6.0},
            ]
        },
        {
            'phase_number': 4,
            'title': 'Phase 4: Finishes & Services',
            'phase_weight': 25.0,
            'milestones': [
                {'no': 17, 'title': 'Joinery & Carpentry', 'phase_pct': 25, 'house_pct': 6.25},
                {'no': 18, 'title': 'Painting & Decorative Finishes', 'phase_pct': 25, 'house_pct': 6.25},
                {'no': 19, 'title': 'Plumbing Second Fix', 'phase_pct': 20, 'house_pct': 5.0},
                {'no': 20, 'title': 'Electrical Second Fix', 'phase_pct': 20, 'house_pct': 5.0},
                {'no': 21, 'title': 'External Development', 'phase_pct': 10, 'house_pct': 2.5},
            ]
        },
        {
            'phase_number': 5,
            'title': 'Phase 5: External Works & Handover',
            'phase_weight': 10.0,
            'milestones': [
                {'no': 22, 'title': 'Testing & Commissioning', 'phase_pct': 25, 'house_pct': 2.5},
                {'no': 23, 'title': 'Snagging / Punch List', 'phase_pct': 20, 'house_pct': 2.0},
                {'no': 24, 'title': 'Final Inspection & Occupancy Approval', 'phase_pct': 30, 'house_pct': 3.0},
                {'no': 25, 'title': 'Handover & Closeout', 'phase_pct': 25, 'house_pct': 2.5},
            ]
        }
    ]

    # Handle POST update of completed milestone checkboxes
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'save_milestones':
            completed_str_list = request.POST.getlist('completed_milestones')
            completed_ids = [int(m) for m in completed_str_list if m.isdigit()]
            
            # Recalculate total progress percentage from checked milestones
            total_earned = 0.0
            for phase in roadmap_phases_def:
                for m in phase['milestones']:
                    if m['no'] in completed_ids:
                        total_earned += m['house_pct']

            total_earned_round = round(total_earned, 1)
            project_obj.completed_milestones = completed_ids
            project_obj.progress_percentage = int(round(total_earned_round))
            
            # Also update video URL and supervisor name if provided
            if request.POST.get('video_url'):
                project_obj.video_url = request.POST.get('video_url').strip()
            if request.POST.get('supervisor_name'):
                project_obj.supervisor_name = request.POST.get('supervisor_name').strip()
            if request.POST.get('status'):
                project_obj.status = request.POST.get('status')
                
            project_obj.save()
            messages.success(request, f"Construction Roadmap updated! New Overall Completion Score: {total_earned_round:.1f}%")
            return redirect('admin_construction_progress', project_id=project_obj.id)

    # Initialize completed milestones if empty
    completed_ids = project_obj.completed_milestones
    if completed_ids is None or len(completed_ids) == 0:
        # Default first 13 milestones if new project to match ~52%
        completed_ids = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]
        project_obj.completed_milestones = completed_ids
        project_obj.progress_percentage = 52
        project_obj.save()

    # Calculate ratios for rendering
    total_score = 0.0
    phases_render = []
    for phase_def in roadmap_phases_def:
        earned_phase_weight = 0.0
        milestones_render = []
        for m in phase_def['milestones']:
            is_done = m['no'] in completed_ids
            if is_done:
                earned_phase_weight += m['house_pct']
            milestones_render.append({
                'no': m['no'],
                'title': m['title'],
                'phase_pct': m['phase_pct'],
                'house_pct': m['house_pct'],
                'is_completed': is_done,
            })

        earned_val = round(earned_phase_weight, 2)
        earned_disp = int(earned_val) if float(earned_val).is_integer() else earned_val
        weight_disp = int(phase_def['phase_weight']) if float(phase_def['phase_weight']).is_integer() else phase_def['phase_weight']
        
        phases_render.append({
            'phase_number': phase_def['phase_number'],
            'title': phase_def['title'],
            'phase_weight': phase_def['phase_weight'],
            'earned_display': earned_disp,
            'weight_display': weight_disp,
            'milestones': milestones_render,
        })
        total_score += earned_phase_weight

    overall_score = round(total_score, 1)

    return render(request, 'admin/construction_progress.html', {
        'project': project_obj,
        'app': app_obj,
        'phases': phases_render,
        'overall_score': overall_score,
        'completed_ids': completed_ids,
        'current_tab': 'construction'
    })


# --- CHATROOM VIEWS & APIS ---

def chat_agent_dashboard(request):
    agent_id = request.session.get('verified_chat_agent_id')
    agent = None
    if agent_id:
        try:
            agent = InspectionAgent.objects.get(id=agent_id)
        except InspectionAgent.DoesNotExist:
            pass

    if not agent:
        if request.user.is_superuser or (hasattr(request.user, 'profile') and request.user.profile.role == 'admin'):
            pass
        else:
            messages.error(request, "Please authenticate as a Chatroom Agent on the portal to access the workspace.")
            return redirect('agent_report_auth')

    open_threads = ChatThread.objects.filter(status='open').order_by('-updated_at')
    if agent:
        my_chats = ChatThread.objects.filter(assigned_agent=agent, status='active').order_by('-updated_at')
    else:
        my_chats = ChatThread.objects.filter(status='active').order_by('-updated_at')
        
    closed_chats = ChatThread.objects.filter(status='closed').order_by('-updated_at')[:20]

    context = {
        'agent': agent,
        'open_threads': open_threads,
        'my_chats': my_chats,
        'closed_chats': closed_chats,
    }
    return render(request, 'chat/agent_dashboard.html', context)


def chat_api_init(request):
    if not request.session.session_key:
        request.session.save()
    session_key = request.session.session_key

    thread = None
    if request.user.is_authenticated:
        guest_thread = ChatThread.objects.filter(session_key=session_key, status__in=['open', 'active']).first()
        if guest_thread:
            guest_thread.user = request.user
            guest_thread.save()

        thread = ChatThread.objects.filter(user=request.user, status__in=['open', 'active']).first()
    else:
        thread = ChatThread.objects.filter(session_key=session_key, status__in=['open', 'active']).first()

    if not thread:
        if request.user.is_authenticated:
            thread = ChatThread.objects.create(user=request.user, status='open')
        else:
            thread = ChatThread.objects.create(session_key=session_key, status='open')

    messages_qs = thread.messages.all().select_related('sender_user', 'sender_agent').order_by('timestamp')

    messages_data = []
    for msg in messages_qs:
        sender_name = "You"
        if msg.sender_type == 'agent':
            sender_name = msg.sender_agent.name if msg.sender_agent else "Trust Support Agent"
        elif msg.sender_type == 'system':
            sender_name = "System"
        elif msg.sender_type == 'client':
            if msg.sender_user:
                sender_name = msg.sender_user.username

        messages_data.append({
            'id': msg.id,
            'sender_type': msg.sender_type,
            'sender_name': sender_name,
            'message': msg.message,
            'timestamp': msg.timestamp.strftime('%H:%M'),
        })

    agent_data = None
    if thread.assigned_agent:
        agent_data = {
            'name': thread.assigned_agent.name,
            'image': thread.assigned_agent.image.url if thread.assigned_agent.image else None,
        }

    return JsonResponse({
        'status': 'success',
        'thread_id': thread.id,
        'thread_status': thread.status,
        'assigned_agent': agent_data,
        'messages': messages_data,
    })


@csrf_exempt
def chat_api_send(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'POST method required'}, status=400)

    import json
    data = {}
    if request.content_type == 'application/json':
        try:
            data = json.loads(request.body.decode('utf-8'))
        except Exception:
            pass
    else:
        data = request.POST

    thread_id = data.get('thread_id')
    message_text = data.get('message', '').strip()
    sender_type = data.get('sender_type', 'client')

    if not thread_id or not message_text:
        return JsonResponse({'status': 'error', 'message': 'Missing thread_id or message'}, status=400)

    thread = get_object_or_404(ChatThread, id=thread_id)

    sender_user = None
    sender_agent = None

    if sender_type == 'agent':
        agent_id = request.session.get('verified_chat_agent_id')
        if agent_id:
            try:
                sender_agent = InspectionAgent.objects.get(id=agent_id)
            except InspectionAgent.DoesNotExist:
                pass
        if not sender_agent and (request.user.is_superuser or (hasattr(request.user, 'profile') and request.user.profile.role == 'admin')):
            sender_agent = thread.assigned_agent

        if sender_agent:
            if thread.status == 'open' or not thread.assigned_agent:
                thread.assigned_agent = sender_agent
                thread.status = 'active'
                thread.save()
    else:
        sender_type = 'client'
        if request.user.is_authenticated:
            sender_user = request.user

    msg = ChatMessage.objects.create(
        thread=thread,
        sender_type=sender_type,
        sender_user=sender_user,
        sender_agent=sender_agent,
        message=message_text
    )

    thread.updated_at = msg.timestamp
    thread.save()

    sender_name = "You"
    if sender_type == 'agent':
        sender_name = sender_agent.name if sender_agent else "Trust Support Agent"
    elif sender_user:
        sender_name = sender_user.username

    return JsonResponse({
        'status': 'success',
        'message_id': msg.id,
        'timestamp': msg.timestamp.strftime('%H:%M'),
        'sender_name': sender_name
    })


def chat_api_poll(request):
    thread_id = request.GET.get('thread_id')
    last_id = request.GET.get('last_id', 0)

    try:
        last_id = int(last_id)
    except ValueError:
        last_id = 0

    if not thread_id:
        return JsonResponse({'status': 'error', 'message': 'Missing thread_id'}, status=400)

    thread = get_object_or_404(ChatThread, id=thread_id)
    new_msgs = thread.messages.filter(id__gt=last_id).select_related('sender_user', 'sender_agent').order_by('timestamp')

    messages_data = []
    for msg in new_msgs:
        sender_name = "You"
        if msg.sender_type == 'agent':
            sender_name = msg.sender_agent.name if msg.sender_agent else "Trust Support Agent"
        elif msg.sender_type == 'system':
            sender_name = "System"
        elif msg.sender_type == 'client' and msg.sender_user:
            sender_name = msg.sender_user.username

        messages_data.append({
            'id': msg.id,
            'sender_type': msg.sender_type,
            'sender_name': sender_name,
            'message': msg.message,
            'timestamp': msg.timestamp.strftime('%H:%M'),
        })

    agent_data = None
    if thread.assigned_agent:
        agent_data = {
            'name': thread.assigned_agent.name,
            'image': thread.assigned_agent.image.url if thread.assigned_agent.image else None,
        }

    return JsonResponse({
        'status': 'success',
        'thread_id': thread.id,
        'thread_status': thread.status,
        'assigned_agent': agent_data,
        'messages': messages_data
    })


@csrf_exempt
def chat_api_claim(request, thread_id):
    agent_id = request.session.get('verified_chat_agent_id')
    agent = None
    if agent_id:
        agent = InspectionAgent.objects.filter(id=agent_id).first()

    thread = get_object_or_404(ChatThread, id=thread_id)
    if agent:
        thread.assigned_agent = agent
        thread.status = 'active'
        thread.save()

        ChatMessage.objects.create(
            thread=thread,
            sender_type='system',
            message=f"Agent {agent.name} has joined the chat."
        )

    return JsonResponse({'status': 'success', 'thread_id': thread.id, 'status_display': thread.get_status_display()})


@csrf_exempt
def chat_api_close(request, thread_id):
    thread = get_object_or_404(ChatThread, id=thread_id)
    thread.status = 'closed'
    thread.save()

    ChatMessage.objects.create(
        thread=thread,
        sender_type='system',
        message="This chat session has been marked as closed."
    )

    return JsonResponse({'status': 'success', 'thread_id': thread.id})


def download_payments_pdf(request):
    if not request.user.is_authenticated or not request.user.is_superuser:
        messages.error(request, 'Access denied. Only system administrators can access this feature.')
        return redirect('login')

    try:
        from io import BytesIO
        from django.http import HttpResponse
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    except ImportError:
        messages.error(request, "PDF generation library (reportlab) is not installed on the server. Please run 'pip install reportlab'.")
        return redirect('admin_dashboard')

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=30
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        textColor=colors.HexColor('#0a5c36'),
        spaceAfter=6
    )
    subtitle_style = ParagraphStyle(
        'SubtitleStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        textColor=colors.HexColor('#64748b'),
        spaceAfter=15
    )
    th_style = ParagraphStyle(
        'THStyle',
        fontName='Helvetica-Bold',
        fontSize=8,
        textColor=colors.white,
        alignment=1
    )
    td_style = ParagraphStyle(
        'TDStyle',
        fontName='Helvetica',
        fontSize=8,
        textColor=colors.HexColor('#1e293b'),
        alignment=0
    )

    elements = []

    # Title & Header
    elements.append(Paragraph("TRUST Real Estate Portal - Received Payments & Escrow Ledger", title_style))
    elements.append(Paragraph(f"Official Financial Accountability Report | Generated: {timezone.now().strftime('%B %d, %Y - %H:%M')}", subtitle_style))
    elements.append(Spacer(1, 10))

    # Fetch received payments data with month/day filter support
    filter_month = request.GET.get('filter_month', '')
    filter_day = request.GET.get('filter_day', '')

    received_bookings = TenantBooking.objects.filter(booking_fee__gt=0).select_related('tenant', 'property').order_by('-booked_at')
    received_rentals = TenantRental.objects.select_related('tenant', 'property').order_by('-created_at', '-start_date')

    if filter_month:
        try:
            m_val = int(filter_month)
            received_bookings = received_bookings.filter(booked_at__month=m_val)
            received_rentals = received_rentals.filter(Q(created_at__month=m_val) | Q(start_date__month=m_val))
        except ValueError:
            pass

    if filter_day:
        try:
            d_val = int(filter_day)
            received_bookings = received_bookings.filter(booked_at__day=d_val)
            received_rentals = received_rentals.filter(Q(created_at__day=d_val) | Q(start_date__day=d_val))
        except ValueError:
            pass

    payments_list = []
    total_booking_revenue = 0
    total_rent_2_revenue = 0
    rent_2_count = 0
    total_rent_3_revenue = 0
    rent_3_count = 0

    for b in received_bookings:
        amount = float(b.booking_fee or 0)
        total_booking_revenue += amount
        payments_list.append([
            f"BKG-{b.id:04d}",
            f"{b.tenant.first_name} {b.tenant.last_name or b.tenant.username}",
            b.property.title[:22],
            "24h Booking Fee (5%)",
            b.payment_method or "Mobile Money",
            f"UGX {amount:,.0f}",
            b.booked_at.strftime('%Y-%m-%d') if b.booked_at else "-",
            b.get_status_display()
        ])

    for r in received_rentals:
        amount = float(r.total_amount) if r.total_amount and float(r.total_amount) > 0 else (float(r.property.price or 0) * (3 if r.payment_type == 'rent_3' else 2) * 1.11)
        if r.payment_type == 'rent_3':
            total_rent_3_revenue += amount
            rent_3_count += 1
            cat = "Pay 3 Months Rent"
        else:
            total_rent_2_revenue += amount
            rent_2_count += 1
            cat = "Pay 2 Months Rent"

        r_date = r.created_at or r.start_date
        payments_list.append([
            f"RNT-{r.id:04d}",
            f"{r.tenant.first_name} {r.tenant.last_name or r.tenant.username}",
            r.property.title[:22],
            cat,
            r.payment_method or "Mobile Money",
            f"UGX {amount:,.0f}",
            r_date.strftime('%Y-%m-%d') if r_date else "-",
            "Escrow Secured" if r.status == 'active' else "Completed"
        ])

    grand_total = total_booking_revenue + total_rent_2_revenue + total_rent_3_revenue

    # Summary Table
    summary_data = [
        [Paragraph("Payment Category", th_style), Paragraph("Transactions", th_style), Paragraph("Total Amount (UGX)", th_style)],
        [Paragraph("24-Hour Booking Lock Fees", td_style), Paragraph(str(len(received_bookings)), td_style), Paragraph(f"UGX {total_booking_revenue:,.0f}", td_style)],
        [Paragraph("Pay 2 Months Rent Payments", td_style), Paragraph(str(rent_2_count), td_style), Paragraph(f"UGX {total_rent_2_revenue:,.0f}", td_style)],
        [Paragraph("Pay 3 Months Rent Payments", td_style), Paragraph(str(rent_3_count), td_style), Paragraph(f"UGX {total_rent_3_revenue:,.0f}", td_style)],
        [Paragraph("GRAND TOTAL ESCROW REVENUE", ParagraphStyle('B', parent=td_style, fontName='Helvetica-Bold')), Paragraph(str(len(payments_list)), ParagraphStyle('B', parent=td_style, fontName='Helvetica-Bold')), Paragraph(f"UGX {grand_total:,.0f}", ParagraphStyle('B', parent=td_style, fontName='Helvetica-Bold', textColor=colors.HexColor('#0a5c36')))]
    ]

    summary_table = Table(summary_data, colWidths=[220, 100, 200])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0a5c36')),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor('#f1f5f9')),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 15))

    # Transactions Ledger Table
    elements.append(Paragraph("Detailed Transactions Ledger", ParagraphStyle('H2', parent=styles['Heading2'], fontName='Helvetica-Bold', fontSize=12, textColor=colors.HexColor('#0a5c36'))))
    elements.append(Spacer(1, 6))

    table_data = [[
        Paragraph("Ref ID", th_style),
        Paragraph("Tenant", th_style),
        Paragraph("Property Unit", th_style),
        Paragraph("Category", th_style),
        Paragraph("Gateway", th_style),
        Paragraph("Amount", th_style),
        Paragraph("Date", th_style),
        Paragraph("Status", th_style)
    ]]

    for p in payments_list:
        table_data.append([
            Paragraph(p[0], td_style),
            Paragraph(p[1], td_style),
            Paragraph(p[2], td_style),
            Paragraph(p[3], td_style),
            Paragraph(p[4], td_style),
            Paragraph(p[5], td_style),
            Paragraph(p[6], td_style),
            Paragraph(p[7], td_style)
        ])

    ledger_table = Table(table_data, colWidths=[55, 80, 100, 85, 65, 75, 55, 60])
    ledger_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0a5c36')),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
    ]))
    elements.append(ledger_table)

    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="TRUST_Payments_Ledger_{timezone.now().strftime("%Y%m%d")}.pdf"'
    response.write(pdf)
    return response


def projects_list_view(request):
    """
    Renders running construction projects supervised by TRUST Protocol.
    """
    from core.models import ConstructionProject, PopupLogic
    projects = ConstructionProject.objects.all().order_by('-created_at')
    active_popup = PopupLogic.objects.filter(is_active=True, display_page__in=['search', 'all'], trigger_event='load').first()

    return render(request, 'tenant/projects.html', {
        'projects': projects,
        'active_popup': active_popup
    })


def project_detail_view(request, project_id):
    """
    Redirects user directly to the Client Construction Supervision Dashboard for an ongoing project.
    """
    from django.shortcuts import redirect
    return redirect('client_construction_dashboard_detail', app_id=project_id)


from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def diaspora_application_submit_view(request):
    """
    Handles form submission from Diaspora clients requesting construction building or supervision.
    Collects minimum required TRUST Protocol fields:
    - Full Name, Passport/ID, Country of Residence, Email, Phone
    - Land Ownership Proof, Location (District, Sub-County, Village)
    - Building Plans/Concept, Budget Range, Preferred Timeline
    - Next of Kin in Uganda (Name, Relationship, Phone, District)
    - Payment Method
    """
    if request.method == 'POST':
        from core.models import DiasporaClientApplication
        from django.http import JsonResponse

        try:
            full_name = request.POST.get('full_name', '').strip()
            passport_or_id = request.POST.get('passport_or_id', '').strip()
            country_of_residence = request.POST.get('country_of_residence', '').strip()
            email = request.POST.get('email', '').strip()
            phone_number = request.POST.get('phone_number', '').strip()

            owns_land = request.POST.get('owns_land', 'yes').strip().lower()
            district = request.POST.get('district', '').strip()
            sub_county = request.POST.get('sub_county', '').strip()
            village = request.POST.get('village', '').strip()

            desired_land_size = request.POST.get('desired_land_size', '').strip()
            desired_land_type = request.POST.get('desired_land_type', '').strip()
            land_budget_range = request.POST.get('land_budget_range', '').strip()

            building_concept_notes = request.POST.get('building_concept_notes', '').strip()
            budget_range = request.POST.get('budget_range', '').strip()
            construction_budget_range = request.POST.get('construction_budget_range', '').strip()
            preferred_timeline = request.POST.get('preferred_timeline', '').strip()

            next_of_kin_name = request.POST.get('next_of_kin_name', '').strip()
            next_of_kin_relationship = request.POST.get('next_of_kin_relationship', '').strip()
            next_of_kin_phone = request.POST.get('next_of_kin_phone', '').strip()
            next_of_kin_district = request.POST.get('next_of_kin_district', '').strip()

            payment_method = request.POST.get('payment_method', 'swift').strip()

            # Files
            id_document = request.FILES.get('id_document')
            applicant_photo = request.FILES.get('applicant_photo')
            land_proof = request.FILES.get('land_proof')
            building_plans = request.FILES.get('building_plans')

            if not full_name or not passport_or_id or not country_of_residence or not email or not phone_number or not district or not next_of_kin_name:
                return JsonResponse({'success': False, 'error': 'Please fill in all required fields marked with *.'}, status=400)

            app = DiasporaClientApplication.objects.create(
                full_name=full_name,
                passport_or_id=passport_or_id,
                id_document=id_document,
                applicant_photo=applicant_photo,
                country_of_residence=country_of_residence,
                email=email,
                phone_number=phone_number,
                owns_land=owns_land,
                land_proof=land_proof,
                district=district,
                sub_county=sub_county,
                village=village,
                desired_land_size=desired_land_size,
                desired_land_type=desired_land_type,
                land_budget_range=land_budget_range,
                building_plans=building_plans,
                building_concept_notes=building_concept_notes,
                budget_range=budget_range,
                construction_budget_range=construction_budget_range,
                preferred_timeline=preferred_timeline,
                next_of_kin_name=next_of_kin_name,
                next_of_kin_relationship=next_of_kin_relationship,
                next_of_kin_phone=next_of_kin_phone,
                next_of_kin_district=next_of_kin_district,
                payment_method=payment_method,
                status='pending'
            )

            return JsonResponse({
                'success': True,
                'message': f'Thank you {full_name}! Your TRUST Construction Application (Ref: #TRUST-DSP-{app.id:04d}) has been submitted successfully. A TRUST Protocol engineering officer will contact you via email ({email}) within 24 hours.',
                'application_id': app.id
            })

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)


def client_construction_dashboard(request, app_id=None):
    """
    Renders the dedicated Client Construction Supervision Dashboard to follow up on real estate assignments.
    Calculates exact overall project completion based on a 5-Phase / 25-Milestone Weighted Roadmap:
    - Phase 1: Planning & Design (15%)
    - Phase 2: Site & Foundation (20%)
    - Phase 3: Structural Works (30%)
    - Phase 4: Finishes & Services (25%)
    - Phase 5: External Works & Handover (10%)
    """
    from core.models import DiasporaClientApplication, ConstructionProject
    
    app = None
    project_obj = None

    if app_id:
        try:
            project_obj = ConstructionProject.objects.get(id=app_id)
        except ConstructionProject.DoesNotExist:
            pass

        try:
            app = DiasporaClientApplication.objects.get(id=app_id)
        except DiasporaClientApplication.DoesNotExist:
            pass

    if not app:
        app = DiasporaClientApplication.objects.first()

    if not project_obj:
        project_obj = ConstructionProject.objects.first()

    # Standard 5-Phase / 25-Milestone Construction Roadmap Engine
    roadmap_phases = [
        {
            'phase_number': 1,
            'title': 'Phase 1: Planning & Design',
            'phase_weight': 15.0,
            'milestones': [
                {'no': 1, 'title': 'Project Initiation', 'phase_pct': 20, 'house_pct': 3.0, 'status': 'completed', 'verified_by': 'TRUST Project Initiation Unit'},
                {'no': 2, 'title': 'Surveying & Site Investigation', 'phase_pct': 15, 'house_pct': 2.25, 'status': 'completed', 'verified_by': 'Registered Surveyor'},
                {'no': 3, 'title': 'Architectural & Engineering Design', 'phase_pct': 30, 'house_pct': 4.5, 'status': 'completed', 'verified_by': 'Lead Architect & Engineer'},
                {'no': 4, 'title': 'Approvals & Permits', 'phase_pct': 20, 'house_pct': 3.0, 'status': 'completed', 'verified_by': 'Physical Planning Board'},
                {'no': 5, 'title': 'Mobilization & Site Setup', 'phase_pct': 15, 'house_pct': 2.25, 'status': 'completed', 'verified_by': 'Site Supervisor'},
            ]
        },
        {
            'phase_number': 2,
            'title': 'Phase 2: Site & Foundation',
            'phase_weight': 20.0,
            'milestones': [
                {'no': 6, 'title': 'Excavation', 'phase_pct': 20, 'house_pct': 4.0, 'status': 'completed', 'verified_by': 'Earthworks Engineer'},
                {'no': 7, 'title': 'Foundation Construction', 'phase_pct': 45, 'house_pct': 9.0, 'status': 'completed', 'verified_by': 'Eng. Patrick Mukasa'},
                {'no': 8, 'title': 'Walling & Structural Frame', 'phase_pct': 20, 'house_pct': 4.0, 'status': 'completed', 'verified_by': 'TRUST Engineering Unit'},
                {'no': 9, 'title': 'Roof Structure', 'phase_pct': 10, 'house_pct': 2.0, 'status': 'completed', 'verified_by': 'Structural Engineer'},
                {'no': 10, 'title': 'Roofing (Lock-Up Stage)', 'phase_pct': 5, 'house_pct': 1.0, 'status': 'completed', 'verified_by': 'Roofing Specialist'},
            ]
        },
        {
            'phase_number': 3,
            'title': 'Phase 3: Structural Works',
            'phase_weight': 30.0,
            'milestones': [
                {'no': 11, 'title': 'Plumbing First Fix', 'phase_pct': 15, 'house_pct': 4.5, 'status': 'completed', 'verified_by': 'Plumbing Engineer'},
                {'no': 12, 'title': 'Electrical First Fix', 'phase_pct': 15, 'house_pct': 4.5, 'status': 'completed', 'verified_by': 'Electrical Engineer'},
                {'no': 13, 'title': 'Mechanical/HVAC First Fix', 'phase_pct': 10, 'house_pct': 3.0, 'status': 'completed', 'verified_by': 'Services Inspector'},
                {'no': 14, 'title': 'Plastering & Screeding', 'phase_pct': 25, 'house_pct': 7.5, 'status': 'in_progress', 'earned_house_pct': 5.0, 'verified_by': 'Finishes Inspector'},
                {'no': 15, 'title': 'Ceiling Installation', 'phase_pct': 15, 'house_pct': 4.5, 'status': 'pending', 'verified_by': 'Pending'},
                {'no': 16, 'title': 'Tiling & Flooring', 'phase_pct': 20, 'house_pct': 6.0, 'status': 'pending', 'verified_by': 'Pending'},
            ]
        },
        {
            'phase_number': 4,
            'title': 'Phase 4: Finishes & Services',
            'phase_weight': 25.0,
            'milestones': [
                {'no': 17, 'title': 'Joinery & Carpentry', 'phase_pct': 25, 'house_pct': 6.25, 'status': 'pending', 'verified_by': 'Upcoming Stage'},
                {'no': 18, 'title': 'Painting & Decorative Finishes', 'phase_pct': 25, 'house_pct': 6.25, 'status': 'pending', 'verified_by': 'Upcoming Stage'},
                {'no': 19, 'title': 'Plumbing Second Fix', 'phase_pct': 20, 'house_pct': 5.0, 'status': 'pending', 'verified_by': 'Upcoming Stage'},
                {'no': 20, 'title': 'Electrical Second Fix', 'phase_pct': 20, 'house_pct': 5.0, 'status': 'pending', 'verified_by': 'Upcoming Stage'},
                {'no': 21, 'title': 'External Development', 'phase_pct': 10, 'house_pct': 2.5, 'status': 'pending', 'verified_by': 'Upcoming Stage'},
            ]
        },
        {
            'phase_number': 5,
            'title': 'Phase 5: External Works & Handover',
            'phase_weight': 10.0,
            'milestones': [
                {'no': 22, 'title': 'Testing & Commissioning', 'phase_pct': 25, 'house_pct': 2.5, 'status': 'pending', 'verified_by': 'Upcoming Stage'},
                {'no': 23, 'title': 'Snagging / Punch List', 'phase_pct': 20, 'house_pct': 2.0, 'status': 'pending', 'verified_by': 'Upcoming Stage'},
                {'no': 24, 'title': 'Final Inspection & Occupancy Approval', 'phase_pct': 30, 'house_pct': 3.0, 'status': 'pending', 'verified_by': 'Upcoming Stage'},
                {'no': 25, 'title': 'Handover & Closeout', 'phase_pct': 25, 'house_pct': 2.5, 'status': 'pending', 'verified_by': 'Upcoming Stage'},
            ]
        }
    ]

    # Calculate exact phase completion percentages & overall house completion score
    completed_ids = project_obj.completed_milestones if (project_obj and project_obj.completed_milestones) else None

    total_house_completion = 0.0
    for phase in roadmap_phases:
        earned_phase_weight = 0.0
        for m in phase['milestones']:
            if completed_ids is not None:
                if m['no'] in completed_ids:
                    m['status'] = 'completed'
                else:
                    m['status'] = 'pending'

            if m.get('status') == 'completed':
                earned_phase_weight += m['house_pct']
            elif m.get('status') == 'in_progress':
                earned = m.get('earned_house_pct', m['house_pct'] * 0.5)
                earned_phase_weight += earned
        
        earned_val = round(earned_phase_weight, 2)
        phase['earned_house_pct'] = earned_val
        phase['earned_display'] = int(earned_val) if float(earned_val).is_integer() else earned_val
        phase['weight_display'] = int(phase['phase_weight']) if float(phase['phase_weight']).is_integer() else phase['phase_weight']
        phase['fill_pct'] = round((earned_phase_weight / phase['phase_weight']) * 100, 1)
        total_house_completion += earned_phase_weight

    overall_completion_pct = round(total_house_completion, 1)

    # Site updates timeline
    site_updates = [
        {
            'date': 'Today, 09:30 AM',
            'title': 'Plastering & Wall Screeding Inspection (Milestone 14)',
            'description': 'Internal wall plastering verified at 70% completion. Mortar mix ratio 1:4 confirmed compliant with structural specs.',
            'category': 'Quality Test',
            'author': 'Eng. Patrick Mukasa'
        },
        {
            'date': 'Yesterday, 04:15 PM',
            'title': 'Plumbing & Electrical First Fix Sign-Off (Milestones 11 & 12)',
            'description': 'Concealed PPR plumbing pressure testing held at 10 bar for 2 hours with zero drop. Electrical conduit runs approved.',
            'category': 'Inspection Sign-off',
            'author': 'TRUST Engineering Inspector'
        },
        {
            'date': '10 Aug 2026',
            'title': 'Phase 2 Completion Escrow Release',
            'description': 'Full Phase 2 (Site & Foundation - 20% house contribution) milestone verified and escrow payment released to contractor.',
            'category': 'Payment Release',
            'author': 'TRUST Financial Auditor'
        }
    ]

    # Site Photo Gallery
    photos = [
        {'url': 'https://images.unsplash.com/photo-1541888946425-d0fbb186a5b3?auto=format&fit=crop&w=800&q=80', 'caption': 'Milestone 14: Internal Wall Plastering & Screeding', 'date': '14 Aug 2026'},
        {'url': 'https://images.unsplash.com/photo-1503387762-592deb58ef4e?auto=format&fit=crop&w=800&q=80', 'caption': 'Milestones 11 & 12: Electrical Conduit & Plumbing First Fix', 'date': '12 Aug 2026'},
        {'url': 'https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=800&q=80', 'caption': 'Milestone 10: Roof Cover & Waterproof Lock-Up', 'date': '05 Aug 2026'},
        {'url': 'https://images.unsplash.com/photo-1512917774080-9991f1c4c750?auto=format&fit=crop&w=800&q=80', 'caption': 'Milestone 7: Reinforced Concrete Foundation Sign-Off', 'date': '20 Jul 2026'},
    ]

    # Video Clips
    videos = [
        {'title': 'Drone Flyover: Lock-Up & Plastering Phase Walkthrough', 'date': '13 Aug 2026', 'duration': '1m 45s', 'poster': 'https://images.unsplash.com/photo-1541888946425-d0fbb186a5b3?auto=format&fit=crop&w=800&q=80'},
        {'title': 'Hydrostatic Plumbing Pressure Test Video', 'date': '11 Aug 2026', 'duration': '0m 58s', 'poster': 'https://images.unsplash.com/photo-1503387762-592deb58ef4e?auto=format&fit=crop&w=800&q=80'}
    ]

    # Payment / Escrow Status
    payment_status = {
        'total_budget': 'UGX 220,000,000',
        'escrow_deposited': 'UGX 150,000,000',
        'disbursed': 'UGX 88,000,000',
        'escrow_balance': 'UGX 62,000,000',
        'next_milestone_payment': 'UGX 33,000,000 (Upon Phase 3 Structural Sign-Off)',
        'payment_method': app.get_payment_method_display() if app else 'SWIFT International Wire Transfer'
    }

    # Contract Status
    contract_status = {
        'agreement_no': f"TRUST-AGR-2026-{(app.id if app else 1):04d}",
        'status': 'Active & Escrow Protected',
        'start_date': '15 July 2026',
        'expected_handover': '28 February 2027',
        'legal_representative': 'TRUST Legal & Supervisory Bureau'
    }

    # Verification Reports
    verification_reports = [
        {'title': 'Phase 1 Sign-Off: Architectural, Engineering & Permit Approvals Certificate', 'ref': 'REP-P1-109', 'date': '18 Jul 2026', 'status': 'Verified & Sealed'},
        {'title': 'Phase 2 Sign-Off: Substructure Foundation & Concrete Compression Report', 'ref': 'REP-P2-204', 'date': '06 Aug 2026', 'status': 'Verified & Sealed'},
        {'title': 'Milestone 11 & 12: Plumbing & Electrical First Fix Inspection Report', 'ref': 'REP-M11-312', 'date': '12 Aug 2026', 'status': 'Verified & Sealed'},
    ]

    return render(request, 'tenant/construction_dashboard.html', {
        'app': app,
        'project_obj': project_obj,
        'roadmap_phases': roadmap_phases,
        'overall_completion_pct': overall_completion_pct,
        'site_updates': site_updates,
        'photos': photos,
        'videos': videos,
        'payment_status': payment_status,
        'contract_status': contract_status,
        'verification_reports': verification_reports,
    })
