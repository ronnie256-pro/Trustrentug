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
    path('admin-login-auth/', views.admin_login_api, name='admin_login_api'),
    path('system-admin/2fa-setup/', views.admin_2fa_setup_view, name='admin_2fa_setup'),
    path('reset-password/', views.password_reset_view, name='password_reset_form'),
    path('logout/', LogoutView.as_view(next_page='/'), name='logout'),
    path('register/', views.register_view, name='register'),
    path('landlord/', views.landlord_dashboard, name='landlord_dashboard'),
    path('landlord/dashboard/', views.landlord_dashboard),
    path('landlord/property/add/', views.add_property, name='add_property'),
    path('search/', views.search_view, name='search'),
    path('offices/', views.offices_view, name='offices'),
    path('nearby/', views.nearby_properties_view, name='nearby_properties'),
    path('projects/', views.projects_list_view, name='projects_list'),
    path('projects/<int:project_id>/', views.project_detail_view, name='project_detail'),
    path('projects/diaspora-apply/', views.diaspora_application_submit_view, name='diaspora_application_submit'),
    path('projects/construction-dashboard/', views.client_construction_dashboard, name='client_construction_dashboard'),
    path('projects/construction-dashboard/<int:app_id>/', views.client_construction_dashboard, name='client_construction_dashboard_detail'),
    path('api/properties/nearby/', views.api_nearby_properties, name='api_nearby_properties'),
    path('api/location-cascade/', views.api_location_cascade, name='api_location_cascade'),
    path('property/<int:property_id>/', views.property_detail_view, name='property_detail'),
    path('property/<int:property_id>/tour/', views.property_tour_view, name='property_tour'),
    path('checkout/<int:property_id>/', views.checkout_view, name='checkout'),

    # Pesapal Payment Gateway Routes
    path('payments/pesapal/initiate/', views.pesapal_initiate_payment, name='pesapal_initiate'),
    path('payments/pesapal/initiate/<int:property_id>/', views.pesapal_initiate_payment, name='pesapal_initiate_property'),
    path('payments/pesapal/callback/', views.pesapal_callback, name='pesapal_callback'),
    path('payments/pesapal/ipn/', views.pesapal_ipn_listener, name='pesapal_ipn'),

    path('about-us/', views.about_us_view, name='about_us'),
    path('how-it-works/', views.how_escrow_works_view, name='how_escrow_works'),
    path('verification/', views.verification_process_view, name='verification_process'),
    path('faq/', views.faq_view, name='faq'),
    path('legal/', views.legal_standards_view, name='legal_standards'),
    path('disputes/', views.disputes_view, name='disputes'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-dashboard/payments/pdf/', views.download_payments_pdf, name='download_payments_pdf'),
    path('admin-dashboard/landlord/approve/<int:user_id>/', views.approve_landlord, name='approve_landlord'),
    path('admin-dashboard/property/approve/<int:property_id>/', views.approve_property, name='approve_property'),
    path('admin-dashboard/property/add-sale/', views.admin_add_sale_property, name='admin_add_sale_property'),
    path('admin-dashboard/property/add-office/', views.admin_add_office_property, name='admin_add_office_property'),
    path('admin-dashboard/property/view/<int:property_id>/', views.admin_property_detail, name='admin_property_detail'),
    path('admin-dashboard/property/inspect/<int:property_id>/', views.submit_property_inspection, name='submit_property_inspection'),
    path('property/delete/<int:property_id>/', views.delete_property, name='delete_property'),
    path('admin-dashboard/agent/delete/<int:agent_id>/', views.delete_agent, name='delete_agent'),
    path('admin-dashboard/agent-role/delete/<int:role_id>/', views.delete_agent_role, name='delete_agent_role'),
    path('admin-dashboard/viewing/<int:viewing_id>/', views.admin_viewing_detail, name='admin_viewing_detail'),
    path('admin-dashboard/viewing/status/<int:viewing_id>/', views.admin_viewing_status_update, name='admin_viewing_status_update'),
    path('admin-dashboard/tenant/<int:tenant_id>/', views.admin_tenant_detail, name='admin_tenant_detail'),
    path('admin-dashboard/application/<int:app_id>/', views.admin_application_detail, name='admin_application_detail'),
    path('admin-dashboard/construction-progress/<int:project_id>/', views.admin_construction_progress, name='admin_construction_progress'),
    path('admin-dashboard/construction-slider/upload/', views.admin_upload_construction_slider, name='admin_upload_construction_slider'),
    path('admin-dashboard/construction-slider/delete/<int:image_id>/', views.admin_delete_construction_slider, name='admin_delete_construction_slider'),
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

    # Chatroom Routes
    path('chat-dashboard/', views.chat_agent_dashboard, name='chat_agent_dashboard'),
    path('chat/api/init/', views.chat_api_init, name='chat_api_init'),
    path('chat/api/send/', views.chat_api_send, name='chat_api_send'),
    path('chat/api/poll/', views.chat_api_poll, name='chat_api_poll'),
    path('chat/api/claim/<int:thread_id>/', views.chat_api_claim, name='chat_api_claim'),
    path('chat/api/close/<int:thread_id>/', views.chat_api_close, name='chat_api_close'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
