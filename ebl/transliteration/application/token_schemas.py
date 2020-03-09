from abc import abstractmethod
from functools import singledispatch
from typing import List, Mapping, Optional, Sequence, Type

import pydash
from marshmallow import EXCLUDE, Schema, fields, post_dump, post_load

from ebl.schemas import NameEnum, ValueEnum
from ebl.transliteration.domain import atf
from ebl.transliteration.domain.atf import Flag
from ebl.transliteration.domain.enclosure_tokens import (
    AccidentalOmission,
    BrokenAway,
    Determinative,
    DocumentOrientedGloss,
    Erasure,
    Gloss,
    IntentionalOmission,
    LinguisticGloss,
    OmissionOrRemoval,
    PerhapsBrokenAway,
    PhoneticGloss,
    Removal,
)
from ebl.transliteration.domain.language import Language
from ebl.transliteration.domain.side import Side
from ebl.transliteration.domain.sign_tokens import (
    CompoundGrapheme,
    Divider,
    Grapheme,
    Logogram,
    NamedSign,
    Number,
    Reading,
    UnclearSign,
    UnidentifiedSign,
)
from ebl.transliteration.domain.tokens import (
    Column,
    CommentaryProtocol,
    Joiner,
    LanguageShift,
    LineContinuation,
    Tabulation,
    Token,
    UnknownNumberOfSigns,
    ValueToken,
    Variant,
)
from ebl.transliteration.domain.word_tokens import (
    ErasureState,
    InWordNewline,
    LoneDeterminative,
    Word,
)


class ValueTokenSchema(Schema):
    type = fields.Constant("Token", required=True)
    value = fields.String(required=True)

    @post_load
    def make_token(self, data, **kwargs):
        return ValueToken.of(data["value"])


class LanguageShiftSchema(Schema):
    type = fields.Constant("LanguageShift", required=True)
    value = fields.String(required=True)
    language = NameEnum(Language, required=True)
    normalized = fields.Boolean(required=True)

    @post_load
    def make_token(self, data, **kwargs):
        return LanguageShift.of(data["value"])


class DocumentOrientedGlossSchema(Schema):
    type = fields.Constant("DocumentOrientedGloss", required=True)
    value = fields.String(required=True)
    side = NameEnum(Side, missing=None)

    @post_load
    def make_token(self, data, **kwargs):
        return (
            DocumentOrientedGloss.of(data["side"])
            if data["side"]
            else DocumentOrientedGloss.of_value(data["value"])
        )


class BrokenAwaySchema(Schema):
    type = fields.Constant("BrokenAway", required=True)
    value = fields.String(required=True)
    side = NameEnum(Side, missing=None)

    @post_load
    def make_token(self, data, **kwargs):
        return (
            BrokenAway.of(data["side"])
            if data["side"]
            else BrokenAway.of_value(data["value"])
        )


class PerhapsBrokenAwaySchema(Schema):
    type = fields.Constant("PerhapsBrokenAway", required=True)
    value = fields.String(required=True)
    side = NameEnum(Side, missing=None)

    @post_load
    def make_token(self, data, **kwargs):
        return (
            PerhapsBrokenAway.of(data["side"])
            if data["side"]
            else PerhapsBrokenAway.of_value(data["value"])
        )


class OmissionOrRemovalSchema(Schema):
    """This class is deprecated and kept only for backwards compatibility.
    Omission, AccidentalOmission, or Removal should be used instead."""

    type = fields.Constant("OmissionOrRemoval", required=True)
    value = fields.String(required=True)

    @post_load
    def make_token(self, data, **kwargs):
        return OmissionOrRemoval(frozenset(), data["value"])


class EnclosureSchema(Schema):
    value = fields.String(required=True)
    side = NameEnum(Side, required=True)

    @abstractmethod
    @post_load
    def make_token(self, data, **kwargs) -> Gloss:
        ...


class AccidentalOmissionSchema(EnclosureSchema):
    type = fields.Constant("AccidentalOmission", required=True)

    @post_load
    def make_token(self, data, **kwargs):
        return AccidentalOmission.of(data["side"])


