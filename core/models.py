from django.db import models
from django.contrib.auth.models import User

class Property(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='properties', null=True, blank=True)
    SINGLE_UNIT_CHOICES = [
        ('single_room', 'Single Room'),
        ('self_contained', 'Self-Contained Room'),
        ('studio', 'Studio Apartment'),
        ('1_bed', '1 Bedroom Apartment'),
        ('2_bed', '2 Bedroom Apartment'),
        ('3_plus_bed', '3+ Bedroom Apartment'),
        ('bungalow', 'Bungalow'),
        ('standalone', 'Standalone House'),
    ]
    MULTI_UNIT_CHOICES = [
        ('apartment_block', 'Apartment Block'),
        ('condo_block', 'Condominium Block'),
        ('flat', 'Flat (Multi-Floor Building)'),
    ]
    CATEGORY_CHOICES = SINGLE_UNIT_CHOICES + MULTI_UNIT_CHOICES

    STATUS_CHOICES = [
        ('available', 'Available'),
        ('rented', 'Rented'),
        ('under_maintenance', 'Under Maintenance'),
        ('pending_verification', 'Pending Verification'),
        ('under_inspection', 'Under Inspection'),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending_verification')
    price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    price_per_month = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    price_per_year = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    location = models.CharField(max_length=255)
    latitude = models.FloatField(null=True, blank=True, help_text="Latitude coordinate (e.g. 0.3476)")
    longitude = models.FloatField(null=True, blank=True, help_text="Longitude coordinate (e.g. 32.5825)")
    
    # Parent-Child relationship
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='units')
    
    is_multi_unit = models.BooleanField(default=False)
    bedrooms = models.IntegerField(null=True, blank=True)
    
    # Images (Hero + 3 Gallery supporting photos)
    hero_image = models.FileField(upload_to='properties/hero/', null=True, blank=True)
    image_1 = models.FileField(upload_to='properties/gallery/', null=True, blank=True)
    image_2 = models.FileField(upload_to='properties/gallery/', null=True, blank=True)
    image_3 = models.FileField(upload_to='properties/gallery/', null=True, blank=True)

    # Documents
    building_plans = models.FileField(upload_to='properties/documents/', null=True, blank=True)
    occupancy_permit = models.FileField(upload_to='properties/documents/', null=True, blank=True)
    lc1_letter = models.FileField(upload_to='properties/documents/', null=True, blank=True)
    tenancy_agreement = models.FileField(upload_to='properties/documents/', null=True, blank=True)
    security_agreement = models.FileField(upload_to='properties/documents/', null=True, blank=True)
    
    amenities = models.ManyToManyField('PropertyAmenity', blank=True, related_name='properties')
    property_id = models.CharField(max_length=50, unique=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def is_available(self):
        if self.is_multi_unit:
            # For multi-unit buildings, availability is based on children
            return self.units.filter(status='available').exists()
        return self.status == 'available'

    def __str__(self):
        if self.parent:
            return f"{self.title} (Unit in {self.parent.title})"
        return self.title

    def save(self, *args, **kwargs):
        if not self.property_id:
            import random
            while True:
                code = str(random.randint(100000, 999999))
                if not Property.objects.filter(property_id=code).exists():
                    self.property_id = code
                    break
        super().save(*args, **kwargs)

    class Meta:
        verbose_name_plural = "Properties"

class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('tenant', 'Tenant'),
        ('landlord', 'Landlord'),
        ('admin', 'Admin'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    phone = models.CharField(max_length=50, blank=True)
    nin = models.CharField(max_length=100, blank=True)
    is_approved = models.BooleanField(default=False)
    
    # Expanded Tenant Profile fields
    phone_2 = models.CharField(max_length=50, blank=True, null=True)
    image = models.FileField(upload_to='profiles/', blank=True, null=True)
    profession = models.CharField(max_length=100, blank=True, null=True)
    place_of_work = models.CharField(max_length=100, blank=True, null=True)
    marriage_status = models.CharField(max_length=50, blank=True, null=True)
    number_of_children = models.IntegerField(default=0, blank=True, null=True)
    emergency_conditions = models.TextField(blank=True, null=True)
    doctor_contact = models.CharField(max_length=100, blank=True, null=True)
    national_id_or_passport = models.FileField(upload_to='documents/identity/', blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} ({self.role})"

class AgentRole(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class InspectionAgent(models.Model):
    name = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=50)
    role = models.ForeignKey(AgentRole, on_delete=models.SET_NULL, null=True, blank=True, related_name='agents')
    image = models.FileField(upload_to='agents/', null=True, blank=True)
    agent_id = models.CharField(max_length=50, unique=True, null=True, blank=True)
    joined_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.agent_id:
            import random
            while True:
                code = str(random.randint(100000, 999999))
                if not InspectionAgent.objects.filter(agent_id=code).exists():
                    self.agent_id = code
                    break
        super().save(*args, **kwargs)

class Inspection(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending Inspection'),
        ('in_progress', 'Inspection in Progress'),
        ('completed', 'Inspection Completed'),
    ]
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='inspections')
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='in_progress')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Inspection for {self.property.title} ({self.get_status_display()})"

