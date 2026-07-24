from django.contrib import admin
from django.conf import settings
from django.urls import include, path
from django.views.static import serve


def serve_public_persona_photo(request, path):
    return serve(request, path, document_root=settings.MEDIA_ROOT / "personas/fotos")

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include(('api.v1.urls', 'api'), namespace='v1')),
]

if settings.DEBUG:
    urlpatterns += [path('media/personas/fotos/<path:path>', serve_public_persona_photo)]
