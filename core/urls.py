"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.views.generic import TemplateView
from django.contrib.auth.views import LogoutView
from django.conf import settings
from django.conf.urls.static import static
from core import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home_view, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', LogoutView.as_view(next_page='/'), name='logout'),
    path('register/', views.register_view, name='register'),
    path('landlord/', views.landlord_dashboard, name='landlord_dashboard'),
    path('landlord/dashboard/', views.landlord_dashboard),
    path('landlord/property/add/', views.add_property, name='add_property'),
    path('search/', views.search_view, name='search'),
    path('property/<int:property_id>/', views.property_detail_view, name='property_detail'),
    path('checkout/<int:property_id>/', views.checkout_view, name='checkout'),
    path('about-us/', TemplateView.as_view(template_name="about.html"), name='about_us'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-dashboard/landlord/approve/<int:user_id>/', views.approve_landlord, name='approve_landlord'),
    path('admin-dashboard/property/approve/<int:property_id>/', views.approve_property, name='approve_property'),
    path('admin-dashboard/property/view/<int:property_id>/', views.admin_property_detail, name='admin_property_detail'),
    path('admin-dashboard/property/inspect/<int:property_id>/', views.submit_property_inspection, name='submit_property_inspection'),
    path('property/delete/<int:property_id>/', views.delete_property, name='delete_property'),
    path('admin-dashboard/agent/delete/<int:agent_id>/', views.delete_agent, name='delete_agent'),
    path('admin-dashboard/agent-role/delete/<int:role_id>/', views.delete_agent_role, name='delete_agent_role'),
    path('admin-dashboard/viewing/<int:viewing_id>/', views.admin_viewing_detail, name='admin_viewing_detail'),
    path('admin-dashboard/viewing/status/<int:viewing_id>/', views.admin_viewing_status_update, name='admin_viewing_status_update'),
    path('agent/report/', views.agent_report_auth, name='agent_report_auth'),
    path('agent/submit-report/', views.agent_submit_report, name='agent_submit_report'),
    
    # Tenant Dashboard Routes
    path('tenant/dashboard/', views.tenant_dashboard, name='tenant_dashboard'),
    path('tenant/profile/update/', views.tenant_update_profile, name='tenant_update_profile'),
    path('tenant/booking/create/<int:property_id>/', views.tenant_create_booking, name='tenant_create_booking'),
    path('tenant/viewing/request/<int:property_id>/', views.tenant_request_viewing, name='tenant_request_viewing'),
    path('tenant/schedule-move-in/<int:property_id>/', views.tenant_schedule_move_in, name='tenant_schedule_move_in'),
    path('tenant/maintenance/report/<int:property_id>/', views.tenant_report_maintenance, name='tenant_report_maintenance'),
    path('tenant/agreement/upload/<int:rental_id>/', views.tenant_upload_agreement, name='tenant_upload_agreement'),
    path('tenant/occupants/upload/<int:rental_id>/', views.tenant_upload_occupants, name='tenant_upload_occupants'),
    path('tenant/payment/process/<int:property_id>/', views.tenant_process_payment, name='tenant_process_payment'),
    path('tenant/booking/cancel/<int:booking_id>/', views.tenant_cancel_booking, name='tenant_cancel_booking'),
    path('tenant/favorite/add/<int:property_id>/', views.tenant_add_favorite, name='tenant_add_favorite'),
    path('tenant/favorite/remove/<int:favorite_id>/', views.tenant_remove_favorite, name='tenant_remove_favorite'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
