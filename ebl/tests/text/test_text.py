from typing import Tuple

import pytest

from ebl.text.atf import Atf
from ebl.text.language import Language
from ebl.text.lemmatization import (Lemmatization, LemmatizationError,
                                    LemmatizationToken)
from ebl.text.line import (ControlLine, EmptyLine, Line, TextLine)
from ebl.text.text import LanguageShift, LoneDeterminative, Partial, Text
from ebl.text.token import Token, Word, LineContinuation, Erasure, Side
from ebl.dictionary.word import WordId
from ebl.text.labels import LineNumberLabel

LINES: Tuple[Line, ...] = (
    TextLine.of_iterable(LineNumberLabel.from_atf('1.'), [Word('ha-am')]),
    ControlLine.of_single('$', Token(' single ruling'))
)
TEXT: Text = Text(LINES)


def test_of_iterable():
    assert Text.of_iterable(LINES) == TEXT


def test_lines():
    assert TEXT.lines == LINES


def test_to_dict():
    assert TEXT.to_dict() == {
        'lines': [line.to_dict() for line in LINES]
    }


def test_lemmatization():
    assert TEXT.lemmatization == Lemmatization((
        (LemmatizationToken('ha-am', tuple()), ),
        (LemmatizationToken(' single ruling'), ),
    ))


def test_atf():
    assert TEXT.atf == Atf(
        '1. ha-am\n'
        '$ single ruling'
    )


def test_update_lemmatization():
    tokens = TEXT.lemmatization.to_list()
    tokens[0][0]['uniqueLemma'] = ['nu I']
    lemmatization = Lemmatization.from_list(tokens)

    expected = Text((
        TextLine('1.', (
            Word('ha-am', unique_lemma=(WordId('nu I'),)),
        )),
        ControlLine('$', (Token(' single ruling'), )),
    ))

    assert TEXT.update_lemmatization(lemmatization) == expected


def test_update_lemmatization_incompatible():
    lemmatization = Lemmatization(
        ((LemmatizationToken('mu', tuple()), ), )
    )
    with pytest.raises(LemmatizationError):
        TEXT.update_lemmatization(lemmatization)


def test_update_lemmatization_wrong_lines():
    tokens = [
        *TEXT.lemmatization.to_list(),
        []
    ]
    lemmatization = Lemmatization.from_list(tokens)

    with pytest.raises(LemmatizationError):
        TEXT.update_lemmatization(lemmatization)


@pytest.mark.parametrize('old,new,expected', [
    (
        Text.of_iterable(LINES),
        Text.of_iterable(LINES),
        Text.of_iterable(LINES)
    ), (
        Text.of_iterable([EmptyLine()]),
        Text.of_iterable([
            ControlLine.of_single('$', Token(' single ruling'))
        ]),
        Text.of_iterable([
            ControlLine.of_single('$', Token(' single ruling'))
        ])
    ), (
        Text.of_iterable([
            ControlLine.of_single('$', Token(' double ruling')),
            ControlLine.of_single('$', Token(' single ruling')),
            EmptyLine()
        ]),
        Text.of_iterable([
            ControlLine.of_single('$', Token(' double ruling')),
            EmptyLine()
        ]),
        Text.of_iterable([
            ControlLine.of_single('$', Token(' double ruling')),
            EmptyLine()
        ]),
    ), (
        Text.of_iterable([
            EmptyLine(),
            ControlLine.of_single('$', Token(' double ruling')),
        ]),
        Text.of_iterable([
            EmptyLine(),
            ControlLine.of_single('$', Token(' single ruling')),
            ControlLine.of_single('$', Token(' double ruling')),
        ]),
        Text.of_iterable([
            EmptyLine(),
            ControlLine.of_single('$', Token(' single ruling')),
            ControlLine.of_single('$', Token(' double ruling')),
        ]),
    ), (
        Text.of_iterable([
            TextLine.of_iterable(LineNumberLabel.from_atf('1.'), [
                Word('nu', unique_lemma=(WordId('nu I'),)),
                Word('nu', unique_lemma=(WordId('nu I'),))
            ])
        ]),
        Text.of_iterable([
            TextLine.of_iterable(LineNumberLabel.from_atf('1.'), [
                Word('mu'), Word('nu')
            ])
        ]),
        Text.of_iterable([
            TextLine.of_iterable(LineNumberLabel.from_atf('1.'), [
                Word('mu'),
                Word('nu', unique_lemma=(WordId('nu I'),))
            ])
        ])
    )
])
def test_merge(old, new, expected):
    assert old.merge(new).to_dict() == expected.to_dict()


@pytest.mark.parametrize('lines', [
    [EmptyLine()],
    [ControlLine.of_single('$', Token(' single ruling'))],
    [
        TextLine.of_iterable(LineNumberLabel.from_atf('1.'), [
            Word('nu', unique_lemma=(WordId('nu I'),)),
            LanguageShift('%sux'),
            LoneDeterminative(
                '{nu}',
                language=Language.SUMERIAN,
                partial=Partial(False, True)
            ),
            Erasure('°', Side.LEFT),
            Erasure('~', Side.CENTER),
            Erasure('°', Side.RIGHT),
            LineContinuation('→')
        ])
    ]
])
def test_from_dict(lines):
    assert Text.from_dict({
        'lines': [line.to_dict() for line in lines]
    }) == Text.of_iterable(lines)
