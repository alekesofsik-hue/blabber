from __future__ import annotations

from repositories.config_repo import get_all as config_get_all
from services.config_registry import get_config_registry
from services import kb_rollout


def test_kb_rollout_flags_seeded_in_db(db):
    rows = config_get_all(category="kb")
    values = {row["key"]: row["value"] for row in rows}

    assert values["kb_docling_enabled"] == "false"
    assert values["kb_docling_fallback_enabled"] == "true"
    assert values["kb_docling_rollout_stage"] == "legacy"
    assert values["kb_docling_canary_telegram_ids"] == "[]"
    assert values["kb_docling_structured_chunks_enabled"] == "false"
    assert values["kb_doc_summary_enabled"] == "false"
    assert values["kb_doc_summary_save_enabled"] == "false"
    assert values["kb_structured_retrieval_enabled"] == "false"
    assert values["kb_max_doc_size_kb"] == "3072"


def test_doc_parser_mode_defaults_to_legacy_only(db):
    reg = get_config_registry()
    reg.load(None)

    assert kb_rollout.is_docling_enabled() is False
    assert kb_rollout.is_docling_fallback_enabled() is True
    assert kb_rollout.get_doc_parser_mode() == "legacy_only"


def test_doc_parser_mode_can_switch_to_docling_with_fallback(db):
    reg = get_config_registry()
    reg.load(None)
    reg.set("kb_docling_enabled", True, "bool", "kb")
    reg.set("kb_docling_fallback_enabled", True, "bool", "kb")
    reg.set("kb_docling_rollout_stage", "global", "str", "kb")

    assert kb_rollout.get_doc_parser_mode() == "docling_with_legacy_fallback"
    assert kb_rollout.is_docling_active_for_user(123) is True


def test_doc_parser_mode_can_switch_to_docling_only(db):
    reg = get_config_registry()
    reg.load(None)
    reg.set("kb_docling_enabled", True, "bool", "kb")
    reg.set("kb_docling_fallback_enabled", False, "bool", "kb")
    reg.set("kb_docling_rollout_stage", "global", "str", "kb")

    assert kb_rollout.get_doc_parser_mode() == "docling_only"
    assert kb_rollout.is_docling_active_for_user(123) is True


def test_canary_rollout_allows_only_selected_users(db):
    reg = get_config_registry()
    reg.load(None)
    reg.set("kb_docling_enabled", True, "bool", "kb")
    reg.set("kb_docling_rollout_stage", "canary", "str", "kb")
    reg.set("kb_docling_canary_telegram_ids", [101, 202], "json", "kb")

    assert kb_rollout.get_canary_telegram_ids() == [101, 202]
    assert kb_rollout.is_docling_active_for_user(101) is True
    assert kb_rollout.is_docling_active_for_user(999) is False


def test_soft_failure_and_ux_policies_are_safe_by_default(db):
    reg = get_config_registry()
    reg.load(None)

    assert kb_rollout.should_continue_after_docling_failure() is True
    assert kb_rollout.should_continue_without_summary() is True
    assert kb_rollout.should_send_summary_after_index_success() is True


def test_rollout_snapshot_reflects_config(db):
    reg = get_config_registry()
    reg.load(None)
    reg.set("kb_docling_enabled", True, "bool", "kb")
    reg.set("kb_docling_rollout_stage", "canary", "str", "kb")
    reg.set("kb_docling_canary_telegram_ids", [7, 8], "json", "kb")
    reg.set("kb_docling_structured_chunks_enabled", True, "bool", "kb")
    reg.set("kb_doc_summary_enabled", True, "bool", "kb")
    reg.set("kb_doc_summary_save_enabled", True, "bool", "kb")
    reg.set("kb_structured_retrieval_enabled", True, "bool", "kb")

    snapshot = kb_rollout.get_rollout_snapshot()
    assert snapshot["docling_enabled"] is True
    assert snapshot["rollout_stage"] == "canary"
    assert snapshot["canary_user_count"] == 2
    assert snapshot["docling_structured_chunks_enabled"] is True
    assert snapshot["doc_summary_enabled"] is True
    assert snapshot["doc_summary_save_enabled"] is True
    assert snapshot["structured_retrieval_enabled"] is True
    assert snapshot["doc_parser_mode"] == "docling_with_legacy_fallback"


def test_log_rollout_event_renames_reserved_logging_keys(db, caplog):
    reg = get_config_registry()
    reg.load(None)

    with caplog.at_level("INFO", logger="blabber"):
        kb_rollout.log_rollout_event(
            "kb_test_reserved_keys",
            filename="demo.pdf",
            module="test_module",
            message="demo",
        )

    record = next(r for r in caplog.records if r.msg == "kb_test_reserved_keys")
    assert getattr(record, "kb_filename") == "demo.pdf"
    assert getattr(record, "kb_module") == "test_module"
    assert getattr(record, "kb_message") == "demo"
