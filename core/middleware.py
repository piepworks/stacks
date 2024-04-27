from django.http import HttpResponsePermanentRedirect


class FlyDomainRedirectMiddleware:
    # Adapted from:
    # https://adamj.eu/tech/2020/03/02/how-to-make-django-redirect-www-to-your-bare-domain/

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host().partition(":")[0]
        if host == "tp-stacks.fly.dev" or host == "66.241.124.244":
            return HttpResponsePermanentRedirect(
                "https://stacks.treypiepmeier.com" + request.path
            )
        else:
            return self.get_response(request)
