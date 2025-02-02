import time
import logging
from typing import Any

from openai import OpenAI
from django.conf import settings


logger = logging.getLogger(__name__)


class OpenAIClient:
    def __init__(self, default_model: str = "gpt-4o-mini"):
        self.api_key = settings.OPENAI_API_KEY
        if not self.api_key:
            logger.error("OPENAI_API_KEY not found in environment variables")
            raise ValueError("OPENAI_API_KEY not found in environment variables")

        logger.info("Initializing OpenAI client with model: %s", default_model)
        self.client = OpenAI(api_key=self.api_key)
        self.default_model = default_model

    def chat_completion(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float = 0.6,
        top_p: float = 0.7,
        max_tokens: int | None = None,
        stream: bool = False,
        functions: list[dict[str, Any]] | None = None,
        function_call: str | dict[str, str] | None = None,
    ) -> Any:
        logger.debug(
            "Making chat completion request: model=%s, stream=%s, temperature=%s",
            model or self.default_model,
            stream,
            temperature,
        )
        try:
            response = self.client.chat.completions.create(
                model=model or self.default_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                stream=stream,
                functions=functions,
                function_call=function_call,
                store=False,
            )
            logger.debug("Chat completion request successful")
            return response.choices[0].message.content if not stream else response
        except Exception as e:
            logger.error("Error in chat completion: %s", str(e))
            raise

    def stream_chat_completion(self, *args, **kwargs) -> str:
        logger.debug("Starting streaming chat completion")
        kwargs["stream"] = True
        try:
            stream = self.chat_completion(*args, **kwargs)
            full_response = []
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    full_response.append(chunk.choices[0].delta.content)
            logger.debug("Streaming chat completion finished successfully")
            return "".join(full_response)
        except Exception as e:
            logger.error("Error in streaming chat completion: %s", str(e))
            raise

    def simple_chat(self, message: str, system_prompt: str | None = None) -> str:
        logger.debug("Starting simple chat: system_prompt=%s", bool(system_prompt))
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": message})
        return self.chat_completion(messages)


