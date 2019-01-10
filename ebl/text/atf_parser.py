import re
import pydash
from parsy import (
    string, regex, seq, ParseError, char_from, string_from, decimal_digit
)
from ebl.text.atf import AtfSyntaxError
from ebl.text.line import EmptyLine, TextLine, ControlLine
from ebl.text.text import Text
from ebl.text.token import (
    Token, Word, LanguageShift, LoneDeterminative, Partial
)


def variant(parser):
    variant_separator = string('/').desc('variant separator')
    return parser + (variant_separator + parser).many().concat()


def determinative(parser):
    return (
        OMISSION.at_most(1).concat() +
        string_from('{+', '{') +
        parser +
        string('}') +
        MODIFIER +
        FLAG +
        OMISSION.at_most(1).concat()
    )


def sequence(prefix, part, min_=None):
    joiner_and_part = JOINER.many().concat() + part
    tail = (
        joiner_and_part.many().concat()
        if min_ is None
        else joiner_and_part.at_least(min_).concat()
    )
    return prefix + tail


OMISSION = string_from(
    '<<', '<(', '<', '>>', ')>', '>'
).desc('omission or removal')
LINQUISTIC_GLOSS = string_from('{{', '}}')
DOCUMENT_ORIENTED_GLOSS = string_from('{(', ')}')
SINGLE_DOT = regex(r'(?<!\.)\.(?!\.)')
JOINER = (
    OMISSION |
    LINQUISTIC_GLOSS |
    string_from('-', '+') |
    SINGLE_DOT
).desc('joiner')
FLAG = char_from('!?*#').many().concat().desc('flag')
MODIFIER = (
    string('@') +
    (char_from('cfgstnzkrhv') | decimal_digit.at_least(1).concat())
).many().concat()
WORD_SEPARATOR = string(' ').desc('word separtor')
LINE_SEPARATOR = regex(r'\n').desc('line separator')
WORD_SEPARATOR_OR_EOL = WORD_SEPARATOR | regex(r'(?=\n|$)')
LINE_NUMBER = regex(r'[^.\s]+\.').at_least(1).concat().desc('line number')
TABULATION = string('($___$)').desc('tabulation')
COLUMN = regex(r'&\d*').desc('column') << WORD_SEPARATOR_OR_EOL
DIVIDER = (
    string_from('|', ':\'', ':"', ':.', '::', ':?', ':', ';', '/') +
    MODIFIER +
    FLAG
).desc('divider') << WORD_SEPARATOR_OR_EOL
COMMENTARY_PROTOCOL = regex(r'!(qt|bs|cm|zz)').desc('commentary protocol')
LACUNA = regex(r'\[?\(?\.\.\.\)?]?').desc('lacuna')
SHIFT = regex(r'%\w+').desc('language or register/writing system shift')
UNKNOWN = (
    char_from('Xx') +
    FLAG
).desc('unclear or unindentified')
SUB_INDEX = regex(r'[₀-₉ₓ]+').desc('subindex')
INLINE_BROKEN = (
    regex(r'(\[\(|\[|(?!>{)\()(?!\.)') |
    regex(r'(?<!\.)(\)\]|\)(?!})|\])')
)
VALUE = seq(
    (
        char_from('aāâbdeēêghiīîyklmnpqrsṣštṭuūûwzḫʾ') |
        decimal_digit |
        INLINE_BROKEN
    ).at_least(1).concat(),
    SUB_INDEX.optional(),
    MODIFIER,
    FLAG
).map(pydash.compact).concat().desc('reading')
GRAPHEME = (
    string('$').at_most(1).concat() +
    (
        regex(r'[A-ZṢŠṬa-zṣšṭ0-9₀-₉]') |
        INLINE_BROKEN
    ).at_least(1).concat() +
    MODIFIER +
    FLAG
).desc('grapheme')
COMPOUND_GRAPHEME_OPERATOR = (SINGLE_DOT | char_from('×%&+()')).desc(
    'compound grapheme operator'
)
COMPOUND_DELIMITER = string('|').at_most(1).concat()
COMPUND_PART = variant(GRAPHEME)
COMPOUND_GRAPHEME = (
    seq(
        COMPOUND_DELIMITER,
        COMPUND_PART,
        (
            COMPOUND_GRAPHEME_OPERATOR.many().concat() +
            COMPUND_PART
        ).many().concat(),
        COMPOUND_DELIMITER
    )
    .map(pydash.flatten_deep)
    .concat()
    .desc('compound grapheme')
)
VALUE_WITH_SIGN = (
    VALUE +
    string('!').at_most(1).concat() +
    string('(') +
    COMPOUND_GRAPHEME +
    string(')')
)
VARIANT = variant(
    UNKNOWN |
    VALUE_WITH_SIGN |
    VALUE |
    COMPOUND_GRAPHEME |
    GRAPHEME |
    DIVIDER
)
DETERMINATIVE_SEQUENCE = determinative(sequence(VARIANT, VARIANT))
WORD = seq(
    JOINER.many().concat(),
    (
        sequence(VARIANT, DETERMINATIVE_SEQUENCE | VARIANT) |
        sequence(DETERMINATIVE_SEQUENCE, DETERMINATIVE_SEQUENCE | VARIANT, 1)
    ),
    JOINER.many().concat(),
    FLAG
).map(pydash.flatten_deep).concat().desc('word')
LONE_DETERMINATIVE = determinative(
    VARIANT + (JOINER.many().concat() + VARIANT).many().concat()
).desc('lone determinative')


