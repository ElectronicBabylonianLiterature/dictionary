import pytest

from ebl.transliteration.application.line_schemas import dump_line, load_line
from ebl.transliteration.application.token_schemas import dump_tokens
from ebl.transliteration.domain.atf import Ruling
from ebl.transliteration.domain.enclosure_tokens import (
    Determinative,
    DocumentOrientedGloss,
)
from ebl.transliteration.domain.labels import LineNumberLabel
from ebl.transliteration.domain.line import (
    ControlLine,
    EmptyLine,
    TextLine,
    LooseDollarLine,
    ImageDollarLine,
    RulingDollarLine,
)
from ebl.transliteration.domain.sign_tokens import Reading
from ebl.transliteration.domain.tokens import ValueToken
from ebl.transliteration.domain.word_tokens import LoneDeterminative, Word

LINES = [
    (
        ControlLine.of_single("@", ValueToken("obverse")),
        {
            "type": "ControlLine",
            "prefix": "@",
            "content": dump_tokens([ValueToken("obverse")]),
        },
    ),
    (
        TextLine.of_iterable(
            LineNumberLabel.from_atf("1."),
            [
                DocumentOrientedGloss("{("),
                Word("bu", parts=[Reading.of("bu")]),
                LoneDeterminative("{d}", parts=[Determinative([Reading.of("d")]),],),
            ],
        ),
        {
            "type": "TextLine",
            "prefix": "1.",
            "content": dump_tokens(
                [
                    DocumentOrientedGloss("{("),
                    Word("bu", parts=[Reading.of("bu")]),
                    LoneDeterminative(
                        "{d}", parts=[Determinative([Reading.of("d")]),],
                    ),
                ]
            ),
        },
    ),
    (EmptyLine(), {"type": "EmptyLine", "prefix": "", "content": []}),
    (
        LooseDollarLine.of_single("(end of side)"),
        {
            "type": "LooseDollarLine",
            "prefix": "$",
            "content": dump_tokens([ValueToken("(end of side)")]),
            "text": "end of side",
        },
    ),
    (
        ImageDollarLine.of_single("1", "a", "great"),
        {
            "type": "ImageDollarLine",
            "prefix": "$",
            "content": dump_tokens([ValueToken("( image 1a = great)")]),
            "number": "1",
            "letter": "a",
            "text": "great",
        },
    ),
    (
        ImageDollarLine.of_single("1", None, "great"),
        {
            "type": "ImageDollarLine",
            "prefix": "$",
            "content": dump_tokens([ValueToken("( image 1 = great)")]),
            "number": "1",
            "letter": None,
            "text": "great",
        },
    ),
    (
        RulingDollarLine.of_single("double"),
        {
            "type": "RulingDollarLine",
            "prefix": "$",
            "content": dump_tokens([ValueToken("double ruling")]),
            "number": "double",
        },
    ),
]


@pytest.mark.parametrize("line,expected", LINES)
def test_dump_line(line, expected):
    assert dump_line(line) == expected


@pytest.mark.parametrize("expected,data", LINES)
def test_load_line(expected, data):
    assert load_line(data) == expected