class InspectionReport(models.Model):
    STATUS_CHOICES = [
        ('approved', 'Approved / Safe'),
        ('flagged', 'Flagged / Minor Concerns'),
        ('rejected', 'Rejected / Unsafe'),
    ]
    inspection = models.ForeignKey(Inspection, on_delete=models.CASCADE, related_name='reports')
    agent = models.ForeignKey(InspectionAgent, on_delete=models.SET_NULL, null=True, blank=True, related_name='reports')
    findings = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='approved')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Report by {self.agent.name if self.agent else 'Unknown'} for {self.inspection.property.title}"

class PropertyAmenity(models.Model):
    LAYER_CHOICES = [
        ('core', 'Core Details'),
        ('verification', 'Verification Details'),
        ('luxury', 'Luxury/Optional Amenities'),
        ('indoor', 'Indoor Amenities'),
        ('utilities', 'Utilities & Infrastructure'),
        ('security', 'Security Features'),
        ('outdoor', 'Outdoor Amenities'),
        ('building', 'Building Features'),
        ('location', 'Location & Convenience'),
        ('rental', 'Rental & Management Features'),
        ('commercial', 'Land & Commercial Property Features'),
    ]
    name = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=100) # e.g. "Indoor", "Utilities", "Security", etc.
    layer = models.CharField(max_length=50, choices=LAYER_CHOICES, default='luxury')
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.get_layer_display()})"

class ProximityCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class ProximityItem(models.Model):
    category = models.ForeignKey(ProximityCategory, on_delete=models.CASCADE, related_name='items')
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} in {self.category.name}"

class PropertyProximity(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='proximities')
    item = models.ForeignKey(ProximityItem, on_delete=models.CASCADE)
    distance_km = models.DecimalField(max_digits=5, decimal_places=2) # e.g. 1.25 KM
    
    class Meta:
        unique_together = ('property', 'item')
        
    def __str__(self):
        return f"{self.item.name} is {self.distance_km} KM from {self.property.title}"

# --- NEW TENANT DASHBOARD MODELS ---

class TenantBooking(models.Model):
    tenant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='bookings')
    booked_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=20, 
        choices=[('reserved', 'Reserved'), ('active', 'Active'), ('expired', 'Expired'), ('paid_rent', 'Paid Rent & Finalized')], 
        default='reserved'
    )
    booking_fee = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    payment_method = models.CharField(max_length=50, blank=True, null=True)
    
    def is_expired(self):
        from django.utils import timezone
        if not self.expires_at:
            return False
        return timezone.now() > self.expires_at and self.status == 'active'

    def __str__(self):
        return f"Booking for {self.property.title} by {self.tenant.username}"

class TenantRental(models.Model):
    tenant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rentals')
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='rentals')
    start_date = models.DateField(auto_now_add=True)
    move_in_date = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=20, 
        choices=[('active', 'Active'), ('terminated', 'Terminated')], 
        default='active'
    )
    signed_agreement = models.FileField(upload_to='agreements/signed/', null=True, blank=True)
    co_occupants_image = models.FileField(upload_to='occupants/', null=True, blank=True)
    
    def __str__(self):
        return f"Rental of {self.property.title} by {self.tenant.username}"

class ViewingRequest(models.Model):
    tenant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='viewing_requests')
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='viewing_requests')
    preferred_date = models.DateTimeField()
    status = models.CharField(
        max_length=20, 
        choices=[('pending', 'Pending Review'), ('approved', 'Approved'), ('declined', 'Declined')], 
        default='pending'
    )
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Viewing for {self.property.title} requested by {self.tenant.username}"

