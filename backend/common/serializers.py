from rest_framework import serializers


class HealthCheckSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    message = serializers.CharField()
    timestamp = serializers.DateTimeField()
