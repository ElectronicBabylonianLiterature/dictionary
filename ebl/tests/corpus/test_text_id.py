import pytest  # pyre-ignore[21]

from ebl.corpus.domain.text import TextId


@pytest.mark.parametrize(  # pyre-ignore[56]
    "text_id,expected", [(TextId(0, 0), "0.0"), (TextId(5, 8), "V.8")]
)
def test_str(text_id, expected) -> None:
    assert str(text_id) == expected
