import json

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

from client.config import MCP_SERVER_URL
from client.llm import GroqLLM


SYSTEM_MESSAGE = {
    "role": "system",
    "content": (
        "You are a helpful assistant with access to MCP tools. "
        "Decide whether a tool is needed for each request. "
        "Use a tool for current or external information that it can provide. "

        "When a tool is called, you MUST use the actual tool result "
        "to answer the user's request. Do not simply say that the "
        "information was found. Present the relevant returned data clearly. "

        "For email requests, show the sender, subject, date, and a short "
        "snippet when available. "

        "For calendar requests, show the event title, date, time, and "
        "location when available. "

        "Never invent information that was not returned by a tool."
    ),
}

def _groq_tools(mcp_tools):
    return [
        {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description or f"Run the {tool.name} MCP tool.",
                "parameters": tool.inputSchema,
            },
        }
        for tool in mcp_tools
    ]


async def chat(history):
    llm = GroqLLM()
    messages = [SYSTEM_MESSAGE, *history]
    tools_used = []

    async with streamable_http_client(MCP_SERVER_URL) as (
        read_stream,
        write_stream,
        _get_session_id,
    ):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            available_tools = await session.list_tools()
            tools = _groq_tools(available_tools.tools)

            for _ in range(5):
                response = llm.chat(messages, tools, tool_choice="auto")
                assistant = response.choices[0].message

                if not assistant.tool_calls:
                    return {
                        "message": assistant.content or "I could not produce a response.",
                        "tools_used": tools_used,
                    }

                messages.append(assistant.model_dump(exclude_none=True))

                for tool_call in assistant.tool_calls:
                    arguments = json.loads(tool_call.function.arguments or "{}")
                    result = await session.call_tool(tool_call.function.name, arguments)
                    result_text = "\n".join(
                        item.text for item in result.content if hasattr(item, "text")
                    )
                    tools_used.append(tool_call.function.name)

                    if result.isError:
                        return {
                            "message": f"The {tool_call.function.name} tool failed: {result_text}",
                            "tools_used": tools_used,
                        }

                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": result_text,
                        }
                    )

    return {
        "message": "The tool workflow exceeded the allowed number of steps.",
        "tools_used": tools_used,
    }
