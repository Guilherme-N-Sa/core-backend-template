from rest_framework import serializers

from .models import Message, Thread


class ThreadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Thread
        fields = ["thread_id", "created_at", "updated_at"]


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ["id", "content", "created_at"]
