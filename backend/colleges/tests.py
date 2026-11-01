from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import AcademicProgram, College


class CollegeDirectoryTests(APITestCase):
    def setUp(self):
        self.active_college = College.objects.create(name="Active College", code="AC")
        self.inactive_college = College.objects.create(
            name="Inactive College",
            code="IC",
            is_active=False,
        )
        self.program = AcademicProgram.objects.create(
            college=self.active_college,
            degree=AcademicProgram.Degree.BTECH,
            branch="Computer Science and Engineering",
        )
        AcademicProgram.objects.create(
            college=self.inactive_college,
            degree=AcademicProgram.Degree.BCA,
            branch="Computer Applications",
        )

    def test_public_college_list_contains_only_active_colleges(self):
        response = self.client.get(reverse("college-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([college["id"] for college in response.data], [self.active_college.id])

    def test_program_list_is_filtered_by_active_college(self):
        response = self.client.get(
            reverse("program-list"),
            {"college": self.active_college.id},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([program["id"] for program in response.data], [self.program.id])

    def test_program_list_requires_a_college_filter(self):
        response = self.client.get(reverse("program-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])
