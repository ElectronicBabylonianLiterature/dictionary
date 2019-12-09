import pytest

import ebl.transliteration.domain.atf as atf
from ebl.tests.asserts import assert_token_serialization
from ebl.transliteration.application.token_schemas import dump_tokens
from ebl.transliteration.domain.alignment import AlignmentError, AlignmentToken
from ebl.transliteration.domain.enclosure_tokens import DocumentOrientedGloss
from ebl.transliteration.domain.language import Language
from ebl.transliteration.domain.lemmatization import (
    LemmatizationError,
    LemmatizationToken,
)
from ebl.transliteration.domain.sign_tokens import Divider, Reading
from ebl.transliteration.domain.tokens import (
    Column,
    CommentaryProtocol,
    Joiner,
    LanguageShift,
    LineContinuation,
    Tabulation,
    UnknownNumberOfSigns,
    ValueToken,
    Variant,
)
from ebl.transliteration.domain.word_tokens import (
    DEFAULT_NORMALIZED,
    InWordNewline,
)

TOKENS = [
    UnknownNumberOfSigns(),
    LanguageShift("%sux"),
    DocumentOrientedGloss("{("),
]


def test_value_token():
    value = "value"
    token = ValueToken(value)
    equal = ValueToken(value)
    other = ValueToken("anothervalue")

    assert token.value == value
    assert token.get_key() == f"ValueToken⁝{value}"
    assert token.lemmatizable is False

    serialized = {"type": "Token", "value": token.value}
    assert_token_serialization(token, serialized)

    assert token == equal
    assert hash(token) == hash(equal)

    assert token != other
    assert hash(token) != hash(other)


@pytest.mark.parametrize(
    "value,expected_language,normalized",
    [
        (r"%sux", Language.SUMERIAN, DEFAULT_NORMALIZED),
        (r"%es", Language.EMESAL, DEFAULT_NORMALIZED),
        (r"%sb", Language.AKKADIAN, DEFAULT_NORMALIZED),
        (r"%n", Language.AKKADIAN, True),
        (r"%foo", Language.UNKNOWN, DEFAULT_NORMALIZED),
    ],
)
def test_language_shift(value, expected_language, normalized):
    shift = LanguageShift(value)
    equal = LanguageShift(value)
    other = ValueToken(r"%bar")

    assert shift.value == value
    assert shift.get_key() == f"LanguageShift⁝{value}"
    assert shift.lemmatizable is False
    assert shift.normalized == normalized
    assert shift.language == expected_language

    serialized = {
        "type": "LanguageShift",
        "value": shift.value,
        "normalized": normalized,
        "language": shift.language.name,
    }
    assert_token_serialization(shift, serialized)

    assert shift == equal
    assert hash(shift) == hash(equal)

    assert shift != other
    assert hash(shift) != hash(other)

    assert shift != ValueToken(value)


@pytest.mark.parametrize("token", TOKENS)
def test_set_unique_lemma_incompatible(token):
    lemma = LemmatizationToken("other-value")
    with pytest.raises(LemmatizationError):
        token.set_unique_lemma(lemma)


@pytest.mark.parametrize("token", TOKENS)
def test_set_unique_lemma_with_lemma(token):
    lemma = LemmatizationToken(token.value, tuple())
    with pytest.raises(LemmatizationError):
        token.set_unique_lemma(lemma)


@pytest.mark.parametrize("token", TOKENS)
def test_set_unique_lemma_no_lemma(token):
    lemma = LemmatizationToken(token.value)
    assert token.set_unique_lemma(lemma) == token


@pytest.mark.parametrize("token", TOKENS)
def test_set_alignment_incompatible(token):
    alignment = AlignmentToken("other-value", None)
    with pytest.raises(AlignmentError):
        token.set_alignment(alignment)


@pytest.mark.parametrize("token", TOKENS)
def test_set_non_empty_alignment(token):
    alignment = AlignmentToken(token.value, 0)
    with pytest.raises(AlignmentError):
        token.set_alignment(alignment)


@pytest.mark.parametrize("token", TOKENS)
def test_set_alignment_no_alignment(token):
    alignment = AlignmentToken(token.value, None)
    assert token.set_alignment(alignment) == token


