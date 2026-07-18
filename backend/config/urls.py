from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.http import JsonResponse
from django.views.generic import TemplateView


def health(_request):
    return JsonResponse({"status": "ok", "service": "casa-yeison"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", health),
    path("api/v1/", include("finance.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.FRONTEND_DIST.exists():
    urlpatterns += [path("", TemplateView.as_view(template_name="index.html"), name="frontend")]
    urlpatterns += [path("<path:path>", TemplateView.as_view(template_name="index.html"), name="frontend-route")]
