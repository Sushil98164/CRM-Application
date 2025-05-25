
from django.urls import path
from .views import *

app_name = 'website'

urlpatterns = [
    path('', LandingPage.as_view(), name='landing_page'),
    path('about/', AboutUsPage.as_view(), name='about'),
    path('solutions/', SolutionPage.as_view(), name='solutions'),
    path('contact/', ContactView.as_view(), name='contact'),
    path('add/contact/', ContactView.as_view(), name='add_contact'),
    path("health/", HealthCheckView.as_view(), name = "health"),
]