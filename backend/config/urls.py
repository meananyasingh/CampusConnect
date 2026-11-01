"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from common.views import frontend_app

urlpatterns = [
    # Django's admin site lives at /django-admin/ because /admin/... belongs to
    # the React college-admin portal.
    path('django-admin/', admin.site.urls),
    path('api/auth/', include('accounts.urls')),
    path('api/colleges/', include('colleges.urls')),
    path('api/companies/', include('companies.urls')),
    path('api/opportunities/', include('opportunities.urls')),
    path('api/applications/', include('applications.urls')),
    path('api/placements/', include('placements.urls')),
    path('api/notifications/', include('notifications.urls')),
    path('api/analytics/', include('analytics.urls')),
    path('api/announcements/', include('announcements.urls')),
    path('api/talent/', include('talent.urls')),
    path('api/documents/', include('documents.urls')),
    path('api/audit/', include('audit.urls')),
    path('api/students/', include('students.urls')),
    path('api/', include('common.urls')),
    path('api/schema/', SpectacularAPIView.as_view(), name='api-schema'),
    path(
        'api/docs/',
        SpectacularSwaggerView.as_view(url_name='api-schema'),
        name='api-docs',
    ),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Must stay last: every other non-API path belongs to the React app.
urlpatterns += [
    re_path(r"^(?!(?:api|django-admin|static|media)(?:/|$)).*$", frontend_app, name="frontend-app"),
]
