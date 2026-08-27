from django.core.management.base import BaseCommand
from core.models import Property

class Command(BaseCommand):
    help = 'Populate missing SEO slugs for existing properties'

    def handle(self, *args, **options):
        properties = Property.objects.filter(slug__isnull=True) | Property.objects.filter(slug='')
        count = 0
        for p in properties:
            p.save()
            count += 1
        self.stdout.write(self.style.SUCCESS(f"Successfully populated SEO slugs for {count} properties."))
