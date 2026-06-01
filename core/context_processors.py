from core.models import SiteSetting

def site_settings(request):
    settings_obj = SiteSetting.objects.first()
    return {
        'site_settings': settings_obj
    }
