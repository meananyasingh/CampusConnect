import django_filters
from django.db.models import Q

from .models import Opportunity


class StudentOpportunityFilter(django_filters.FilterSet):
    company = django_filters.CharFilter(field_name="company__name", lookup_expr="icontains")
    skill = django_filters.CharFilter(field_name="required_skills__name", lookup_expr="icontains")
    min_compensation = django_filters.NumberFilter(method="filter_min_compensation")
    deadline_before = django_filters.DateFilter(field_name="application_deadline", lookup_expr="lte")
    saved_only = django_filters.BooleanFilter(method="filter_saved_only")
    eligible_only = django_filters.BooleanFilter(method="filter_eligible_only")

    class Meta:
        model = Opportunity
        fields = ("opportunity_type", "work_mode")

    def filter_min_compensation(self, queryset, name, value):
        return queryset.filter(Q(compensation_max__gte=value) | Q(compensation_min__gte=value))

    def filter_saved_only(self, queryset, name, value):
        if value:
            return queryset.filter(bookmarks__student=self.request.user.student_profile)
        return queryset

    def filter_eligible_only(self, queryset, name, value):
        if not value:
            return queryset
        student = self.request.user.student_profile
        from placements.services import get_college_policy_blockers

        if get_college_policy_blockers(student):
            return queryset.none()
        if student.cgpa is None:
            queryset = queryset.filter(min_cgpa=0)
        else:
            queryset = queryset.filter(min_cgpa__lte=student.cgpa)
        return queryset.filter(
            max_active_backlogs__gte=student.active_backlogs,
        ).filter(
            Q(graduation_year_from__isnull=True) | Q(graduation_year_from__lte=student.graduation_year),
            Q(graduation_year_to__isnull=True) | Q(graduation_year_to__gte=student.graduation_year),
        ).filter(
            Q(eligible_programs__isnull=True) | Q(eligible_programs=student.program),
        ).distinct()