class IntentionalOmissionSchema(EnclosureSchema):
    type = fields.Constant("IntentionalOmission", required=True)

    @post_load
    def make_token(self, data, **kwargs):
        return IntentionalOmission.of(data["side"])


class RemovalSchema(EnclosureSchema):
    type = fields.Constant("Removal", required=True)

    @post_load
    def make_token(self, data, **kwargs):
        return Removal.of(data["side"])


class ErasureSchema(EnclosureSchema):
    type = fields.Constant("Erasure", required=True)

    @post_load
    def make_token(self, data, **kwargs):
        return Erasure.of(data["side"])


class LineContinuationSchema(Schema):
    type = fields.Constant("LineContinuation", required=True)
    value = fields.String(required=True)

    @post_load
    def make_token(self, data, **kwargs):
        return LineContinuation(frozenset(), data["value"])


class UnknownNumberOfSignsSchema(Schema):
    type = fields.Constant("UnknownNumberOfSigns", required=True)
    value = fields.String(required=True)

    @post_load
    def make_token(self, data, **kwargs):
        return UnknownNumberOfSigns(frozenset())


class TabulationSchema(Schema):
    type = fields.Constant("Tabulation", required=True)
    value = fields.String(required=True)

    @post_load
    def make_token(self, data, **kwargs):
        return Tabulation.of(data["value"])


class CommentaryProtocolSchema(Schema):
    type = fields.Constant("CommentaryProtocol", required=True)
    value = fields.String(required=True)

    @post_load
    def make_token(self, data, **kwargs):
        return CommentaryProtocol.of(data["value"])


class DividerSchema(Schema):
    type = fields.Constant("Divider", required=True)
    value = fields.String(required=True)
    divider = fields.String(required=True)
    modifiers = fields.List(fields.String(), required=True)
    flags = fields.List(ValueEnum(Flag), required=True)

    @post_load
    def make_token(self, data, **kwargs):
        return Divider.of(
            data["divider"], tuple(data["modifiers"]), tuple(data["flags"]),
        )


class ColumnSchema(Schema):
    type = fields.Constant("Column", required=True)
    value = fields.String(required=True)
    number = fields.Integer(missing=None)

    @post_load
    def make_token(self, data, **kwargs):
        return Column.of(data["number"])


class UnidentifiedSignSchema(Schema):
    type = fields.Constant("UnidentifiedSign", required=True)
    value = fields.String(required=True)
    flags = fields.List(ValueEnum(Flag), required=True)

    @post_load
    def make_token(self, data, **kwargs):
        return UnidentifiedSign.of(tuple(data["flags"]))


class UnclearSignSchema(Schema):
    type = fields.Constant("UnclearSign", required=True)
    value = fields.String(required=True)
    flags = fields.List(ValueEnum(Flag), required=True)

    @post_load
    def make_token(self, data, **kwargs):
        return UnclearSign.of(tuple(data["flags"]))


class JoinerSchema(Schema):
    type = fields.Constant("Joiner", required=True)
    value = fields.String()
    enum_value = ValueEnum(atf.Joiner, required=True, data_key="value", load_only=True)

    @post_load
    def make_token(self, data, **kwargs):
        return Joiner(frozenset(), data["enum_value"])


class InWordNewlineSchema(Schema):
    type = fields.Constant("InWordNewline", required=True)
    value = fields.String(required=True)

    @post_load
    def make_token(self, data, **kwargs):
        return InWordNewline(frozenset())


def _dump_sign(named_sign: NamedSign) -> Optional[dict]:
    return None if named_sign.sign is None else dump_token(named_sign.sign)


@singledispatch
def _load_sign(sign) -> Optional[Token]:
    return load_token(sign)


@_load_sign.register
def _load_sign_none(sign: None) -> None:
    return sign


@_load_sign.register
def _load_sign_str(sign: str) -> Token:
    return ValueToken.of(sign)


