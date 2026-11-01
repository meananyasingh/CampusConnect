import django_filters

from students.models import StudentProfile


class RecruiterCandidateFilter(django_filters.FilterSet):
    college = django_filters.NumberFilter(field_name="college_id")
    program = django_filters.NumberFilter(field_name="program_id")
    graduation_year = django_filters.NumberFilter()
    min_cgpa = django_filters.NumberFilter(field_name="cgpa", lookup_expr="gte")
    max_backlogs = django_filters.NumberFilter(field_name="active_backlogs", lookup_expr="lte")
    skill = django_filters.CharFilter(field_name="skills__skill__name", lookup_expr="icontains")
    has_resume = django_filters.BooleanFilter(method="filter_has_resume")

    class Meta:
        model = StudentProfile
        fields = ()

    def filter_has_resume(self, queryset, name, value):
        if value:
            return queryset.filter(resumes__is_primary=True).distinct()
        return queryset.exclude(resumes__is_primary=True).distinct()
