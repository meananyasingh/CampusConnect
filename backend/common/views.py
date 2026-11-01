from django.conf import settings
from django.http import FileResponse, Http404
from django.utils import timezone
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import HealthCheckSerializer


class HealthCheckView(APIView):
    permission_classes = (AllowAny,)
    serializer_class = HealthCheckSerializer

    def get(self, request):
        return Response(
            {
                "success": True,
                "message": "CampusConnect API is running.",
                "timestamp": timezone.now(),
            }
        )


def frontend_app(request):
    """Serve the built React app; React Router then handles the client-side route."""

    index_file = settings.FRONTEND_DIST_DIR / "index.html"
    if not index_file.is_file():
        raise Http404("The frontend has not been built.")
    return FileResponse(index_file.open("rb"), content_type="text/html")
