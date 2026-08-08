from django.contrib import admin
from .models import (
    Property, PropertyPanorama, HeroVideo, UserProfile, 
    Inspection, InspectionReport, InspectionAgent, AgentRole
)

@admin.register(HeroVideo)
class HeroVideoAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_active', 'order', 'created_at')
    list_editable = ('is_active', 'order')
    search_fields = ('title',)

@admin.register(PropertyPanorama)
class PropertyPanoramaAdmin(admin.ModelAdmin):
    list_display = ('title', 'property', 'panorama_type', 'order', 'created_at')
    list_filter = ('panorama_type',)
    search_fields = ('title', 'property__title')
