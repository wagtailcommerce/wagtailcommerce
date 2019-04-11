from django.conf import settings


if getattr(settings, 'WAGTAILCOMMERCE_ASYNC_THUMBNAILS', False):
    from django.core.management.base import BaseCommand

    class Command(BaseCommand):
        help = 'Regenerates product image renditions'

        def handle(self, *args, **options):
            question = 'Are you sure you want to regenerate all product thumbnails?\n'
            result = input("%s " % question)

            if not result:
                return
            while len(result) < 1 or result[0].lower() not in "yn":
                result = input("Please answer yes or no: ")

            if result[0].lower() == "y":
                self.stdout.write(self.style.SUCCESS('Regenerating thumbnails\n'))

                from wagtailcommerce.products.models import Image
                from wagtailcommerce.products.images import generate_renditions

                for image in Image.objects.all():
                    generate_renditions.delay(image)
