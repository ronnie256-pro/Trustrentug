import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from core.models import Property

# Clear existing properties to start fresh for this logic demonstration
Property.objects.all().delete()

# --- Single-Unit Properties ---
Property.objects.create(
    title="Executive Studio",
    category="studio",
    status="available",
    price=1200000,
    location="Ntinda, Kampala"
)

Property.objects.create(
    title="2-Bedroom Haven",
    category="2_bed",
    status="rented",
    price=2500000,
    location="Naalya, Kampala"
)

Property.objects.create(
    title="Lakeside Bungalow",
    category="bungalow",
    status="available",
    price=6500000,
    location="Entebbe"
)

# --- Multi-Unit Property (Parent) ---
parent_building = Property.objects.create(
    title="Emerald Heights Block A",
    category="apartment_block",
    status="available", # Buildings are technically 'available' if they have units
    location="Kololo, Kampala",
    is_multi_unit=True
)

# Child Units
Property.objects.create(
    title="Unit 101",
    category="2_bed",
    status="available",
    price=3000000,
    location="Kololo, Kampala",
    parent=parent_building
)

Property.objects.create(
    title="Unit 102",
    category="1_bed",
    status="rented",
    price=1800000,
    location="Kololo, Kampala",
    parent=parent_building
)

Property.objects.create(
    title="Penthouse Suite",
    category="3_plus_bed",
    status="available",
    price=8000000,
    location="Kololo, Kampala",
    parent=parent_building
)

print("Sample Ugandan properties with hierarchy created successfully.")
