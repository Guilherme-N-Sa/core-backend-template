from rest_framework import viewsets, status, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.core_api.clients.openai_client import AssistantClient
from .models import Message, Thread
from .serializers import MessageSerializer, ThreadSerializer
import time
import logging

logger = logging.getLogger(__name__)


class ThreadViewSet(viewsets.GenericViewSet, mixins.ListModelMixin):
    queryset = Thread.objects.all().order_by("-created_at")
    serializer_class = ThreadSerializer
    ordering = "-created_at"


class ChatViewSet(viewsets.ViewSet):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.assistant_client = AssistantClient()

    @action(detail=True, methods=["get"], url_path="history")
    def get_chat_history(self, request, pk=None):
        """Get chat history for a specific thread."""
        try:
            # Verify thread exists in our database
            Thread.objects.get(thread_id=pk)

            messages = self.assistant_client.get_thread_history(thread_id=pk)
            return Response(messages)
        except Thread.DoesNotExist:
            return Response(
                {"error": "Thread not found."}, status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=["post"], url_path="send")
    def send_message(self, request):
        """Send a message and get response from the assistant."""
        message = request.data.get("message")
        thread_id = request.data.get("thread_id", None)

        if not message:
            return Response(
                {"error": "Message is required."}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            start_time = time.time()
            response = self.assistant_client.get_response(
                question=message, thread_id=thread_id
            )
            end_time = time.time()
            logger.info("Time taken: %s seconds", end_time - start_time)

            if not thread_id:
                thread_id = self.assistant_client.default_thread_id

            thread, created = Thread.objects.get_or_create(thread_id=thread_id)
            if not created:
                thread.save()

            return Response(
                {"thread": ThreadSerializer(thread).data, "message": response}
            )
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
