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
