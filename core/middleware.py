class ContentSecurityPolicyMiddleware:
    """
    Custom Middleware to enforce comprehensive Content Security Policy headers,
    permitting Cloudflare Insights, Google ReCAPTCHA, FontAwesome CDN, Leaflet, and static assets.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if response is not None and hasattr(response, '__setitem__'):
            csp_script_src = (
                "'self' 'unsafe-inline' 'unsafe-eval' "
                "https://www.google.com/recaptcha/ "
                "https://www.gstatic.com/recaptcha/ "
                "https://cdnjs.cloudflare.com "
                "https://static.cloudflareinsights.com "
                "https://cloudflareinsights.com"
            )

            csp_policy = (
                f"default-src 'self' 'unsafe-inline' 'unsafe-eval' data: blob: https:; "
                f"script-src {csp_script_src}; "
                f"script-src-elem {csp_script_src}; "
                "style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com https://fonts.googleapis.com; "
                "font-src 'self' data: https://cdnjs.cloudflare.com https://fonts.gstatic.com; "
                "img-src 'self' data: blob: https:; "
                "connect-src 'self' https://static.cloudflareinsights.com https://cloudflareinsights.com https://www.google.com/recaptcha/ https:;"
            )

            response['Content-Security-Policy'] = csp_policy
        return response
