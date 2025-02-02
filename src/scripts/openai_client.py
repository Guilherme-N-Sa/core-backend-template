import os
from typing import Any

from openai import OpenAI
from prettyconf import config


class OpenAIClient:
    def __init__(self, default_model: str = "gpt-4o-mini"):
        self.api_key = config("OPENAI_API_KEY", default=os.getenv("OPENAI_API_KEY"))
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")

        self.client = OpenAI(api_key=self.api_key)
        self.default_model = default_model

    def chat_completion(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        stream: bool = False,
        functions: list[dict[str, Any]] | None = None,
        function_call: str | dict[str, str] | None = None,
    ) -> Any:
        response = self.client.chat.completions.create(
            model=model or self.default_model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=stream,
            functions=functions,
            function_call=function_call,
            store=False,
        )
        return response.choices[0].message.content if not stream else response

    def stream_chat_completion(self, *args, **kwargs) -> str:
        kwargs["stream"] = True
        stream = self.chat_completion(*args, **kwargs)
        full_response = []
        for chunk in stream:
            if chunk.choices[0].delta.content:
                full_response.append(chunk.choices[0].delta.content)
        return "".join(full_response)

    def simple_chat(self, message: str, system_prompt: str | None = None) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": message})
        return self.chat_completion(messages)


class AssistantClient:
    def __init__(self, assistant_id: str = config("DEFAULT_ASSISTANT_ID")):
        """Initialize the AssistantClient with a specific assistant ID.

        Args:
            assistant_id: The ID of the pre-configured assistant
        """
        self.oai = OpenAIClient()
        self.assistant_id = assistant_id
        self._assistant = None
        self._default_thread_id = None

    @property
    def assistant(self):
        """Lazy load the assistant details."""
        if self._assistant is None:
            self._assistant = self.oai.client.beta.assistants.retrieve(
                self.assistant_id
            )
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
        return self.oai.client.beta.threads.retrieve(thread_id)

    def set_current_thread(self, thread_id: str | None):
        """Set the default thread ID for continued conversation.

        Args:
            thread_id: The ID of the thread to set as default, or None to clear

        Raises:
            ValueError: If the provided thread_id does not exist
        """
        if thread_id is not None:
            try:
                # Verify thread exists
                self.get_thread(thread_id)
            except Exception as e:
                raise ValueError(f"Thread with ID '{thread_id}' does not exist") from e
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
            raise ValueError("No thread ID provided or set as default thread")

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
        if not thread_id:
            thread_id = self._default_thread_id
        messages = self.list_messages(thread_id, limit)
        return [self._format_message(msg) for msg in messages]

    def get_response(
        self, question: str, thread_id: str | None = None, wait_interval: float = 1.0
    ) -> str:
        """Get a response from the assistant for a given question.

        Args:
            question: The question to ask the assistant
            thread_id: Optional thread ID to continue an existing conversation
            wait_interval: Time in seconds to wait between status checks

        Returns:
            str: The assistant's response
        """
        # Use existing thread or create new one
        if thread_id:
            thread = self.get_thread(thread_id)
            self._default_thread_id = thread_id
        elif self._default_thread_id:
            thread_id = self._default_thread_id
            thread = self.get_thread(thread_id)
        else:
            thread = self.oai.client.beta.threads.create()
            self._default_thread_id = thread.id

        # Add the user's message to the thread
        self.oai.client.beta.threads.messages.create(
            thread_id=thread.id, role="user", content=question
        )

        # Run the assistant
        run = self.oai.client.beta.threads.runs.create(
            thread_id=thread.id, assistant_id=self.assistant_id
        )

        # Wait for completion
        while run.status not in ["completed", "failed", "expired"]:
            run = self.oai.client.beta.threads.runs.retrieve(
                thread_id=thread.id, run_id=run.id
            )
            if run.status in ["failed", "expired"]:
                return f"Error: Assistant run {run.status}"

        # Get the assistant's response
        messages = self.oai.client.beta.threads.messages.list(
            thread_id=thread.id, limit=1, order="desc"
        )

        # Return the most recent assistant message
        for msg in messages.data:
            if msg.role == "assistant":
                return msg.content[0].text.value

        return "No response received from assistant"

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


# Example usage
if __name__ == "__main__":
    # Create an instance of AssistantClient
    assistant = AssistantClient()

    # Print assistant details
    info = assistant.get_assistant_info()
    print("\nAssistant Details:")
    print(f"Name: {info['name']}")
    print(f"Model: {info['model']}")
    print(f"Instructions: {info['instructions']}")
    print(f"Tools: {info['tools']}\n")

    # Example of thread management and conversation
    print("\nStarting new conversation...")
    response1 = assistant.get_response(
        "Qual é a experiência profissional do Guilherme?"
    )
    print(f"Primeira resposta: {response1}\n")

    # Get the default thread ID
    thread_id = assistant.default_thread
    print(f"Thread ID: {thread_id}")

    # Continue the conversation in the same thread
    response2 = assistant.get_response("E quais são suas principais habilidades?")
    print(f"Segunda resposta: {response2}\n")

    # List message history
    print("\nHistórico da conversa:")
    history = assistant.get_thread_history()
    for msg in history:
        print(f"{msg['role'].upper()}: {msg['content']}\n")

