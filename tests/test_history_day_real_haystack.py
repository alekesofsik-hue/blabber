from __future__ import annotations

from haystack.tools import Tool as HaystackTool

from services.history_day_haystack_adapter import (
    CompatibleAgentStep,
    CompatibleToolCall,
    HaystackCompatibleTool,
    HaystackCompatibleToolRegistry,
)
from services.history_day_real_haystack import (
    build_haystack_tools_from_registry,
    dispatch_agent_step_via_haystack,
    invoke_tool_call_via_haystack,
    to_haystack_tool,
)


def test_to_haystack_tool_converts_compatible_tool():
    tool = HaystackCompatibleTool(
        name="history_fact",
        description="Возвращает факт дня",
        input_schema={
            "type": "object",
            "properties": {"date": {"type": "string"}},
            "required": ["date"],
        },
        handler=lambda date="": {"date": date, "fact": "ok"},
    )

    haystack_tool = to_haystack_tool(tool)
    assert isinstance(haystack_tool, HaystackTool)
    assert haystack_tool.name == "history_fact"
    assert haystack_tool.description == "Возвращает факт дня"


def test_build_haystack_tools_from_registry_exports_all_tools():
    registry = HaystackCompatibleToolRegistry()
    registry.register_many(
        [
            HaystackCompatibleTool(
                name="history_fact",
                description="Возвращает факт дня",
                input_schema={"type": "object", "properties": {"date": {"type": "string"}}},
                handler=lambda date="": {"kind": "fact", "date": date},
            ),
            HaystackCompatibleTool(
                name="history_memory_lookup",
                description="Ищет по памяти",
                input_schema={"type": "object", "properties": {"query": {"type": "string"}}},
                handler=lambda query="": {"kind": "memory", "query": query},
            ),
        ]
    )

    tools = build_haystack_tools_from_registry(registry)
    assert len(tools) == 2
    assert all(isinstance(tool, HaystackTool) for tool in tools)


def test_invoke_tool_call_via_haystack_executes_real_toolinvoker():
    registry = HaystackCompatibleToolRegistry()
    registry.register(
        HaystackCompatibleTool(
            name="history_fact",
            description="Возвращает факт дня",
            input_schema={
                "type": "object",
                "properties": {"date": {"type": "string"}},
                "required": ["date"],
            },
            handler=lambda date="": {"kind": "fact", "date": date},
        )
    )

    observation = invoke_tool_call_via_haystack(
        tool_call=CompatibleToolCall(id="call_1", name="history_fact", arguments='{"date":"03-26"}'),
        registry=registry,
    )

    assert observation["tool_name"] == "history_fact"
    assert observation["error"] is False
    assert observation["result"]["kind"] == "fact"
    assert observation["result"]["date"] == "03-26"


def test_invoke_tool_call_via_haystack_reports_unknown_tool():
    registry = HaystackCompatibleToolRegistry()

    observation = invoke_tool_call_via_haystack(
        tool_call=CompatibleToolCall(id="call_2", name="unknown_tool", arguments="{}"),
        registry=registry,
    )

    assert observation["error"] is True
    assert "Unknown tool" in observation["result"]["error"]


def test_dispatch_agent_step_via_haystack_executes_multiple_calls():
    registry = HaystackCompatibleToolRegistry()
    registry.register_many(
        [
            HaystackCompatibleTool(
                name="history_fact",
                description="Возвращает факт дня",
                input_schema={"type": "object", "properties": {"date": {"type": "string"}}},
                handler=lambda date="": {"kind": "fact", "date": date},
            ),
            HaystackCompatibleTool(
                name="history_memory_lookup",
                description="Ищет по памяти",
                input_schema={"type": "object", "properties": {"query": {"type": "string"}}},
                handler=lambda query="": {"kind": "memory", "query": query},
            ),
        ]
    )

    step = CompatibleAgentStep(
        step_type="tool_calls",
        tool_calls=[
            CompatibleToolCall(id="call_1", name="history_fact", arguments='{"date":"03-26"}'),
            CompatibleToolCall(id="call_2", name="history_memory_lookup", arguments='{"query":"Напомни год"}'),
        ],
    )

    observations = dispatch_agent_step_via_haystack(step=step, registry=registry)
    assert len(observations) == 2
    assert observations[0]["result"]["kind"] == "fact"
    assert observations[1]["result"]["kind"] == "memory"
