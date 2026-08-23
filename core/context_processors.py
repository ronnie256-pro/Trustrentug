from core.models import SiteSetting

def site_settings(request):
    try:
        settings_obj = SiteSetting.objects.first()
    except Exception:
        settings_obj = None
    return {
        'site_settings': settings_obj
    }
