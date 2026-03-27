"""
Haystack-compatible adapter layer for the History Day scenario.

This module does not depend on the real `haystack` package. Instead, it provides
small compatibility primitives that make the scenario architecture explainable in
Haystack terms:
- tool registry
- tool invocation wrapper
- agent-step parsing
- OpenAI-compatible tool schema export

The goal is architectural compatibility and explicit mapping, not a literal
replacement of the Haystack runtime.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Callable, Iterable


ToolHandler = Callable[..., Any]


@dataclass(frozen=True)
class HaystackCompatibleTool:
    """Tool definition that can be exported to OpenAI-style or documented as Haystack-like."""

    name: str
    description: str
    input_schema: dict[str, Any]
    handler: ToolHandler
    origin: str = "history_day"
    compatibility_note: str = (
        "Совместимый интерфейс для сценария `История дня`; не является runtime-ядром Haystack."
    )

    def to_openai_tool(self) -> dict[str, Any]:
        """Return an OpenAI function-calling compatible schema."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.input_schema,
            },
        }

    def to_haystack_component_spec(self) -> dict[str, Any]:
        """Return a lightweight spec for documentation/debugging."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
            "origin": self.origin,
            "compatibility_note": self.compatibility_note,
        }


class HaystackCompatibleToolRegistry:
    """Registry for scenario tools exposed via the compatibility layer."""

    def __init__(self) -> None:
        self._tools: dict[str, HaystackCompatibleTool] = {}

    def register(self, tool: HaystackCompatibleTool) -> None:
        """Register or replace one tool by name."""
        self._tools[tool.name] = tool

    def register_many(self, tools: Iterable[HaystackCompatibleTool]) -> None:
        """Register multiple tools preserving last-write-wins semantics."""
        for tool in tools:
            self.register(tool)

    def get(self, name: str) -> HaystackCompatibleTool | None:
        """Return one registered tool or None."""
        return self._tools.get(name)

    def list_tools(self) -> list[HaystackCompatibleTool]:
        """Return all registered tools sorted by name for deterministic output."""
        return [self._tools[name] for name in sorted(self._tools)]

    def openai_schemas(self) -> list[dict[str, Any]]:
        """Export all registered tools in OpenAI function-calling format."""
        return [tool.to_openai_tool() for tool in self.list_tools()]

    def haystack_component_specs(self) -> list[dict[str, Any]]:
        """Export lightweight specs for documentation/debugging."""
        return [tool.to_haystack_component_spec() for tool in self.list_tools()]

    def invoke(self, name: str, arguments: dict[str, Any] | str | None = None) -> dict[str, Any]:
        """
        Invoke one registered tool and always return a JSON-serializable dict.

        Accepted argument forms:
        - dict
        - JSON string
        - None
        """
        tool = self.get(name)
        if tool is None:
            return {"error": f"Unknown tool: {name}", "tool": name}

        if arguments is None:
            parsed_args: dict[str, Any] = {}
        elif isinstance(arguments, str):
            try:
                parsed = json.loads(arguments)
                parsed_args = parsed if isinstance(parsed, dict) else {}
            except json.JSONDecodeError:
                return {"error": f"Bad arguments for {name}: invalid JSON", "tool": name}
        elif isinstance(arguments, dict):
            parsed_args = arguments
        else:
            return {"error": f"Bad arguments for {name}: unsupported type", "tool": name}

        try:
            result = tool.handler(**parsed_args)
        except TypeError as exc:
            return {"error": f"Bad arguments for {name}: {exc}", "tool": name}
        except Exception as exc:
            return {"error": f"Tool {name} failed: {exc}", "tool": name}

        if isinstance(result, dict):
            return result
        return {"result": result, "tool": name}


@dataclass(frozen=True)
class CompatibleToolCall:
    """Normalized representation of one tool call requested by the model."""

    id: str
    name: str
    arguments: str


@dataclass(frozen=True)
class CompatibleAgentStep:
    """Normalized representation of one model step: final answer or tool calls."""

    step_type: str
    content: str = ""
    tool_calls: list[CompatibleToolCall] = field(default_factory=list)


def build_agent_messages(
    *,
    system_prompt: str,
    user_message: str,
    context_blocks: list[str] | None = None,
) -> list[dict[str, str]]:
    """
    Build initial messages for a Haystack-like scenario flow.

    `context_blocks` are appended to the system prompt so the orchestrator can
    inject retrieval results without changing the user message itself.
    """
    context_blocks = context_blocks or []
    full_system_prompt = system_prompt.strip()
    if context_blocks:
        full_system_prompt += "\n\n" + "\n\n".join(block.strip() for block in context_blocks if block.strip())
    return [
        {"role": "system", "content": full_system_prompt},
        {"role": "user", "content": user_message},
    ]


def parse_openai_message(message: Any) -> CompatibleAgentStep:
    """
    Normalize an OpenAI-compatible response message into one agent step.

    Expected shape:
    - final answer: `message.content`
    - tool calls: `message.tool_calls[*].id`, `.function.name`, `.function.arguments`
    """
    tool_calls = getattr(message, "tool_calls", None) or []
    if not tool_calls:
        return CompatibleAgentStep(
            step_type="final",
            content=str(getattr(message, "content", "") or ""),
            tool_calls=[],
        )

    normalized_calls = [
        CompatibleToolCall(
            id=str(tc.id),
            name=str(tc.function.name),
            arguments=str(tc.function.arguments or "{}"),
        )
        for tc in tool_calls
    ]
    return CompatibleAgentStep(
        step_type="tool_calls",
        content=str(getattr(message, "content", "") or ""),
        tool_calls=normalized_calls,
    )


def dispatch_agent_step(
    *,
    registry: HaystackCompatibleToolRegistry,
    step: CompatibleAgentStep,
) -> list[dict[str, Any]]:
    """
    Execute all tool calls from one normalized step and return observations.

    The returned list is suitable for feeding back into a model loop or for
    scenario-level logging/debugging.
    """
    if step.step_type != "tool_calls":
        return []

    observations: list[dict[str, Any]] = []
    for call in step.tool_calls:
        result = registry.invoke(call.name, call.arguments)
        observations.append(
            {
                "tool_call_id": call.id,
                "tool_name": call.name,
                "arguments": call.arguments,
                "result": result,
            }
        )
    return observations
