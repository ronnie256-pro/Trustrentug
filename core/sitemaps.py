from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from core.models import Property

class PropertySitemap(Sitemap):
    changefreq = "daily"
    priority = 0.9

    def items(self):
        return Property.objects.filter(status='available', parent=None)

    def lastmod(self, obj):
        return obj.updated_at

class StaticViewSitemap(Sitemap):
    priority = 0.6
    changefreq = "weekly"

    def items(self):
        return ['home', 'offices', 'search', 'about_us', 'how_escrow_works', 'faq']

    def location(self, item):
        return reverse(item)
