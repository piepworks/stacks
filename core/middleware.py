import pytz
from django.http import HttpResponsePermanentRedirect
from django.utils import timezone
from django.conf import settings


class FlyDomainRedirectMiddleware:
    # Adapted from:
    # https://adamj.eu/tech/2020/03/02/how-to-make-django-redirect-www-to-your-bare-domain/

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host().partition(":")[0]
        if (
            host == "tp-stacks.fly.dev"
            or host == "stacks.treypiepmeier.com"
            or host == "66.241.124.244"
        ):
            return HttpResponsePermanentRedirect(
                "https://bookstacks.app" + request.path
            )
        else:
            return self.get_response(request)


class TimezoneMiddleware:
    """
    Automatically set the timezone to what's the user has chosen.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            tzname = request.user.timezone
            if tzname:
                timezone.activate(pytz.timezone(tzname))
            else:
                timezone.activate(pytz.timezone(settings.TIME_ZONE))
        else:
            timezone.deactivate()

        return self.get_response(request)
