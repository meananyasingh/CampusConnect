from rest_framework import serializers

from .models import AcademicProgram, College


class CollegeSerializer(serializers.ModelSerializer):
    class Meta:
        model = College
        fields = ("id", "name", "code")


class AcademicProgramSerializer(serializers.ModelSerializer):
    degree_display = serializers.CharField(source="get_degree_display", read_only=True)

    class Meta:
        model = AcademicProgram
        fields = ("id", "college", "degree", "degree_display", "branch", "duration_years")
