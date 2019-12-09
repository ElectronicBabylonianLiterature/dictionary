import pytest

from ebl.dictionary.domain.word import WordId
from ebl.transliteration.application.line_schemas import dump_lines
from ebl.transliteration.application.text_schema import TextSchema
from ebl.transliteration.domain.enclosure_tokens import Erasure, Side
from ebl.transliteration.domain.labels import LineNumberLabel
from ebl.transliteration.domain.language import Language
from ebl.transliteration.domain.line import ControlLine, EmptyLine, TextLine
from ebl.transliteration.domain.sign_tokens import Reading
from ebl.transliteration.domain.text import Text
from ebl.transliteration.domain.tokens import (
    Joiner,
    LanguageShift,
    LineContinuation,
    ValueToken,
)
from ebl.transliteration.domain.word_tokens import LoneDeterminative, Partial, Word


def test_dump_line():
    text = Text(
        (
            TextLine.of_iterable(
                LineNumberLabel.from_atf("1."),
                [
                    Word(
                        "ha-am",
                        parts=[Reading.of("ha"), Joiner.hyphen(), Reading.of("am"),],
                    )
                ],
            ),
            EmptyLine(),
            ControlLine.of_single("$", ValueToken(" single ruling")),
        ),
        "1.0.0",
    )

    assert TextSchema().dump(text) == {
        "lines": dump_lines(text.lines),
        "parser_version": text.parser_version,
    }


@pytest.mark.parametrize(
    "lines",
    [
        [EmptyLine()],
        [ControlLine.of_single("$", ValueToken(" single ruling"))],
        [
            TextLine.of_iterable(
                LineNumberLabel.from_atf("1."),
                [
                    Word("nu", unique_lemma=(WordId("nu I"),)),
                    Word("nu", alignment=1),
                    LanguageShift("%sux"),
                    LoneDeterminative(
                        "{nu}",
                        language=Language.SUMERIAN,
                        partial=Partial(False, True),
                    ),
                    Erasure(Side.LEFT),
                    Erasure(Side.CENTER),
                    Erasure(Side.RIGHT),
                    LineContinuation("→"),
                ],
            )
        ],
    ],
)
def test_load_line(lines):
    parser_version = "2.3.1"
    assert TextSchema().load(
        {"lines": dump_lines(lines), "parser_version": "2.3.1",}
    ) == Text.of_iterable(lines).set_parser_version(parser_version)