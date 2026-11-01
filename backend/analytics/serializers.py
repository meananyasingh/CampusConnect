from rest_framework import serializers

from announcements.serializers import AnnouncementSerializer
from applications.serializers import (
    ApplicationSerializer,
    InterviewScheduleSerializer,
    StudentInterviewScheduleSerializer,
)
from companies.serializers import CompanySummarySerializer
from opportunities.serializers import RecommendedOpportunitySerializer


class NamedCountSerializer(serializers.Serializer):
    name = serializers.CharField()
    count = serializers.IntegerField()


class BranchAnalyticsSerializer(serializers.Serializer):
    name = serializers.CharField()
    total_students = serializers.IntegerField()
    placed_students = serializers.IntegerField()
    placement_percentage = serializers.DecimalField(max_digits=7, decimal_places=2)


class CompanyAnalyticsSerializer(serializers.Serializer):
    name = serializers.CharField()
    placed_students = serializers.IntegerField()
    average_package = serializers.DecimalField(max_digits=12, decimal_places=2, allow_null=True)
    highest_package = serializers.DecimalField(max_digits=12, decimal_places=2, allow_null=True)


class MonthlyAnalyticsSerializer(serializers.Serializer):
    month = serializers.DateField()
    applications = serializers.IntegerField()


class CollegeAnalyticsSerializer(serializers.Serializer):
    application_pipeline = NamedCountSerializer(many=True)
    branch_performance = BranchAnalyticsSerializer(many=True)
    company_placements = CompanyAnalyticsSerializer(many=True)
    monthly_applications = MonthlyAnalyticsSerializer(many=True)


class DashboardStatsSerializer(serializers.Serializer):
    total_applications = serializers.IntegerField()
    under_review = serializers.IntegerField()
    shortlisted = serializers.IntegerField()
    upcoming_interviews = serializers.IntegerField()
    selected = serializers.IntegerField()


class StudentDashboardSerializer(serializers.Serializer):
    profile_completion = serializers.IntegerField()
    stats = DashboardStatsSerializer()
    recent_applications = ApplicationSerializer(many=True)
    upcoming_interviews = StudentInterviewScheduleSerializer(many=True)
    recommended_opportunities = RecommendedOpportunitySerializer(many=True)
    announcements = AnnouncementSerializer(many=True)


class RecruiterDashboardStatsSerializer(DashboardStatsSerializer):
    active_opportunities = serializers.IntegerField()
    verified_colleges = serializers.IntegerField()


class OpportunityPerformanceSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    status = serializers.CharField()
    status_display = serializers.CharField()
    total_applications = serializers.IntegerField()
    shortlisted = serializers.IntegerField()
    selected = serializers.IntegerField()


class RecruiterDashboardSerializer(serializers.Serializer):
    company = CompanySummarySerializer()
    stats = RecruiterDashboardStatsSerializer()
    recent_applications = ApplicationSerializer(many=True)
    upcoming_interviews = InterviewScheduleSerializer(many=True)
    opportunity_performance = OpportunityPerformanceSerializer(many=True)
