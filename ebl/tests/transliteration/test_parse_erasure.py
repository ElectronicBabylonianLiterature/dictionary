import pytest

from ebl.transliteration.domain.enclosure_tokens import Erasure
from ebl.transliteration.domain.lark_parser import parse_erasure
from ebl.transliteration.domain.side import Side
from ebl.transliteration.domain.sign_tokens import (
    Divider,
    Reading,
    UnclearSign,
    UnidentifiedSign,
)
from ebl.transliteration.domain.word_tokens import ErasureState, Word

ERASURE_LEFT = Erasure(Side.LEFT)
ERASURE_CENTER = Erasure(Side.CENTER)
ERASURE_RIGHT = Erasure(Side.RIGHT)


@pytest.mark.parametrize("parser", [parse_erasure])
@pytest.mark.parametrize(
    "atf,erased,over_erased",
    [
        (
            "°ku\\ku°",
            (Word(erasure=ErasureState.ERASED, parts=[Reading.of_name("ku")]),),
            (Word(erasure=ErasureState.OVER_ERASED, parts=[Reading.of_name("ku")],),),
        ),
        ("°::\\:.°", (Divider.of("::"),), (Divider.of(":."),),),
        (
            "°\\ku°",
            tuple(),
            (Word(erasure=ErasureState.OVER_ERASED, parts=[Reading.of_name("ku")],),),
        ),
        (
            "°ku\\°",
            (Word(erasure=ErasureState.ERASED, parts=[Reading.of_name("ku")]),),
            tuple(),
        ),
        ("°\\°", tuple(), tuple()),
        (
            "°x X\\X x°",
            (
                Word(erasure=ErasureState.ERASED, parts=[UnclearSign()]),
                Word(erasure=ErasureState.ERASED, parts=[UnidentifiedSign()],),
            ),
            (
                Word(erasure=ErasureState.OVER_ERASED, parts=[UnidentifiedSign()],),
                Word(erasure=ErasureState.OVER_ERASED, parts=[UnclearSign()],),
            ),
        ),
    ],
)
def test_erasure(parser, atf, erased, over_erased):
    assert parser(atf) == [
        ERASURE_LEFT,
        erased,
        ERASURE_CENTER,
        over_erased,
        ERASURE_RIGHT,
    ]
