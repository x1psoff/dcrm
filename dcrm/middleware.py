class StripNullOriginMiddleware:
    """
    Workaround for clients that send `Origin: null` on POST requests.

    When enabled via settings.CSRF_STRIP_NULL_ORIGIN = True, this middleware
    removes the Origin header so Django's CsrfViewMiddleware falls back to its
    normal CSRF cookie/token validation.

    NOTE: This weakens CSRF protection for "opaque origin" requests, so keep it
    disabled unless you really need it.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if getattr(request, "META", None) is not None:
            enabled = getattr(request, "CSRF_STRIP_NULL_ORIGIN", None)
            # Prefer settings if available
            try:
                from django.conf import settings

                enabled = getattr(settings, "CSRF_STRIP_NULL_ORIGIN", False)
            except Exception:
                enabled = bool(enabled)

            if enabled:
                origin = request.META.get("HTTP_ORIGIN")
                if origin is not None and origin.strip().lower() == "null":
                    request.META.pop("HTTP_ORIGIN", None)

        return self.get_response(request)


