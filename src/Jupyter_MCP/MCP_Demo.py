import asyncio
import json

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


# Change this to your MCP server file
SERVER_SCRIPT = "server.py"


async def main():

    server_params = StdioServerParameters(
        command="python",
        args=[SERVER_SCRIPT],
    )

    async with stdio_client(server_params) as (read, write):

        async with ClientSession(read, write) as session:

            # Initialize MCP connection
            await session.initialize()

            # Get all tools exposed by your MCP server
            response = await session.list_tools()
            tools = response.tools

            print("\n========== MCP TEST CLIENT ==========\n")

            # Number the tools
            for i, tool in enumerate(tools, start=1):
                print(f"{i}. {tool.name}")

            print("\n=====================================")

            while True:

                try:
                    choice = input("\nEnter tool number (q to quit): ").strip()

                    if choice.lower() == "q":
                        break

                    choice = int(choice)

                    if choice < 1 or choice > len(tools):
                        print("Invalid tool number.")
                        continue

                    tool = tools[choice - 1]

                    print(f"\nSelected: {tool.name}")
                    print(f"Description: {tool.description}")

                    # Show expected arguments
                    print("\nArguments schema:")
                    print(json.dumps(tool.inputSchema, indent=2))

                    # Get arguments from user
                    args_input = input("\nEnter arguments as JSON ({} if none): ").strip()

                    if not args_input:
                        args_input = "{}"

                    try:
                        arguments = json.loads(args_input)
                    except json.JSONDecodeError:
                        print("Invalid JSON.")
                        continue

                    print("\nCalling MCP tool...\n")

                    # Call the MCP tool
                    result = await session.call_tool(
                        tool.name,
                        arguments
                    )

                    print("========== RESULT ==========")

                    for content in result.content:

                        if hasattr(content, "text"):
                            print(content.text)
                        else:
                            print(content)

                    print("============================")

                except ValueError:
                    print("Please enter a number.")

                except Exception as e:
                    print(f"\nERROR: {type(e).__name__}: {e}")


if __name__ == "__main__":
    asyncio.run(main())