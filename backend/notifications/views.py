from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics
from rest_framework.response import Response

from .models import Notification, NotificationPreference
from .serializers import NotificationPreferenceSerializer, NotificationSerializer, NotificationUnreadCountSerializer


class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    filterset_fields = ("category", "is_read")
    search_fields = ("title", "message")
    ordering_fields = ("created_at",)

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Notification.objects.none()
        return Notification.objects.filter(recipient=self.request.user)


class NotificationUnreadCountView(generics.GenericAPIView):
    serializer_class = NotificationUnreadCountSerializer

    def get(self, request):
        return Response({
            "unread_count": Notification.objects.filter(recipient=request.user, is_read=False).count(),
        })


class NotificationMarkReadView(generics.GenericAPIView):
    serializer_class = NotificationSerializer

    def post(self, request, *args, **kwargs):
        notification = get_object_or_404(
            Notification.objects.filter(recipient=request.user),
            pk=self.kwargs["pk"],
        )
        if not notification.is_read:
            notification.is_read = True
            notification.read_at = timezone.now()
            notification.save(update_fields=("is_read", "read_at"))
        return Response(NotificationSerializer(notification).data)


class NotificationMarkAllReadView(generics.GenericAPIView):
    serializer_class = NotificationUnreadCountSerializer

    def post(self, request):
        Notification.objects.filter(recipient=request.user, is_read=False).update(
            is_read=True,
            read_at=timezone.now(),
        )
        return Response({"unread_count": 0})


class NotificationPreferenceView(generics.RetrieveUpdateAPIView):
    serializer_class = NotificationPreferenceSerializer

    def get_object(self):
        preference, _ = NotificationPreference.objects.get_or_create(user=self.request.user)
        return preference
