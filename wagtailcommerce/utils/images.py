from django.apps import apps
from django.core.exceptions import ImproperlyConfigured

from wagtail.images import get_image_model_string


def get_image_model(require_ready=True):
    """
    Wagtail images/__init__.get_image_ready replacement with require_ready
    """
    model_string = get_image_model_string()
    try:
        app_label, model_name = model_string.split('.')
        return apps.get_model(app_label, model_name, require_ready=require_ready)

    except ValueError:
        raise ImproperlyConfigured("WAGTAILIMAGES_IMAGE_MODEL must be of the form 'app_label.model_name'")
    except LookupError:
        raise ImproperlyConfigured(
            "WAGTAILIMAGES_IMAGE_MODEL refers to model '%s' that has not been installed" % model_string
        )
