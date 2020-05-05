from abc import ABC, abstractmethod
from typing import Iterable, Sequence, Tuple

import attr

from ebl.transliteration.domain.atf import Atf
from ebl.transliteration.domain.atf_visitor import AtfVisitor
from ebl.transliteration.domain.enclosure_visitor import EnclosureUpdater
from ebl.transliteration.domain.language import Language
from ebl.transliteration.domain.language_visitor import LanguageVisitor
from ebl.transliteration.domain.line import Line
from ebl.transliteration.domain.tokens import Token, ValueToken


@attr.s(frozen=True, auto_attribs=True)
class NotePart(ABC):
    @property
    @abstractmethod
    def value(self) -> str:
        ...


@attr.s(frozen=True, auto_attribs=True)
class StringPart(NotePart):
    text: str

    @property
    def value(self) -> str:
        return self.text


@attr.s(frozen=True, auto_attribs=True)
class EmphasisPart(NotePart):
    text: str

    @property
    def value(self) -> str:
        return f"@i{{{self.text}}}"


@attr.s(frozen=True, auto_attribs=True)
class LanguagePart(NotePart):
    language: Language = attr.ib()
    tokens: Sequence[Token] = attr.ib(converter=tuple)

    @language.validator
    def _check_language(self, attribute, value):
        if value not in [Language.AKKADIAN, Language.SUMERIAN]:
            raise ValueError("language must be AKKADIAN or SUMERIAN")

    @property
    def value(self) -> str:
        code = {Language.AKKADIAN: "akk", Language.SUMERIAN: "sux"}[self.language]
        transliteration = AtfVisitor.to_atf(None, self.tokens)
        return f"@{code}{{{transliteration}}}"

    @staticmethod
    def of_transliteration(
        language: Language,
        tokens: Sequence[Token]
    ) -> "LanguagePart":
        tokens_with_enclosures = EnclosureUpdater.set_enclosure_types(tokens)
        tokens_with_language = LanguageVisitor.set_language(
            tokens_with_enclosures,
            language
        )

        return LanguagePart(language, tokens_with_language)


def convert_part_sequence(flags: Iterable[NotePart]) -> Tuple[NotePart, ...]:
    return tuple(flags)


@attr.s(frozen=True, auto_attribs=True)
class NoteLine(Line):
    parts: Sequence[NotePart] = attr.ib(converter=convert_part_sequence)

    @property
    def prefix(self) -> str:
        return "#note: "

    @property
    def content(self) -> Sequence[ValueToken]:
        return [ValueToken.of(part.value) for part in self.parts]

    @property
    def atf(self) -> Atf:
        note = "".join(part.value for part in self.parts)
        return Atf(f"{self.prefix}{note}")
