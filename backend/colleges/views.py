from rest_framework import generics
from rest_framework.permissions import AllowAny

from .models import AcademicProgram, College
from .serializers import AcademicProgramSerializer, CollegeSerializer


class ActiveCollegeListView(generics.ListAPIView):
    permission_classes = (AllowAny,)
    serializer_class = CollegeSerializer
    pagination_class = None
    queryset = College.objects.filter(is_active=True).order_by("name")


class ActiveAcademicProgramListView(generics.ListAPIView):
    permission_classes = (AllowAny,)
    serializer_class = AcademicProgramSerializer
    pagination_class = None

    def get_queryset(self):
        queryset = AcademicProgram.objects.filter(
            is_active=True,
            college__is_active=True,
        ).select_related("college")
        college_id = self.request.query_params.get("college")
        if not college_id:
            return queryset.none()
        return queryset.filter(college_id=college_id).order_by("degree", "branch")