@pytest.mark.parametrize("old", TOKENS)
@pytest.mark.parametrize("new", TOKENS)
def test_merge(old, new):
    merged = old.merge(new)
    assert merged == new


def test_unknown_number_of_signs():
    unknown_number_of_signs = UnknownNumberOfSigns()

    expected_value = "..."
    assert unknown_number_of_signs.value == expected_value
    assert unknown_number_of_signs.get_key() == f"UnknownNumberOfSigns⁝{expected_value}"
    assert unknown_number_of_signs.lemmatizable is False

    serialized = {
        "type": "UnknownNumberOfSigns",
        "value": expected_value,
    }
    assert_token_serialization(unknown_number_of_signs, serialized)


def test_tabulation():
    value = "($___$)"
    tabulation = Tabulation(value)

    assert tabulation.value == value
    assert tabulation.get_key() == f"Tabulation⁝{value}"
    assert tabulation.lemmatizable is False

    serialized = {"type": "Tabulation", "value": value}
    assert_token_serialization(tabulation, serialized)


@pytest.mark.parametrize("protocol_enum", atf.CommentaryProtocol)
def test_commentary_protocol(protocol_enum):
    value = protocol_enum.value
    protocol = CommentaryProtocol(value)

    assert protocol.value == value
    assert protocol.get_key() == f"CommentaryProtocol⁝{value}"
    assert protocol.lemmatizable is False
    assert protocol.protocol == protocol_enum

    serialized = {"type": "CommentaryProtocol", "value": value}
    assert_token_serialization(protocol, serialized)


def test_column():
    column = Column()

    expected_value = "&"
    assert column.value == expected_value
    assert column.get_key() == f"Column⁝{expected_value}"
    assert column.lemmatizable is False

    serialized = {
        "type": "Column",
        "value": expected_value,
        "number": None,
    }
    assert_token_serialization(column, serialized)


def test_column_with_number():
    column = Column(1)

    expected_value = "&1"
    assert column.value == expected_value
    assert column.get_key() == f"Column⁝{expected_value}"
    assert column.lemmatizable is False

    serialized = {
        "type": "Column",
        "value": expected_value,
        "number": 1,
    }
    assert_token_serialization(column, serialized)


def test_invalid_column():
    with pytest.raises(ValueError):
        Column(-1)


def test_variant():
    reading = Reading.of("sal")
    divider = Divider.of(":")
    variant = Variant.of(reading, divider)

    expected_value = "sal/:"
    assert variant.value == expected_value
    assert variant.get_key() == f"Variant⁝{expected_value}"
    assert variant.lemmatizable is False

    serialized = {
        "type": "Variant",
        "value": expected_value,
        "tokens": dump_tokens([reading, divider]),
    }
    assert_token_serialization(variant, serialized)


@pytest.mark.parametrize(
    "joiner,expected_value",
    [
        (Joiner.dot(), "."),
        (Joiner.hyphen(), "-"),
        (Joiner.colon(), ":"),
        (Joiner.plus(), "+"),
    ],
)
def test_joiner(joiner, expected_value):
    assert joiner.value == expected_value
    assert joiner.get_key() == f"Joiner⁝{expected_value}"
    assert joiner.lemmatizable is False

    serialized = {
        "type": "Joiner",
        "value": expected_value,
    }
    assert_token_serialization(joiner, serialized)


def test_in_word_new_line():
    newline = InWordNewline()

    expected_value = ";"
    assert newline.value == expected_value
    assert newline.get_key() == f"InWordNewline⁝{expected_value}"
    assert newline.lemmatizable is False

    serialized = {
        "type": "InWordNewline",
        "value": expected_value,
    }
    assert_token_serialization(newline, serialized)


def test_line_continuation():
    value = "→"
    continuation = LineContinuation(value)

    assert continuation.value == value
    assert continuation.get_key() == f"LineContinuation⁝{value}"
    assert continuation.lemmatizable is False

    serialized = {
        "type": "LineContinuation",
        "value": continuation.value,
    }
    assert_token_serialization(continuation, serialized)