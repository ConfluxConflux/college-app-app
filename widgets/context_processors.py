from django.conf import settings


def widgets_build(request):
    """Flags the widget templates need to know which build they're rendering in.

    `widgets_only` is False on the full site, so the shared widget templates can
    drop the bits that only make sense in the standalone build (and vice versa).
    """
    return {
        'widgets_only': settings.WIDGETS_ONLY,
        'tracker_url': settings.TRACKER_URL,
    }
