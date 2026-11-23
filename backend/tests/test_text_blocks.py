from pfefinder.rag.ingestion.text_blocks import split_into_blocks


def _doc(pages: int, size: int) -> str:
    return "\n".join(f"[page {i}]\n" + "x" * size for i in range(1, pages + 1))


def test_blocks_respect_limit_and_cut_between_pages():
    blocks = split_into_blocks(_doc(10, 900), 2500)
    assert all(len(b) <= 2500 for b in blocks)
    assert all(b.lstrip().startswith("[page") for b in blocks)
    assert sum(b.count("[page") for b in blocks) == 10


def test_short_text_is_one_block():
    assert len(split_into_blocks(_doc(2, 100), 20_000)) == 1


def test_oversized_page_is_split_as_last_resort():
    assert all(len(b) <= 500 for b in split_into_blocks("[page 1]\n" + "y" * 1800, 500))
