from __future__ import annotations

from services import kb_ingestion_pipeline as pipeline


def test_extract_structured_blocks_keeps_sections_and_tables():
    text = (
        "# Camera\n\n"
        "The diaphragm controls light and depth of field.\n\n"
        "| f-stop | effect |\n"
        "| --- | --- |\n"
        "| 2.8 | blur |\n"
        "| 8 | sharp |\n\n"
        "## Lens\n\n"
        "Lens selection changes perspective.\n"
    )

    blocks = pipeline.extract_structured_blocks(text, fallback_headings=["Camera"])

    assert len(blocks) == 3
    assert blocks[0].block_type == "prose"
    assert blocks[0].heading_path == ["Camera"]
    assert blocks[1].block_type == "table"
    assert blocks[1].is_table is True
    assert blocks[1].heading_path == ["Camera"]
    assert blocks[2].heading_path == ["Camera", "Lens"]


def test_build_chunks_adds_heading_prefix_and_table_metadata():
    text = (
        "# Camera\n\n"
        "The diaphragm controls light and depth of field. "
        "This paragraph is intentionally long so that it needs chunking. "
        "The camera manual explains aperture, exposure, focus, and composition.\n\n"
        "| f-stop | effect |\n"
        "| --- | --- |\n"
        "| 2.8 | blur |\n"
        "| 8 | sharp |\n"
    )
    document = pipeline.normalize_document(
        filename="camera.pdf",
        text=text,
        parser_backend="docling",
        source_format="PDF",
        structure={"headings": ["Camera"]},
    )

    chunks = pipeline.build_chunks(document, chunk_size=130, overlap=20)

    assert len(chunks) >= 2
    assert chunks[0].text.startswith("[Раздел: Camera]")
    assert any(chunk.is_table for chunk in chunks)
    assert all(chunk.meta["char_count"] >= 1 for chunk in chunks)
    assert all(chunk.meta["token_estimate"] >= 1 for chunk in chunks)
