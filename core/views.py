from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login
from django.contrib import messages
from core.models import Property, UserProfile, AgentRole, InspectionAgent, Inspection, InspectionReport
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
            agent_role_id = request.POST.get('agent_role_id')
            agent_image = request.FILES.get('agent_image')
            
            if agent_name and agent_email and agent_phone:
                try:
                    role_obj = None
                    if agent_role_id:
                        role_obj = AgentRole.objects.get(id=agent_role_id)
                    InspectionAgent.objects.create(
                        name=agent_name,
                        email=agent_email,
                        phone=agent_phone,
                        role=role_obj,
                        image=agent_image
                    )
                    messages.success(request, f"Inspection Agent '{agent_name}' has been registered successfully!")
                except Exception as e:
                    messages.error(request, f"Error registering agent: An agent with this email might already exist.")
            else:
                messages.error(request, "Name, Email, and Phone number are required to register an agent.")
            return redirect('/admin-dashboard/?tab=agents')

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
        
        property_obj = Property(
            owner=request.user,
            title=title,
            category=category,
            parent=parent,
            location=location,
            is_multi_unit=is_multi_unit,
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
        messages.success(request, f"Property '{title}' was submitted successfully and is now pending manual security vetting by the TRUST board!")
        return redirect('landlord_dashboard')
        
    buildings = Property.objects.filter(is_multi_unit=True)
    return render(request, 'landlord/add_property.html', {'buildings': buildings})

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
            
        return render(request, 'admin/property_detail.html', {
            'property': property_obj,
            'inspection': inspection,
            'reports': reports
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
    # Fetch parent (standalone or building) properties that are approved/available
    properties = Property.objects.filter(parent=None).prefetch_related('units')
    return render(request, 'index.html', {'properties': properties})

def agent_report_auth(request):
    if request.method == 'POST':
        agent_id = request.POST.get('agent_id', '').strip()
        phone = request.POST.get('phone', '').strip()
        email = request.POST.get('email', '').strip()
        
        agent = InspectionAgent.objects.filter(
            agent_id__iexact=agent_id,
            phone=phone,
            email__iexact=email
        ).select_related('role').first()
        
        if agent:
            request.session['verified_agent_id'] = agent.id
            messages.success(request, f"Welcome back, Inspector {agent.name}! Credentials successfully verified.")
            return redirect('agent_submit_report')
        else:
            messages.error(request, "Access Denied: Invalid Agent credentials. Please verify your ID, Phone, and Email address.")
            
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
