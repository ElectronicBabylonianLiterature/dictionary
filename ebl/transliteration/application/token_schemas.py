from abc import abstractmethod
from typing import List, Mapping, Optional, Sequence, Tuple, Type, Union

import pydash
from marshmallow import EXCLUDE, Schema, fields, post_dump, post_load

from ebl.schemas import NameEnum, ValueEnum
from ebl.transliteration.domain import atf
from ebl.transliteration.domain.atf import Flag
from ebl.transliteration.domain.enclosure_tokens import (
    IntentionalOmission,
    BrokenAway,
    Determinative,
    DocumentOrientedGloss,
    Erasure,
    Gloss,
    LinguisticGloss,
    AccidentalOmission,
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
        return ValueToken(data["value"])


class LanguageShiftSchema(Schema):
    type = fields.Constant("LanguageShift", required=True)
    value = fields.String(required=True)
    language = NameEnum(Language, required=True)
    normalized = fields.Boolean(required=True)

    @post_load
    def make_token(self, data, **kwargs):
        return LanguageShift(data["value"])


class DocumentOrientedGlossSchema(Schema):
    type = fields.Constant("DocumentOrientedGloss", required=True)
    value = fields.String(required=True)

    @post_load
    def make_token(self, data, **kwargs):
        return DocumentOrientedGloss(data["value"])


class BrokenAwaySchema(Schema):
    type = fields.Constant("BrokenAway", required=True)
    value = fields.String(required=True)

    @post_load
    def make_token(self, data, **kwargs):
        return BrokenAway(data["value"])


class PerhapsBrokenAwaySchema(Schema):
    type = fields.Constant("PerhapsBrokenAway", required=True)
    value = fields.String(required=True)

    @post_load
    def make_token(self, data, **kwargs):
        return PerhapsBrokenAway(data["value"])


class OmissionOrRemovalSchema(Schema):
    """This class is deprecated and kept only for backwards compatibility.
    Omission, AccidentalOmission, or Removal should be used instead."""

    type = fields.Constant("OmissionOrRemoval", required=True)
    value = fields.String(required=True)

    @post_load
    def make_token(self, data, **kwargs):
        return OmissionOrRemoval(data["value"])


class EnclosureSchema(Schema):
    value = fields.String(required=True)
    side = NameEnum(Side, required=True)

    @abstractmethod
    @post_load
    def make_token(self, data, **kwargs) -> Gloss:
        ...


class AccidentlOmissionSchema(EnclosureSchema):
    type = fields.Constant("AccidentalOmission", required=True)

    @post_load
    def make_token(self, data, **kwargs):
        return AccidentalOmission(data["side"])


class IntentionalOmissionSchema(EnclosureSchema):
    type = fields.Constant("IntentionalOmission", required=True)

    @post_load
    def make_token(self, data, **kwargs):
        return IntentionalOmission(data["side"])


class RemovalSchema(EnclosureSchema):
    type = fields.Constant("Removal", required=True)

    @post_load
    def make_token(self, data, **kwargs):
        return Removal(data["side"])


class ErasureSchema(EnclosureSchema):
    type = fields.Constant("Erasure", required=True)

    @post_load
    def make_token(self, data, **kwargs):
        return Erasure(data["side"])


class LineContinuationSchema(Schema):
    type = fields.Constant("LineContinuation", required=True)
    value = fields.String(required=True)

    @post_load
    def make_token(self, data, **kwargs):
        return LineContinuation(data["value"])


class UnknownNumberOfSignsSchema(Schema):
    type = fields.Constant("UnknownNumberOfSigns", required=True)
    value = fields.String(required=True)

    @post_load
    def make_token(self, data, **kwargs):
        return UnknownNumberOfSigns()


class TabulationSchema(Schema):
    type = fields.Constant("Tabulation", required=True)
    value = fields.String(required=True)

    @post_load
    def make_token(self, data, **kwargs):
        return Tabulation(data["value"])


class CommentaryProtocolSchema(Schema):
    type = fields.Constant("CommentaryProtocol", required=True)
    value = fields.String(required=True)

    @post_load
    def make_token(self, data, **kwargs):
        return CommentaryProtocol(data["value"])


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
        return Column(data["number"])


class UnidentifiedSignSchema(Schema):
    type = fields.Constant("UnidentifiedSign", required=True)
    value = fields.String(required=True)
    flags = fields.List(ValueEnum(Flag), required=True)

    @post_load
    def make_token(self, data, **kwargs):
        return UnidentifiedSign(tuple(data["flags"]))


class UnclearSignSchema(Schema):
    type = fields.Constant("UnclearSign", required=True)
    value = fields.String(required=True)
    flags = fields.List(ValueEnum(Flag), required=True)

    @post_load
    def make_token(self, data, **kwargs):
        return UnclearSign(tuple(data["flags"]))


class JoinerSchema(Schema):
    type = fields.Constant("Joiner", required=True)
    value = fields.String()
    enum_value = ValueEnum(atf.Joiner, required=True, data_key="value", load_only=True)

    @post_load
    def make_token(self, data, **kwargs):
        return Joiner(data["enum_value"])


class InWordNewlineSchema(Schema):
    type = fields.Constant("InWordNewline", required=True)
    value = fields.String(required=True)

    @post_load
    def make_token(self, data, **kwargs):
        return InWordNewline()


def _load_sign(sign: Optional[Union[str, dict]]) -> Optional[Token]:
    if sign is None:
        return sign
    elif isinstance(sign, str):
        return ValueToken(sign)
    else:
        return load_token(sign)


class ReadingSchema(Schema):
    type = fields.Constant("Reading", required=True)
    value = fields.String(required=True)
    name = fields.String(required=True)
    sub_index = fields.Integer(data_key="subIndex", allow_none=True)
    modifiers = fields.List(fields.String(), required=True)
    flags = fields.List(ValueEnum(Flag), required=True)
    sign = fields.Raw(missing=None)

    @post_load
    def make_token(self, data, **kwargs):
        return Reading.of(
            data["name"],
            data["sub_index"],
            data["modifiers"],
            data["flags"],
            _load_sign(data["sign"]),
        )

    @post_dump
    def dump_token(self, data, **kwargs):
        return {
            **data,
            "sign": data["sign"] and dump_token(data["sign"]),
        }


class LogogramSchema(Schema):
    type = fields.Constant("Logogram", required=True)
    value = fields.String(required=True)
    name = fields.String(required=True)
    sub_index = fields.Integer(data_key="subIndex", allow_none=True)
    modifiers = fields.List(fields.String(), required=True)
    flags = fields.List(ValueEnum(Flag), required=True)
    sign = fields.Raw(missing=None)
    surrogate = fields.List(fields.Dict(), missing=[])

    @post_load
    def make_token(self, data, **kwargs):
        return Logogram.of(
            data["name"],
            data["sub_index"],
            data["modifiers"],
            data["flags"],
            _load_sign(data["sign"]),
            load_tokens(data["surrogate"]),
        )

    @post_dump
    def dump_token(self, data, **kwargs):
        return {
            **data,
            "surrogate": dump_tokens(data["surrogate"]),
            "sign": data["sign"] and dump_token(data["sign"]),
        }


class NumberSchema(Schema):
    type = fields.Constant("Number", required=True)
    value = fields.String(required=True)
    numeral = fields.Integer(load_only=True)
    name = fields.String(missing=None)
    sub_index = fields.Integer(data_key="subIndex", missing=1)
    modifiers = fields.List(fields.String(), required=True)
    flags = fields.List(ValueEnum(Flag), required=True)
    sign = fields.Raw(missing=None)

    @post_load
    def make_token(self, data, **kwargs):
        return Number.of(
            data["name"] or str(data["numeral"]),
            data["modifiers"],
            data["flags"],
            _load_sign(data["sign"]),
            data["sub_index"],
        )

    @post_dump
    def dump_token(self, data, **kwargs):
        return {
            **data,
            "sign": data["sign"] and dump_token(data["sign"]),
        }


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
        return Word(
            data["value"],
            data["language"],
            data["normalized"],
            tuple(data["unique_lemma"]),
            data.get("erasure"),
            data.get("alignment"),
            parts=load_tokens(data["parts"]),
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
        return LoneDeterminative(
            data["value"],
            data["language"],
            data["normalized"],
            tuple(data["unique_lemma"]),
            data["erasure"],
            data["alignment"],
            parts=load_tokens(data["parts"]),
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
        return Variant(load_tokens(data["tokens"]))

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
        return CompoundGrapheme(data["value"])


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
        return Determinative(load_tokens(data["parts"]))


class PhoneticGlossSchema(GlossSchema):
    type = fields.Constant("PhoneticGloss", required=True)

    @post_load
    def make_token(self, data, **kwargs):
        return PhoneticGloss(load_tokens(data["parts"]))


class LinguisticGlossSchema(GlossSchema):
    type = fields.Constant("LinguisticGloss", required=True)

    @post_load
    def make_token(self, data, **kwargs):
        return LinguisticGloss(load_tokens(data["parts"]))


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
    "AccidentalOmission": AccidentlOmissionSchema,
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


def load_tokens(tokens: Sequence[dict]) -> Tuple[Token, ...]:
    return tuple(map(load_token, tokens))
