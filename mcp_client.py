import asyncio
import json

from mcp import Client
from ollama import chat

from mcp_server import mcp


MODEL = "qwen3:4b"


# ==================================================
# TOOL DEFINITIONS GIVEN TO THE LLM
# ==================================================

MCP_TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "list_supported_universities",
            "description": (
                "List the universities supported by the "
                "Lebanon university guidance system."
            ),
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_official_programs",
            "description": (
                "Search approved official Lebanese university "
                "program pages for candidate majors."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "majors": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        }
                    }
                },
                "required": [
                    "majors"
                ]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_official_university_details",
            "description": (
                "Retrieve official tuition, admissions, "
                "financial-aid, and housing information "
                "for one supported university."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "short_name": {
                        "type": "string"
                    }
                },
                "required": [
                    "short_name"
                ]
            }
        }
    }
]


# ==================================================
# MCP TOOL EXECUTION
# ==================================================

async def call_mcp_tool(
    tool_name,
    arguments
):
    """
    Execute one tool through the MCP server.
    """

    async with Client(mcp) as client:

        result = await client.call_tool(
            tool_name,
            arguments
        )

        if result.is_error:
            raise RuntimeError(
                f"MCP tool failed: {tool_name}"
            )

        if not result.content:
            return {}

        # Our MCP server returns JSON as text content.
        text = result.content[0].text

        try:
            return json.loads(
                text
            )

        except json.JSONDecodeError:
            return {
                "text": text
            }


# ==================================================
# LLM FUNCTION CALLING
# ==================================================

async def function_calling_agent(
    user_request
):
    """
    Allow the LLM to choose an MCP tool,
    then execute that tool through MCP.
    """

    messages = [
        {
            "role": "system",
            "content": (
                "You are a university research assistant. "
                "Use the available tools when information "
                "must come from official university sources."
            )
        },
        {
            "role": "user",
            "content": user_request
        }
    ]

    response = chat(
        model=MODEL,
        messages=messages,
        tools=MCP_TOOL_SCHEMAS,
        think=False
    )

    tool_calls = response.message.tool_calls

    if not tool_calls:
        return {
            "message": response.message.content,
            "tool_used": None,
            "result": None
        }

    # For this student project, execute the first
    # requested tool call.
    tool_call = tool_calls[0]

    tool_name = tool_call.function.name

    arguments = tool_call.function.arguments

    print(
        f"LLM selected MCP tool: {tool_name}"
    )

    print(
        f"Tool arguments: {arguments}"
    )

    result = await call_mcp_tool(
        tool_name,
        arguments
    )

    return {
        "tool_used": tool_name,
        "arguments": arguments,
        "result": result
    }


# ==================================================
# SIMPLE TEST
# ==================================================

if __name__ == "__main__":

    async def main():

        result = await function_calling_agent(
            "Find universities that offer Computer Science."
        )

        print(
            "\nFUNCTION CALLING RESULT:\n"
        )

        print(
            json.dumps(
                result,
                indent=2,
                ensure_ascii=False
            )
        )

    asyncio.run(
        main()
    )
