import asyncio
import json

from client.llm import GroqLLM

from client.config import MCP_SERVER_URL

from mcp import ClientSession

from mcp.client.streamable_http import streamable_http_client


llm = GroqLLM()


async def main():

    async with streamable_http_client(MCP_SERVER_URL) as (
        read_stream,
        write_stream,
        _get_session_id,
    ):

        async with ClientSession(
            read_stream,
            write_stream
        ) as session:

            print("Initializing MCP...")

            await session.initialize()

            print("Connected Successfully")

            tools = await session.list_tools()

            groq_tools = []

            for tool in tools.tools:

                groq_tools.append({

                    "type": "function",

                    "function": {

                        "name": tool.name,

                        "description": tool.description,

                        "parameters": tool.inputSchema
                    }
                })

            while True:

                question = input("\nYou : ")

                if question.lower() == "exit":
                    break

                messages = [

                    {
                        "role": "system",
                        "content": (
                            "You are a live weather assistant. Always use the provided "
                            "weather tool to answer weather questions. Never claim that "
                            "you cannot access real-time weather data."
                        )
                    },

                    {
                        "role": "user",
                        "content": question
                    }

                ]

                response = llm.chat(
                    messages,
                    groq_tools,
                    tool_choice="auto",
                )

                assistant = response.choices[0].message

                if assistant.tool_calls:

                    tool = assistant.tool_calls[0]

                    tool_name = tool.function.name

                    arguments = json.loads(
                        tool.function.arguments
                    )

                    result = await session.call_tool(
                        tool_name,
                        arguments
                    )

                    result_text = "\n".join(
                        item.text for item in result.content
                        if hasattr(item, "text")
                    )

                    messages.append(assistant.model_dump(exclude_none=True))
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool.id,
                        "content": result_text,
                    })

                    final_response = llm.chat(messages)
                    print(final_response.choices[0].message.content)

                else:

                    print(
                        assistant.content
                    )


if __name__ == "__main__":
    asyncio.run(main())
