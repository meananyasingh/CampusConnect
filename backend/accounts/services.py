from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode


def send_activation_email(user, college_name):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    activation_url = f"{settings.FRONTEND_URL.rstrip('/')}/activate-account/{uid}/{token}"
    context = {
        "recipient_name": user.get_full_name() or "Student",
        "college_name": college_name,
        "activation_url": activation_url,
    }
    email = EmailMultiAlternatives(
        subject="Activate your CampusConnect student account",
        body=render_to_string("emails/activation.txt", context),
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email],
    )
    email.attach_alternative(render_to_string("emails/activation.html", context), "text/html")
    email.send()
    user.activation_email_sent_at = timezone.now()
    user.activation_email_count += 1
    user.save(update_fields=("activation_email_sent_at", "activation_email_count"))
