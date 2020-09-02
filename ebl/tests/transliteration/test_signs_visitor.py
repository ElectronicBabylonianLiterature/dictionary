from typing import cast, Sequence

import pytest  # pyre-ignore[21]

from ebl.transliteration.application.signs_visitor import SignsVisitor
from ebl.transliteration.domain.lark_parser import parse_line
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.tokens import Token, Variant
from ebl.transliteration.domain.word_tokens import Word
from ebl.transliteration.domain.sign_tokens import (
    CompoundGrapheme, Divider, Grapheme, Logogram, Number, Reading
)
from ebl.transliteration.domain.unknown_sign_tokens import UnclearSign, UnidentifiedSign


@pytest.mark.parametrize("tokens,expected",[
    (
        [
            Word.of([Reading.of_name("ku")]),
            Word.of([Reading.of_name("gid", 2)]),
            Word.of([Reading.of_name("nu")]),
            Word.of([Reading.of_name("ši")]),
        ],
        ["KU", "BU", "ABZ075", "ABZ207a\\u002F207b\\u0020X"]
    ),
    (
        [
            Word.of([CompoundGrapheme.of(["(4×ZA)×KUR"])]),
            Word.of([CompoundGrapheme.of(["(AŠ&AŠ@180)×U"])]),
            Word.of([Logogram.of_name("NU")]),
            Word.of([CompoundGrapheme.of(["GA₂#*+BAD!?"])]),
            Word.of([CompoundGrapheme.of(["GA₂#*", "BAD!?"])]),
        ],
        ["ABZ531+588", "|(AŠ&AŠ@180)×U|", "ABZ075", "|GA₂+BAD|", "GA₂", "BAD"]
    ),
    (
        [
            Word.of([Reading.of_name("ummu", 3)]),
            Word.of([CompoundGrapheme.of(["IGI", "KU"])]),
            Word.of([Reading.of_name("mat", 3)]),
            Word.of([Reading.of_name("kunga", 1)]),
        ],
        [
            "A",
            "ABZ168",
            "LAL",
            "ABZ207a\\u002F207b\\u0020X",
            "KU",
            "HU",
            "HI",
            "ŠU₂",
            "3×AN",
        ],
    ),
    (
        [
            Word.of([Reading.of_name("unknown", 1)]),
            Word.of([UnidentifiedSign.of()]),
            Word.of([UnclearSign.of()]),
        ],
        ["?", "X", "X"],
    ),
    (
        [
            Word.of([Number.of_name("1", sign=Grapheme.of("AŠ"))]),
            Word.of([Number.of_name("1")]),
            Word.of([Number.of_name("2")]),
            Word.of([Number.of_name("10")]),
            Word.of([Number.of_name("20")]),
            Word.of([Number.of_name("30")]),
            Word.of([Number.of_name("256")]),
        ],
        ["ABZ001", "DIŠ", "2", "ABZ411", "ABZ411", "ABZ411", "30", "256"],
    ),
    (
        [
            Divider.of(":"),
            Divider.of("|"),
        ],
        ["ABZ377n1"],
    ),
    (
        [
            Variant.of(
                Divider.of(":"), Reading.of_name("ku"),
            ),
            Word.of(
                [
                    Variant.of(
                        Reading.of_name("šu"), CompoundGrapheme.of(["BI×IS"])
                    ),
                    Variant.of(
                        Reading.of_name("ummu", 3),
                        CompoundGrapheme.of(["IGI", "KU"]),
                        Reading.of_name("mat", 3),
                    ),
                ],
            ),
        ],
        ["ABZ377n1/KU", "ŠU/|BI×IS|", "|A.EDIN.LAL|/|IGI.KU|/ABZ081"],
    ),
    (
        cast(TextLine, parse_line("1. ku-[nu ši]")).content,
        ["KU", "ABZ075", "ABZ207a\\u002F207b\\u0020X"],
    ),
    (
        cast(TextLine, parse_line("1. < : ši>-ku")).content,
        ["KU"],
    ),
    (
        cast(TextLine, parse_line(
            "1. ku-<<nu ši 1 |KU+KU| nu/ši nu(KU) x X ... : >>"
        )).content,
        ["KU"],
    ),
    (
        cast(TextLine, parse_line(
            "1. ku-<nu ši 1 |KU+KU| nu/ši nu(KU) x X ... : >"
        )).content,
        ["KU"],
    ),
    (
        cast(TextLine, parse_line(
            "1. ku-<(nu ši 1 |KU+KU| nu/ši nu(KU) x X ... : )>"
        )).content,
        ["KU"],
    ),
])
def test_signs_visitor(
    tokens: Sequence[Token],
    expected: Sequence[str],
    sign_repository, signs
):
    for sign in signs:
        sign_repository.create(sign)

    visitor = SignsVisitor(sign_repository)
    for token in tokens:
        token.accept(visitor)

    assert visitor.result == expected