class NamedSignSchema(Schema):
    value = fields.String(required=True)
    name = fields.String(required=True)
    name_parts = fields.Function(
        lambda reading: dump_tokens(reading.name_parts),
        lambda data: load_tokens(data),
        missing=None,
        data_key="nameParts",
    )
    sub_index = fields.Integer(data_key="subIndex", allow_none=True)
    modifiers = fields.List(fields.String(), required=True)
    flags = fields.List(ValueEnum(Flag), required=True)
    sign = fields.Function(_dump_sign, _load_sign, missing=None)


class ReadingSchema(NamedSignSchema):
    type = fields.Constant("Reading", required=True)

    @post_load
    def make_token(self, data, **kwargs):
        return Reading.of(
            data["name_parts"] or (ValueToken.of(data["name"]),),
            data["sub_index"],
            data["modifiers"],
            data["flags"],
            data["sign"],
        )


class LogogramSchema(NamedSignSchema):
    type = fields.Constant("Logogram", required=True)
    surrogate = fields.Function(
        lambda logogram: dump_tokens(logogram.surrogate),
        lambda value: load_tokens(value),
        missing=tuple(),
    )

    @post_load
    def make_token(self, data, **kwargs):
        return Logogram.of(
            data["name_parts"] or (ValueToken.of(data["name"]),),
            data["sub_index"],
            data["modifiers"],
            data["flags"],
            data["sign"],
            data["surrogate"],
        )


class NumberSchema(NamedSignSchema):
    type = fields.Constant("Number", required=True)
    numeral = fields.Integer(load_only=True)

    @post_load
    def make_token(self, data, **kwargs):
        return Number.of(
            data["name_parts"] or (ValueToken.of(data["name"]),),
            data["modifiers"],
            data["flags"],
            data["sign"],
            data["sub_index"],
        )


class WordSchema(Schema):
    type = fields.Constant("Word", required=True)
    value = fields.String(required=True)
    language = NameEnum(Language, required=True)
    normalized = fields.Boolean(required=True)
    lemmatizable = fields.Boolean(required=True)
    unique_lemma = fields.List(fields.String(), data_key="uniqueLemma", required=True)
    erasure = NameEnum(ErasureState, missing=ErasureState.NONE)
    alignment = fields.Integer(allow_none=True, missing=None)
    parts = fields.List(fields.Dict(), missing=[])

    @post_load
    def make_token(self, data, **kwargs):
        return Word.of(
            load_tokens(data["parts"]),
            data["language"],
            data["normalized"],
            tuple(data["unique_lemma"]),
            data.get("erasure"),
            data.get("alignment"),
        )

    @post_dump
    def dump_token(self, data, **kwargs):
        return pydash.omit_by(
            {**data, "parts": dump_tokens(data["parts"]),}, lambda value: value is None,
        )


class LoneDeterminativeSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    type = fields.Constant("LoneDeterminative", required=True)
    value = fields.String(required=True)
    language = NameEnum(Language, required=True)
    normalized = fields.Boolean(required=True)
    lemmatizable = fields.Boolean(required=True)
    unique_lemma = fields.List(fields.String(), data_key="uniqueLemma", required=True)
    erasure = NameEnum(ErasureState, missing=ErasureState.NONE)
    alignment = fields.Integer(allow_none=True, missing=None)
    parts = fields.List(fields.Dict(), missing=[])

    @post_load
    def make_token(self, data, **kwargs):
        return LoneDeterminative.of(
            load_tokens(data["parts"]),
            data["language"],
            data["normalized"],
            tuple(data["unique_lemma"]),
            data["erasure"],
            data["alignment"],
        )

    @post_dump
    def dump_token(self, data, **kwargs):
        return pydash.omit_by(
            {**data, "parts": dump_tokens(data["parts"]),}, lambda value: value is None,
        )


class VariantSchema(Schema):
    type = fields.Constant("Variant", required=True)
    value = fields.String()
    tokens = fields.List(fields.Dict(), required=True)

    @post_load
    def make_token(self, data, **kwargs):
        return Variant.of(*load_tokens(data["tokens"]))

    @post_dump
    def dump_token(self, data, **kwargs):
        return {
            **data,
            "tokens": dump_tokens(data["tokens"]),
        }