class AssistantClient:
    def __init__(self, assistant_id: str = settings.DEFAULT_ASSISTANT_ID):
        """Initialize the AssistantClient with a specific assistant ID.

        Args:
            assistant_id: The ID of the pre-configured assistant
        """
        logger.info("Initializing AssistantClient with ID: %s", assistant_id)
        self.oai = OpenAIClient()
        self.assistant_id = assistant_id
        self._assistant = None
        self._default_thread_id = None

    @property
    def assistant(self):
        """Lazy load the assistant details."""
        if self._assistant is None:
            try:
                logger.debug("Loading assistant details for ID: %s", self.assistant_id)
                self._assistant = self.oai.client.beta.assistants.retrieve(
                    self.assistant_id
                )
            except Exception as e:
                logger.error(
                    "Failed to retrieve assistant with ID '%s': %s",
                    self.assistant_id,
                    str(e),
                )
                raise ValueError(
                    f"Assistant with ID '{self.assistant_id}' does not exist"
                ) from e
        return self._assistant

    @property
    def default_thread_id(self):
        """Get the default thread ID if exists."""
        return self._default_thread_id

    def get_thread(self, thread_id: str):
        """Retrieve a specific thread by ID.

        Args:
            thread_id: The ID of the thread to retrieve

        Returns:
            Thread object if found
        """
        try:
            logger.debug("Retrieving thread: %s", thread_id)
            return self.oai.client.beta.threads.retrieve(thread_id)
        except Exception as e:
            logger.error("Failed to retrieve thread '%s': %s", thread_id, str(e))
            raise ValueError(f"Thread with ID '{thread_id}' does not exist") from e

    def set_default_thread(self, thread_id: str | None):
        """Set the default thread ID for continued conversation.

        Args:
            thread_id: The ID of the thread to set as default, or None to clear

        Raises:
            ValueError: If the provided thread_id does not exist
        """
        if thread_id is not None:
            logger.info("Setting default thread ID: %s", thread_id)
            self.get_thread(thread_id)
        else:
            logger.info("Clearing default thread ID")
        self._default_thread_id = thread_id

    def list_messages(
        self, thread_id: str | None = None, limit: int = 100, order: str = "desc"
    ) -> list:
        """List messages from a specific thread.

        Args:
            thread_id: The thread ID to list messages from (uses default_thread if None)
            limit: Maximum number of messages to return
            order: Sort order ("asc" or "desc")

        Returns:
            list: List of message objects
        """
        thread_id = thread_id or self._default_thread_id
        if not thread_id:
            logger.error("No thread ID provided or set as default thread")
            raise ValueError("No thread ID provided or set as default thread")

        logger.debug("Listing messages for thread %s (limit=%d, order=%s)", thread_id, limit, order)
        messages = self.oai.client.beta.threads.messages.list(
            thread_id=thread_id, limit=limit, order=order
        )
        return messages.data

    def _format_message(self, message) -> dict:
        """Format a message object into a readable dictionary.

        Args:
            message: The message object to format

        Returns:
            dict: Formatted message with role, content, and timestamp
        """
        return {
            "role": message.role,
            "content": message.content[0].text.value if message.content else None,
            "created_at": message.created_at,
            "id": message.id,
        }

    def get_thread_history(
        self, thread_id: str | None = None, limit: int = 100
    ) -> list[dict]:
        """Get formatted conversation history from a thread.

        Args:
            thread_id: The thread ID to get history from (uses default_thread if None)
            limit: Maximum number of messages to return

        Returns:
            list: List of formatted messages
        """
        thread_id = thread_id or self._default_thread_id
        if not thread_id:
            raise ValueError("No thread ID provided or set as default thread")

        messages = self.list_messages(thread_id, limit)
        return [self._format_message(msg) for msg in messages]

    def get_response(
        self, question: str, thread_id: str | None = None, wait_interval: float = 1
    ) -> str:
        """Get a response from the assistant for a given question.

        Args:
            question: The question to ask the assistant
            thread_id: Optional thread ID to continue an existing conversation
            wait_interval: Time in seconds to wait between status checks

        Returns:
            str: The assistant's response
        """
        try:
            # Use existing thread or create new one
            if thread_id:
                logger.debug("Using existing thread: %s", thread_id)
                thread = self.get_thread(thread_id)
            elif self._default_thread_id:
                logger.debug("Using default thread: %s", self._default_thread_id)
                thread = self.get_thread(self._default_thread_id)
            else:
                logger.debug("Creating new thread")
                thread = self.oai.client.beta.threads.create()
                self.set_default_thread(thread.id)

            logger.debug("Adding user message to thread")
            self.oai.client.beta.threads.messages.create(
                thread_id=thread.id, role="user", content=question
            )

            logger.debug("Starting assistant run")
            run = self.oai.client.beta.threads.runs.create(
                thread_id=thread.id, assistant_id=self.assistant_id
            )

            # Wait for completion
            while run.status not in ["completed", "failed", "expired"]:
                run = self.oai.client.beta.threads.runs.retrieve(
                    thread_id=thread.id, run_id=run.id
                )
                logger.debug("Run status: %s", run.status)
                if run.status in ["failed", "expired"]:
                    logger.error("Assistant run %s", run.status)
                    return f"Error: Assistant run {run.status}"
                time.sleep(wait_interval)

            logger.debug("Getting assistant response")
            messages = self.oai.client.beta.threads.messages.list(
                thread_id=thread.id, limit=1, order="desc"
            )

            for msg in messages.data:
                if msg.role == "assistant":
                    return msg.content[0].text.value

            logger.warning("No assistant response received")
            return "No response received from assistant"
        except Exception as e:
            logger.error("Error getting assistant response: %s", str(e))
            raise

    def get_assistant_info(self) -> dict:
        """Get information about the configured assistant.

        Returns:
            dict: Assistant details including name, model, and instructions
        """
        return {
            "name": self.assistant.name,
            "model": self.assistant.model,
            "instructions": self.assistant.instructions,
            "tools": self.assistant.tools,
        }
