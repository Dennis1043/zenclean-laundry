from django.conf import settings

def company_settings(request):
    return {
        'company_name': getattr(settings, 'COMPANY_NAME', 'ZenClean'),
        'company_phone': getattr(settings, 'COMPANY_PHONE', '0729 116 844'),
        'company_email': getattr(settings, 'COMPANY_EMAIL', 'info@zenclean.co.ke'),
        'company_address': getattr(settings, 'COMPANY_ADDRESS', 'Kasarani, Nairobi, Kenya'),
        'company_website': getattr(settings, 'COMPANY_WEBSITE', 'www.zenclean.co.ke'),
        'company_logo_text': getattr(settings, 'COMPANY_LOGO_TEXT', '🧺 ZenClean'),
    }

def base_context(request):
    from django.utils import timezone
    return {
        'today': timezone.now(),
        'site_name': getattr(settings, 'COMPANY_NAME', 'ZenClean'),
    }
