from django.conf import settings

from celery import shared_task


if getattr(settings, 'WAGTAILCOMMERCE_ASYNC_THUMBNAILS', False):
    @shared_task(name='wagtailcommerce_generate_image_renditions')
    def generate_renditions(image):
        """
        Get or generate product image renditions asynchronously.
        """
        for name, spec in image.image_set.product.specific.image_renditions.items():
            print(image.image.get_rendition(spec).url)
