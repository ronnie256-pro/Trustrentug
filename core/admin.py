from django.contrib import admin
from .models import (
    Property, PropertyPanorama, HeroVideo, UserProfile, 
    Inspection, InspectionReport, InspectionAgent, AgentRole,
    ConstructionProject, ShowcaseSliderImage
)

@admin.register(HeroVideo)
class HeroVideoAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_active', 'order', 'created_at')
    list_editable = ('is_active', 'order')
    search_fields = ('title',)

@admin.register(ShowcaseSliderImage)
class ShowcaseSliderImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'is_active', 'order', 'created_at')
    list_editable = ('is_active', 'order')
    search_fields = ('title',)

@admin.register(PropertyPanorama)
class PropertyPanoramaAdmin(admin.ModelAdmin):
    list_display = ('title', 'property', 'panorama_type', 'order', 'created_at')
    list_filter = ('panorama_type',)
    search_fields = ('title', 'property__title')

@admin.register(ConstructionProject)
class ConstructionProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'property_id', 'owner_phone', 'location', 'progress_percentage', 'status', 'supervisor_name', 'created_at')
    list_filter = ('status',)
    search_fields = ('title', 'property_id', 'owner_phone', 'location', 'short_description')
    readonly_fields = ('property_id', 'created_at', 'updated_at')


