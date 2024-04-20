from django.http import HttpResponsePermanentRedirect


class FlyDomainRedirectMiddleware:
    # This is to catch visits from the “Starter” domain created by Fly.io
    # that is apparently impossible to remove. And I get an email every time
    # some sketchy bot tries to visit it. Let’s just tell them to stop.
    #
    # Adapted from:
    # https://adamj.eu/tech/2020/03/02/how-to-make-django-redirect-www-to-your-bare-domain/

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host().partition(":")[0]
        if host == "tp-stacks.fly.dev" or host == "66.241.125.144":
            return HttpResponsePermanentRedirect(
                "https://stacks.treypiepmeier.com" + request.path
            )
        else:
            return self.get_response(request)