class MaintenanceRequest(models.Model):
    tenant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='maintenance_requests')
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='maintenance_requests')
    issue_description = models.TextField()
    category = models.CharField(max_length=100) # Plumbing, Electrical, Structural, Security, Other
    reported_to = models.CharField(
        max_length=20, 
        choices=[('landlord', 'Landlord'), ('agent', 'Trust Agent')], 
        default='landlord'
    )
    status = models.CharField(
        max_length=20, 
        choices=[('pending', 'Pending'), ('in_progress', 'In Progress'), ('resolved', 'Resolved')], 
        default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Maintenance for {self.property.title} reported to {self.reported_to}"

class FavoriteProperty(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorite_properties')
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'property')
        verbose_name_plural = 'Favorite Properties'

    def __str__(self):
        return f"{self.user.username} favorited {self.property.title}"


class CommitteeExecutive(models.Model):
    name = models.CharField(max_length=150)
    role = models.CharField(max_length=150)
    image = models.FileField(upload_to='committee/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.role}"


class ServiceDistrict(models.Model):
    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class ServiceDivision(models.Model):
    district = models.ForeignKey(ServiceDistrict, on_delete=models.CASCADE, related_name='divisions')
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('district', 'name')

    def __str__(self):
        return f"{self.name} ({self.district.name})"

class ServiceVillage(models.Model):
    division = models.ForeignKey(ServiceDivision, on_delete=models.CASCADE, related_name='villages')
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('division', 'name')

    def __str__(self):
        return f"{self.name} ({self.division.name})"


class PopupLogic(models.Model):
    PAGE_CHOICES = [
        ('search', 'Find a Property (Search Page)'),
        ('tenant_dashboard', 'Tenant Dashboard'),
        ('all', 'All Pages'),
    ]
    
    TRIGGER_CHOICES = [
        ('load', 'On Page Load'),
        ('payment_success', 'After Payment Completed (Redirect Trigger)'),
    ]
    
    POPUP_TYPE_CHOICES = [
        ('marketing', 'Marketing & Promotion'),
        ('logistics', 'Logistics / Booking Flow'),
    ]

    title = models.CharField(max_length=200)
    popup_type = models.CharField(max_length=20, choices=POPUP_TYPE_CHOICES, default='marketing')
    display_page = models.CharField(max_length=50, choices=PAGE_CHOICES, default='search')
    trigger_event = models.CharField(max_length=50, choices=TRIGGER_CHOICES, default='load')
    content = models.TextField(help_text="HTML/Text description of the offer or logistical guidelines")
    image = models.FileField(upload_to='popups/', null=True, blank=True, help_text="Popup hero graphic or icon")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_popup_type_display()} - {self.title}"


class SiteSetting(models.Model):
    site_name = models.CharField(max_length=100, default='TRUST')
    site_icon = models.FileField(upload_to='site_settings/', null=True, blank=True, help_text="Favicon / Tab icon")
    site_logo = models.FileField(upload_to='site_settings/', null=True, blank=True, help_text="Top header logo replacement for 'Shield and TRUST'")

    def __str__(self):
        return "Site Settings"

    class Meta:
        verbose_name = "Site Setting"
        verbose_name_plural = "Site Settings"


class ChatThread(models.Model):
    STATUS_CHOICES = [
        ('open', 'Open / Unassigned'),
        ('active', 'Active'),
        ('closed', 'Closed'),
    ]
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='chat_threads')
    session_key = models.CharField(max_length=255, null=True, blank=True)
    assigned_agent = models.ForeignKey(InspectionAgent, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_chats')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        client_identifier = self.user.username if self.user else f"Guest ({self.session_key[:8] if self.session_key else 'Anonymous'})"
        return f"Chat #{self.id} - {client_identifier} [{self.get_status_display()}]"


class ChatMessage(models.Model):
    SENDER_CHOICES = [
        ('client', 'Client'),
        ('agent', 'Agent'),
        ('system', 'System'),
    ]
    thread = models.ForeignKey(ChatThread, on_delete=models.CASCADE, related_name='messages')
    sender_type = models.CharField(max_length=20, choices=SENDER_CHOICES, default='client')
    sender_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    sender_agent = models.ForeignKey(InspectionAgent, on_delete=models.SET_NULL, null=True, blank=True)
    message = models.TextField()
    is_read_by_client = models.BooleanField(default=False)
    is_read_by_agent = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"[{self.sender_type}] Thread #{self.thread.id}: {self.message[:30]}"


class PropertyPanorama(models.Model):
    PANORAMA_TYPE_CHOICES = [
        ('360', '360° Full Room Panorama'),
        ('180', '180° Balcony / Partial View'),
    ]
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='panoramas')
    title = models.CharField(max_length=150, help_text="e.g. Living Room, Master Bedroom, Balcony View")
    panorama_type = models.CharField(max_length=10, choices=PANORAMA_TYPE_CHOICES, default='360')
    image = models.FileField(upload_to='properties/panoramas/')
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'created_at']

    def __str__(self):
        return f"{self.title} ({self.get_panorama_type_display()}) - {self.property.title}"

