from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.db import transaction
from django.template.loader import render_to_string

from .models import Notification, NotificationPreference


CATEGORY_PREFERENCE_FIELDS = {
    Notification.Category.COMPANY: "email_company",
    Notification.Category.APPLICATION: "email_applications",
    Notification.Category.INTERVIEW: "email_interviews",
    Notification.Category.PLACEMENT: "email_placements",
    Notification.Category.ANNOUNCEMENT: "email_announcements",
    Notification.Category.SYSTEM: "email_system",
}


def send_notification_email(notification):
    preferences, _ = NotificationPreference.objects.get_or_create(user=notification.recipient)
    category_field = CATEGORY_PREFERENCE_FIELDS.get(notification.category, "email_system")
    if not preferences.email_enabled or not getattr(preferences, category_field):
        return False
    action_url = (
        f"{settings.FRONTEND_URL.rstrip('/')}{notification.link}"
        if notification.link.startswith("/") else notification.link
    )
    context = {"notification": notification, "action_url": action_url}
    email = EmailMultiAlternatives(
        subject=f"CampusConnect: {notification.title}",
        body=render_to_string("emails/notification.txt", context),
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[notification.recipient.email],
    )
    email.attach_alternative(render_to_string("emails/notification.html", context), "text/html")
    try:
        email.send()
    except Exception:
        return False
    return True


def create_notification(*, recipient, category, title, message, link=""):
    if recipient and recipient.is_active:
        notification = Notification.objects.create(
            recipient=recipient,
            category=category,
            title=title,
            message=message,
            link=link,
        )
        transaction.on_commit(lambda: send_notification_email(notification))
        return notification
    return None


def notify_users(*, users, category, title, message, link=""):
    recipients = {user.id: user for user in users if user.is_active}
    notifications = Notification.objects.bulk_create([
        Notification(
            recipient=user,
            category=category,
            title=title,
            message=message,
            link=link,
        )
        for user in recipients.values()
    ])
    transaction.on_commit(lambda: [send_notification_email(item) for item in notifications])
    return notifications


def notify_company_recruiters(*, company, category, title, message, link=""):
    return notify_users(
        users=(profile.user for profile in company.recruiters.select_related("user").all()),
        category=category,
        title=title,
        message=message,
        link=link,
    )


def notify_college_admins(*, college, category, title, message, link=""):
    return notify_users(
        users=(profile.user for profile in college.administrators.select_related("user").all()),
        category=category,
        title=title,
        message=message,
        link=link,
    )
