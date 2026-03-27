from __future__ import annotations

from services.history_day_haystack_adapter import (
    CompatibleAgentStep,
    CompatibleToolCall,
    HaystackCompatibleTool,
    HaystackCompatibleToolRegistry,
    build_agent_messages,
    dispatch_agent_step,
    parse_openai_message,
)


def test_tool_registry_registers_and_exports_openai_schema():
    registry = HaystackCompatibleToolRegistry()
    registry.register(
        HaystackCompatibleTool(
            name="history_fact",
            description="Возвращает исторический факт дня",
            input_schema={
                "type": "object",
                "properties": {"date": {"type": "string"}},
                "required": ["date"],
            },
            handler=lambda date: {"date": date, "fact": "test"},
        )
    )

    schemas = registry.openai_schemas()
    assert len(schemas) == 1
    assert schemas[0]["function"]["name"] == "history_fact"
    assert schemas[0]["function"]["parameters"]["required"] == ["date"]


def test_tool_registry_invokes_tool_from_json_arguments():
    registry = HaystackCompatibleToolRegistry()
    registry.register(
        HaystackCompatibleTool(
            name="history_fact",
            description="Возвращает исторический факт дня",
            input_schema={"type": "object", "properties": {"date": {"type": "string"}}},
            handler=lambda date="": {"date": date, "fact": "ok"},
        )
    )

    result = registry.invoke("history_fact", '{"date":"03-26"}')
    assert result["date"] == "03-26"
    assert result["fact"] == "ok"


def test_tool_registry_reports_bad_arguments():
    registry = HaystackCompatibleToolRegistry()
    registry.register(
        HaystackCompatibleTool(
            name="history_fact",
            description="Возвращает исторический факт дня",
            input_schema={"type": "object", "properties": {"date": {"type": "string"}}},
            handler=lambda date: {"date": date},
        )
    )

    result = registry.invoke("history_fact", "{bad json")
    assert "error" in result
    assert "invalid JSON" in result["error"]


def test_build_agent_messages_appends_context_blocks_to_system_prompt():
    messages = build_agent_messages(
        system_prompt="Ты ассистент истории дня",
        user_message="Что произошло сегодня?",
        context_blocks=["[Память]\nПользователь уже спрашивал про март"],
    )

    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert "[Память]" in messages[0]["content"]
    assert messages[1]["role"] == "user"


def test_parse_openai_message_as_final_answer():
    message = type("Msg", (), {"content": "Готовый ответ", "tool_calls": []})()
    step = parse_openai_message(message)

    assert isinstance(step, CompatibleAgentStep)
    assert step.step_type == "final"
    assert step.content == "Готовый ответ"
    assert step.tool_calls == []


def test_parse_openai_message_as_tool_calls():
    tool_call = type(
        "ToolCall",
        (),
        {
            "id": "call_1",
            "function": type("Fn", (), {"name": "history_fact", "arguments": '{"date":"03-26"}'})(),
        },
    )()
    message = type("Msg", (), {"content": "", "tool_calls": [tool_call]})()

    step = parse_openai_message(message)
    assert step.step_type == "tool_calls"
    assert len(step.tool_calls) == 1
    assert isinstance(step.tool_calls[0], CompatibleToolCall)
    assert step.tool_calls[0].name == "history_fact"


def test_dispatch_agent_step_executes_all_tool_calls():
    registry = HaystackCompatibleToolRegistry()
    registry.register_many(
        [
            HaystackCompatibleTool(
                name="history_fact",
                description="Возвращает факт",
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
            CompatibleToolCall(id="call_2", name="history_memory_lookup", arguments='{"query":"Напомни"}'),
        ],
    )

    observations = dispatch_agent_step(registry=registry, step=step)
    assert len(observations) == 2
    assert observations[0]["result"]["kind"] == "fact"
    assert observations[1]["result"]["kind"] == "memory"
