
import asyncio
from typing import Optional, Any
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters, types
from anthropic import AsyncAnthropic
import sys
from mcp.client.stdio import stdio_client
from dotenv import load_dotenv
import json

from mcp.types import LoggingMessageNotificationParams
from pydantic import AnyUrl
from colorama import Fore, Style, init
from client.claude_client import chat, add_user_message, add_assistant_message, convert_mcp_to_tool_result

init(autoreset=True) # Automatically resets style after every print

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

load_dotenv()
CLAUDE_MODEL="claude-haiku-4-5-20251001"
client = AsyncAnthropic()

server_params = StdioServerParameters(
    command="uv",
    args=["run", "mcp server/server.py"],
)

class MCPClient:
    def __init__(
        self,
        command: str,
        args: list[str],
        env: Optional[dict] = None,
    ):
        self._command = command
        self._args = args
        self._env = env
        self._session: Optional[ClientSession] = None
        self._exit_stack: AsyncExitStack = AsyncExitStack()

    async def connect(self):
        server_params = StdioServerParameters(
            command=self._command,
            args=self._args,
            env=self._env
        )
        stdio_transport = await self._exit_stack.enter_async_context(
            stdio_client(server_params)
        )
        _stdio, _write = stdio_transport
        self._session = await self._exit_stack.enter_async_context(
            ClientSession(_stdio, _write, logging_callback= logging_callback)
        )
        await self._session.initialize()


    def session(self) -> ClientSession:
        if self._session is None:
            raise ConnectionError(
                "Client session not initialized or cache not populated. Call connect_to_server first."
            )
        return self._session

    async def list_tools(self) -> list[types.Tool]:
        result = await self.session().list_tools()
        return result.tools

    async def call_tool(
        self, tool_name: str, tool_input: dict
    ) -> types.CallToolResult | None:
        return await self.session().call_tool(tool_name, tool_input)

    async def list_prompts(self) -> list[types.Prompt]:
        result = await self.session().list_prompts()
        return result.prompts

    async def get_prompt(self, prompt_name, args: dict[str, str]):
        result = await self.session().get_prompt(prompt_name, args)
        return result.messages

    async def read_resource(self, uri: str) -> Any:
        result = await self.session().read_resource(AnyUrl(url= uri))
        resource =  result.contents[0]
        if isinstance(resource, types.TextResourceContents):
            if resource.mimeType == "application/json":
                return json.loads(resource.text)

            return resource.text
        return None

    async def cleanup(self):
        await self._exit_stack.aclose()
        self._session = None

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.cleanup()



# Converts MCP tools to a format compatible with Anthropic's tool specification.
# It converts MCP tool definitions → Anthropic tool schema
def convert_mcp_tools_to_anthropic(tools):
    anthropic_tools = []

    for tool in tools:
        anthropic_tools.append({
            "name": tool.name,
            "description": tool.description or "",
            "input_schema": tool.inputSchema
        })

    return anthropic_tools

async def logging_callback(params: LoggingMessageNotificationParams):
    print(f"[MCP LOG - {params.level}] {params.data}")


async def main():
    print("Starting MCP client...")
    async with MCPClient(
            # If using Python without UV, update command to 'python' and remove "run" from args.
            command="uv",
            args=["run", "server/server.py"],
    ) as mcp_client:
        tool_input = {
            "doc_id": "deposition.md"
        }
        mcp_tools = await mcp_client.list_tools()
        tools = convert_mcp_tools_to_anthropic(mcp_tools)
        #print("available tools:", tools)
        #print("Connected to MCP server. Type 'exit' to quit.\n")
        messages = []
        while True:
            print("----------------------------------------")
            #print("messages so far:")
            #for message in messages:
                #print(message)
                #print(json.dumps(message, indent=2))


            user_input = input(Fore.CYAN  +"You: "+Fore.YELLOW)
            if user_input == "exit":
                break

            add_user_message(messages,user_input)

            claude_response = await chat(messages = messages, tools=tools)
            add_assistant_message(messages, claude_response)

            # Handle tool calls
            # when multiple tool calls happen in a single turn.
            tool_results = []
            for content in claude_response.content:
                if content.type == "tool_use":
                    tool_result = await mcp_client.call_tool(
                        content.name,
                        content.input
                    )
                    tool_results.append(
                        # Converts MCP result object → Anthropic tool_result message
                        convert_mcp_to_tool_result(tool_result, content.id)
                    )
                    #print("tool result raw:", tool_result)


            if tool_results:
                # Send the tool result back to Claude and get the next response
                messages.extend(tool_results)
                claude_response = await chat(messages=messages, tools=tools)
                add_assistant_message(messages, claude_response)

            print(Fore.MAGENTA +  "AI Notes-Assistance :")
            print("  "+Fore.GREEN +  claude_response.content[0].text)


# uv run -m client.client
if __name__ == "__main__":
    asyncio.run(main())

    """
    Sample prompts
    1) Save a note titled "Meeting Notes" with content "Discussed AI roadmap and hiring plan"
    2) I had an idea about a startup that uses AI for code reviews, save it as a note
    3) Show me all my notes
    4) update a note titled "Meeting Notes" with some random notes
    5) Find notes related to AI
    6) Did I write anything about hiring?
    7) Find my notes about AI and summarize them
    8) Save a note (should reply with What title and content should I save?)
    
    """