from groq import Groq

from client.config import GROQ_API_KEY, MODEL_NAME


class GroqLLM:

    def __init__(self):

        self.client = Groq(
            api_key=GROQ_API_KEY
        )

        self.model = MODEL_NAME

    def chat(self, messages, tools=None, tool_choice="auto"):
        request = {
            "model": self.model,
            "messages": messages,
            "temperature": 0,
        }

        if tools:
            request["tools"] = tools
            request["tool_choice"] = tool_choice

        return self.client.chat.completions.create(
            **request
        )
