"""
Real Haystack integration for the History Day scenario.

This module is intentionally small and focused:
- converts scenario-compatible tools into real `haystack` Tool objects
- invokes tool calls through real Haystack `ToolInvoker`
- returns normalized observations that the scenario orchestrator can reuse

Unlike the compatibility-only adapter, this module depends on the actual
`haystack-ai` package and is the real integration point for the scenario.
"""

from __future__ import annotations

import json
from ast import literal_eval
from typing import Any, Iterable

from haystack.components.tools import ToolInvoker
from haystack.dataclasses import ChatMessage
from haystack.dataclasses.chat_message import ToolCall
from haystack.tools import Tool

from services.history_day_haystack_adapter import (
    CompatibleAgentStep,
    CompatibleToolCall,
    HaystackCompatibleTool,
    HaystackCompatibleToolRegistry,
)


def to_haystack_tool(tool: HaystackCompatibleTool) -> Tool:
    """Convert one scenario-compatible tool into a real Haystack Tool."""
    return Tool(
        name=tool.name,
        description=tool.description,
        parameters=tool.input_schema,
        function=tool.handler,
    )


def build_haystack_tools(tools: Iterable[HaystackCompatibleTool]) -> list[Tool]:
    """Convert multiple compatible tools into real Haystack tools."""
    return [to_haystack_tool(tool) for tool in tools]


def build_haystack_tools_from_registry(registry: HaystackCompatibleToolRegistry) -> list[Tool]:
    """Export one registry into a list of real Haystack Tool objects."""
    return build_haystack_tools(registry.list_tools())


def _normalize_arguments(arguments: str | dict[str, Any]) -> dict[str, Any]:
    if isinstance(arguments, dict):
        return arguments
    if not arguments:
        return {}
    parsed = json.loads(arguments)
    return parsed if isinstance(parsed, dict) else {}


def invoke_tool_call_via_haystack(
    *,
    tool_call: CompatibleToolCall,
    registry: HaystackCompatibleToolRegistry,
) -> dict[str, Any]:
    """
    Invoke one tool call through the real Haystack ToolInvoker.

    Returns a normalized observation payload suitable for scenario orchestration.
    """
    tool = registry.get(tool_call.name)
    if tool is None:
        return {
            "tool_call_id": tool_call.id,
            "tool_name": tool_call.name,
            "error": True,
            "result": {"error": f"Unknown tool: {tool_call.name}", "tool": tool_call.name},
            "result_text": "",
        }

    haystack_tool = to_haystack_tool(tool)
    haystack_call = ToolCall(
        tool_name=tool_call.name,
        arguments=_normalize_arguments(tool_call.arguments),
        id=tool_call.id,
    )
    assistant_message = ChatMessage.from_assistant(tool_calls=[haystack_call])
    invoker = ToolInvoker(tools=[haystack_tool], raise_on_failure=False, convert_result_to_json_string=False)
    output = invoker.run(messages=[assistant_message])
    tool_messages = output.get("tool_messages") or []
    if not tool_messages:
        return {
            "tool_call_id": tool_call.id,
            "tool_name": tool_call.name,
            "error": True,
            "result": {"error": "Haystack ToolInvoker returned no tool messages", "tool": tool_call.name},
            "result_text": "",
        }

    tool_message = tool_messages[0]
    tool_results = tool_message.tool_call_results
    if not tool_results:
        return {
            "tool_call_id": tool_call.id,
            "tool_name": tool_call.name,
            "error": True,
            "result": {"error": "Haystack tool message has no tool results", "tool": tool_call.name},
            "result_text": "",
        }

    result_part = tool_results[0]
    result_raw = result_part.result
    error = bool(result_part.error)
    try:
        parsed_result = json.loads(result_raw)
        result_payload = parsed_result if isinstance(parsed_result, dict) else {"result": parsed_result}
    except Exception:
        try:
            parsed_result = literal_eval(result_raw)
            result_payload = parsed_result if isinstance(parsed_result, dict) else {"result": parsed_result}
        except Exception:
            result_payload = {"result": result_raw}

    return {
        "tool_call_id": tool_call.id,
        "tool_name": tool_call.name,
        "error": error,
        "result": result_payload,
        "result_text": str(result_raw),
        "haystack_tool_message": tool_message,
    }


def dispatch_agent_step_via_haystack(
    *,
    step: CompatibleAgentStep,
    registry: HaystackCompatibleToolRegistry,
) -> list[dict[str, Any]]:
    """Execute all tool calls from a normalized step via real Haystack ToolInvoker."""
    if step.step_type != "tool_calls":
        return []
    return [
        invoke_tool_call_via_haystack(tool_call=tool_call, registry=registry)
        for tool_call in step.tool_calls
    ]
