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
    ]

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending_verification')
    price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    location = models.CharField(max_length=255)
    
    # Parent-Child relationship
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='units')
    
    is_multi_unit = models.BooleanField(default=False)
    
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

    class Meta:
        verbose_name_plural = "Properties"
