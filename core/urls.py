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
from core import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home_view, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', LogoutView.as_view(next_page='/'), name='logout'),
    path('register/', views.register_view, name='register'),
    path('landlord/', views.landlord_dashboard, name='landlord_dashboard'),
    path('landlord/property/add/', views.add_property, name='add_property'),
    path('search/', TemplateView.as_view(template_name="tenant/search.html"), name='search'),
    path('property/1/', TemplateView.as_view(template_name="tenant/property_detail.html"), name='property_detail'),
    path('checkout/1/', TemplateView.as_view(template_name="tenant/checkout.html"), name='checkout'),
    path('about-us/', TemplateView.as_view(template_name="about.html"), name='about_us'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-dashboard/landlord/approve/<int:user_id>/', views.approve_landlord, name='approve_landlord'),
]
