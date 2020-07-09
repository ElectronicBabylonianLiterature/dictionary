import pytest  # pyre-ignore

from ebl.transliteration.domain import atf
from ebl.transliteration.domain.dollar_line import (
    ImageDollarLine,
    LooseDollarLine,
    RulingDollarLine,
    ScopeContainer,
    StateDollarLine,
)
from ebl.transliteration.domain.tokens import ValueToken


def test_loose_dollar_line():
    text = "this is a loose line"
    loose_line = LooseDollarLine(text)

    assert loose_line.content == (ValueToken.of(f" ({text})"),)
    assert loose_line.text == text
    assert loose_line.atf == f"$ ({text})"
    assert loose_line.display_value == "(this is a loose line)"


def test_image_dollar_line():
    image = ImageDollarLine("1", "a", "great")

    assert image.content == (ValueToken.of(" (image 1a = great)"),)
    assert image.number == "1"
    assert image.letter == "a"
    assert image.text == "great"
    assert image.atf == "$ (image 1a = great)"
    assert image.display_value == "(image 1a = great)"


def test_ruling_dollar_line():
    ruling_line = RulingDollarLine(atf.Ruling.DOUBLE)

    assert ruling_line.content == (ValueToken.of(" double ruling"),)
    assert ruling_line.number == atf.Ruling.DOUBLE
    assert ruling_line.status is None
    assert ruling_line.atf == "$ double ruling"
    assert ruling_line.display_value == "double ruling"


def test_ruling_dollar_line_status():
    ruling_line = RulingDollarLine(
        atf.Ruling.DOUBLE, atf.DollarStatus.EMENDED_NOT_COLLATED
    )

    assert ruling_line.content == (ValueToken.of(" double ruling !"),)
    assert ruling_line.number == atf.Ruling.DOUBLE
    assert ruling_line.status == atf.DollarStatus.EMENDED_NOT_COLLATED
    assert ruling_line.atf == "$ double ruling !"
    assert ruling_line.display_value == "double ruling !"


def test_strict_dollar_line_with_none():
    scope = ScopeContainer(atf.Object.OBJECT, "what")
    actual = StateDollarLine(None, atf.Extent.SEVERAL, scope, None, None)

    assert actual.scope.content == atf.Object.OBJECT
    assert actual.scope.text == "what"
    assert actual.content == (ValueToken.of(" several object what"),)
    assert actual.atf == "$ several object what"
    assert actual.display_value == "several object what"


def test_state_dollar_line():
    actual = StateDollarLine(
        atf.Qualification.AT_LEAST,
        atf.Extent.SEVERAL,
        ScopeContainer(atf.Scope.COLUMNS, ""),
        atf.State.BLANK,
        atf.DollarStatus.UNCERTAIN,
    )

    assert actual.qualification == atf.Qualification.AT_LEAST
    assert actual.scope.content == atf.Scope.COLUMNS
    assert actual.scope.text == ""
    assert actual.extent == atf.Extent.SEVERAL
    assert actual.state == atf.State.BLANK
    assert actual.status == atf.DollarStatus.UNCERTAIN
    assert actual.content == (ValueToken.of(" at least several columns blank ?"),)
    assert actual.atf == "$ at least several columns blank ?"
    assert actual.display_value == "at least several columns blank ?"


def test_state_dollar_line_content():
    scope = ScopeContainer(atf.Surface.OBVERSE)
    actual = StateDollarLine(
        atf.Qualification.AT_LEAST,
        1,
        scope,
        atf.State.BLANK,
        atf.DollarStatus.UNCERTAIN,
    )

    assert actual.content == (ValueToken.of(" at least 1 obverse blank ?"),)
    assert actual.display_value == "at least 1 obverse blank ?"


def test_state_dollar_line_non_empty_string_error():
    with pytest.raises(ValueError):
        StateDollarLine(
            None, None, ScopeContainer(atf.Surface.REVERSE, "test"), None, None
        )


def test_state_dollar_line_range():
    scope = ScopeContainer(atf.Scope.LINES)
    actual = StateDollarLine(
        None,
        (2, 4),
        scope,
        atf.State.MISSING,
        None,
    )

    assert actual.content == (ValueToken.of(" 2-4 lines missing"),)
    assert actual.display_value == "2-4 lines missing"
