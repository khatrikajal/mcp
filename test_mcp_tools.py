import asyncio

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

from client.config import MCP_SERVER_URL


async def main():

    async with streamable_http_client(MCP_SERVER_URL) as (
        read_stream,
        write_stream,
        _,
    ):

        async with ClientSession(
            read_stream,
            write_stream
        ) as session:

            print("Connecting to MCP server...")

            await session.initialize()

            print("Connected successfully.\n")

            result = await session.list_tools()

            print("Available MCP tools:")
            print("-" * 50)

            for tool in result.tools:

                print(f"\nName: {tool.name}")
                print(f"Description: {tool.description}")
                print(f"Input Schema: {tool.inputSchema}")


if __name__ == "__main__":
    asyncio.run(main())