from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('',include('userauth.urls')),
    path('',include('company_admin.urls')),
    path('',include('employee.urls')),
    path('',include('website.urls')),
    path('',include('rostering.urls')),


]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)

handler404 = "userauth.views.page_not_found_404_view"


