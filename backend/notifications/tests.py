from django.urls import reverse
from django.core import mail
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User

from .models import Notification, NotificationPreference
from .services import create_notification


class NotificationTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="notification-student@example.com",
            password="A-strong-test-password-2048",
            role=User.Role.STUDENT,
        )
        self.other_user = User.objects.create_user(
            email="other-notification-user@example.com",
            password="A-strong-test-password-2048",
            role=User.Role.RECRUITER,
        )
        self.notification = Notification.objects.create(
            recipient=self.user,
            category=Notification.Category.APPLICATION,
            title="Application shortlisted",
            message="Your application moved to the shortlist.",
            link="/student/applications",
        )
        Notification.objects.create(
            recipient=self.other_user,
            category=Notification.Category.COMPANY,
            title="Other user's notification",
            message="This must remain private.",
        )
        self.client.force_authenticate(self.user)

    def test_user_sees_only_own_notifications(self):
        response = self.client.get(reverse("notification-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], self.notification.id)

    def test_unread_count_is_scoped_to_current_user(self):
        response = self.client.get(reverse("notification-unread-count"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["unread_count"], 1)

    def test_user_can_mark_own_notification_as_read(self):
        response = self.client.post(reverse("notification-read", args=(self.notification.id,)))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["is_read"])
        self.assertIsNotNone(response.data["read_at"])

    def test_user_cannot_mark_another_users_notification(self):
        other_notification = self.other_user.notifications.get()

        response = self.client.post(reverse("notification-read", args=(other_notification.id,)))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_mark_all_read_only_updates_current_users_notifications(self):
        response = self.client.post(reverse("notification-read-all"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["unread_count"], 0)
        self.assertTrue(Notification.objects.get(pk=self.notification.id).is_read)
        self.assertFalse(self.other_user.notifications.get().is_read)

    def test_user_can_manage_email_notification_preferences(self):
        initial = self.client.get(reverse("notification-preferences"))
        response = self.client.patch(
            reverse("notification-preferences"),
            {"email_interviews": False, "email_announcements": False},
            format="json",
        )

        self.assertEqual(initial.status_code, status.HTTP_200_OK)
        self.assertTrue(initial.data["email_enabled"])
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["email_interviews"])
        self.assertFalse(response.data["email_announcements"])

    def test_workflow_notification_sends_branded_email_after_commit(self):
        with self.captureOnCommitCallbacks(execute=True):
            create_notification(
                recipient=self.user,
                category=Notification.Category.APPLICATION,
                title="Application selected",
                message="Your application was selected.",
                link="/student/applications",
            )

        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("CampusConnect: Application selected", mail.outbox[0].subject)
        self.assertIn("http://localhost:5173/student/applications", mail.outbox[0].body)
        self.assertEqual(len(mail.outbox[0].alternatives), 1)

    def test_disabled_category_still_creates_in_app_notification_without_email(self):
        NotificationPreference.objects.create(user=self.user, email_applications=False)

        with self.captureOnCommitCallbacks(execute=True):
            notification = create_notification(
                recipient=self.user,
                category=Notification.Category.APPLICATION,
                title="Application reviewed",
                message="Your application was reviewed.",
            )

        self.assertIsNotNone(notification)
        self.assertEqual(len(mail.outbox), 0)
