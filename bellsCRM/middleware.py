from django.utils import timezone
class TimezoneMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        original_timezone_now = timezone.now
        timezone.now = lambda: timezone.make_naive(original_timezone_now())
        response = self.get_response(request)
        timezone.now = original_timezone_now
        return response