class GraphemeSchema(Schema):
    type = fields.Constant("Grapheme", required=True)
    value = fields.String(required=True)
    name = fields.String(required=True)
    modifiers = fields.List(fields.String(), required=True)
    flags = fields.List(ValueEnum(Flag), required=True)

    @post_load
    def make_token(self, data, **kwargs):
        return Grapheme.of(data["name"], data["modifiers"], data["flags"])


class CompoundGraphemeSchema(Schema):
    type = fields.Constant("CompoundGrapheme", required=True)
    value = fields.String(required=True)

    @post_load
    def make_token(self, data, **kwargs):
        return CompoundGrapheme.of(data["value"])


class GlossSchema(Schema):
    value = fields.String()
    parts = fields.List(fields.Dict(), required=True)

    @abstractmethod
    @post_load
    def make_token(self, data, **kwargs) -> Gloss:
        ...

    @post_dump
    def dump_token(self, data, **kwargs):
        return {
            **data,
            "parts": dump_tokens(data["parts"]),
        }


class DeterminativeSchema(GlossSchema):
    type = fields.Constant("Determinative", required=True)

    @post_load
    def make_token(self, data, **kwargs):
        return Determinative.of(load_tokens(data["parts"]))


class PhoneticGlossSchema(GlossSchema):
    type = fields.Constant("PhoneticGloss", required=True)

    @post_load
    def make_token(self, data, **kwargs):
        return PhoneticGloss.of(load_tokens(data["parts"]))


class LinguisticGlossSchema(GlossSchema):
    type = fields.Constant("LinguisticGloss", required=True)

    @post_load
    def make_token(self, data, **kwargs):
        return LinguisticGloss.of(load_tokens(data["parts"]))


_schemas: Mapping[str, Type[Schema]] = {
    "Token": ValueTokenSchema,
    "ValueToken": ValueTokenSchema,
    "Word": WordSchema,
    "LanguageShift": LanguageShiftSchema,
    "LoneDeterminative": LoneDeterminativeSchema,
    "DocumentOrientedGloss": DocumentOrientedGlossSchema,
    "BrokenAway": BrokenAwaySchema,
    "PerhapsBrokenAway": PerhapsBrokenAwaySchema,
    "OmissionOrRemoval": OmissionOrRemovalSchema,
    "AccidentalOmission": AccidentalOmissionSchema,
    "IntentionalOmission": IntentionalOmissionSchema,
    "Removal": RemovalSchema,
    "LineContinuation": LineContinuationSchema,
    "Erasure": ErasureSchema,
    "UnknownNumberOfSigns": UnknownNumberOfSignsSchema,
    "Tabulation": TabulationSchema,
    "CommentaryProtocol": CommentaryProtocolSchema,
    "Divider": DividerSchema,
    "Column": ColumnSchema,
    "Variant": VariantSchema,
    "UnidentifiedSign": UnidentifiedSignSchema,
    "UnclearSign": UnclearSignSchema,
    "Joiner": JoinerSchema,
    "InWordNewline": InWordNewlineSchema,
    "Reading": ReadingSchema,
    "Logogram": LogogramSchema,
    "Number": NumberSchema,
    "CompoundGrapheme": CompoundGraphemeSchema,
    "Grapheme": GraphemeSchema,
    "Determinative": DeterminativeSchema,
    "PhoneticGloss": PhoneticGlossSchema,
    "LinguisticGloss": LinguisticGlossSchema,
}


def dump_token(token: Token) -> dict:
    return _schemas[type(token).__name__]().dump(token)


def dump_tokens(tokens: Sequence[Token]) -> List[dict]:
    return list(map(dump_token, tokens))


def load_token(data: dict) -> Token:
    return _schemas[data["type"]]().load(data)


def load_tokens(tokens: Sequence[dict]) -> Sequence[Token]:
    return tuple(map(load_token, tokens))