CONTROL_LINE = seq(
    string_from('=:', '$', '@', '&', '#'),
    regex(r'.*').map(Token)
).combine(ControlLine.of_single)
EMPTY_LINE = regex(
    r'^$', re.RegexFlag.MULTILINE
).map(lambda _: EmptyLine()) << LINE_SEPARATOR
TEXT_LINE = seq(
    LINE_NUMBER << WORD_SEPARATOR,
    (
        TABULATION.map(Token) |
        COLUMN.map(Token) |
        DIVIDER.map(Token) |
        COMMENTARY_PROTOCOL.map(Token) |
        DOCUMENT_ORIENTED_GLOSS.map(Token) |
        SHIFT.map(LanguageShift) |
        WORD.map(Word) |
        seq(LACUNA, LONE_DETERMINATIVE, LACUNA).map(
            lambda values: [
                Token(values[0]),
                LoneDeterminative.of_value(
                    values[1], Partial(True, True)
                ),
                Token(values[2])
            ]
        ) |
        seq(LACUNA, LONE_DETERMINATIVE).map(
            lambda values: [
                Token(values[0]),
                LoneDeterminative.of_value(
                    values[1], Partial(True, False)
                )
            ]
        ) |
        seq(LONE_DETERMINATIVE, LACUNA).map(
            lambda values: [
                LoneDeterminative.of_value(
                    values[0], Partial(False, True)
                ),
                Token(values[1])
            ]
        ) |
        LONE_DETERMINATIVE.map(
            lambda value: LoneDeterminative.of_value(
                value, Partial(False, False)
            )
        ) |
        LACUNA.map(Token) |
        OMISSION.map(Token)
    ).many().sep_by(WORD_SEPARATOR).map(pydash.flatten_deep)
).combine(TextLine.of_iterable)


ATF = (
    (CONTROL_LINE | TEXT_LINE | EMPTY_LINE)
    .many()
    .sep_by(LINE_SEPARATOR)
    .map(pydash.flatten)
    .map(tuple)
    .map(Text)
)


def parse_atf(atf: str):
    try:
        return ATF.parse(atf)
    except ParseError as error:
        line_number = int(error.line_info().split(':')[0]) + 1
        raise AtfSyntaxError(line_number)
