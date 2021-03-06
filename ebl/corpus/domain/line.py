from typing import Optional, Sequence, Tuple, Union, cast

import attr
import pydash

from ebl.corpus.domain.create_alignment_map import create_alignment_map
from ebl.corpus.domain.enclosure_validator import validate
from ebl.merger import Merger
from ebl.transliteration.domain.dollar_line import DollarLine
from ebl.transliteration.domain.enclosure_visitor import set_enclosure_type
from ebl.transliteration.domain.label_validator import validate_labels
from ebl.transliteration.domain.labels import Label
from ebl.transliteration.domain.language_visitor import set_language
from ebl.transliteration.domain.line import EmptyLine
from ebl.transliteration.domain.line_number import AbstractLineNumber
from ebl.transliteration.domain.note_line import NoteLine
from ebl.transliteration.domain.parallel_line import ParallelLine
from ebl.transliteration.domain.text_line import AlignmentMap, TextLine, merge_tokens
from ebl.transliteration.domain.tokens import Token
from ebl.transliteration.domain.translation_line import Extent, TranslationLine

ManuscriptLineLabel = Tuple[int, Sequence[Label], AbstractLineNumber]


@attr.s(auto_attribs=True, frozen=True)
class ManuscriptLine:
    manuscript_id: int
    labels: Sequence[Label] = attr.ib(validator=validate_labels)
    line: Union[TextLine, EmptyLine]
    paratext: Sequence[Union[DollarLine, NoteLine]] = tuple()
    omitted_words: Sequence[int] = tuple()

    @property
    def label(self) -> Optional[ManuscriptLineLabel]:
        return (
            (self.manuscript_id, self.labels, cast(TextLine, self.line).line_number)
            if isinstance(self.line, TextLine)
            else None
        )

    def merge(self, other: "ManuscriptLine") -> "ManuscriptLine":
        merged_line = self.line.merge(other.line)
        return attr.evolve(other, line=merged_line)

    def update_alignments(self, aligment_map: AlignmentMap) -> "ManuscriptLine":
        return attr.evolve(
            self,
            line=self.line.update_alignments(aligment_map),
            omitted_words=tuple(
                aligment_map[index]
                for index in self.omitted_words
                if index < len(aligment_map) and aligment_map[index] is not None
            ),
        )


@attr.s(auto_attribs=True, frozen=True)
class LineVariant:
    reconstruction: Sequence[Token] = attr.ib(
        converter=pydash.flow(set_enclosure_type, set_language)
    )
    note: Optional[NoteLine] = None
    manuscripts: Sequence[ManuscriptLine] = tuple()
    parallel_lines: Sequence[ParallelLine] = tuple()

    @reconstruction.validator
    def validate_reconstruction(self, _, value):
        validate(value)

    @property
    def manuscript_ids(self) -> Sequence[int]:
        return [manuscript.manuscript_id for manuscript in self.manuscripts]

    @property
    def manuscript_line_labels(self) -> Sequence[ManuscriptLineLabel]:
        return [
            cast(ManuscriptLineLabel, manuscript_line.label)
            for manuscript_line in self.manuscripts
            if manuscript_line.label
        ]

    def get_manuscript_text_line(self, manuscript_id: int) -> Optional[TextLine]:
        return (
            pydash.chain(self.manuscripts)
            .filter(lambda manuscript: manuscript.manuscript_id == manuscript_id)
            .map_(lambda manuscript: manuscript.line)
            .filter(lambda line: isinstance(line, TextLine))
            .head()
            .value()
        )

    def merge(self, other: "LineVariant") -> "LineVariant":
        merged_reconstruction = merge_tokens(self.reconstruction, other.reconstruction)
        alignment_map = create_alignment_map(self.reconstruction, merged_reconstruction)

        def merge_manuscript(
            old: ManuscriptLine, new: ManuscriptLine
        ) -> ManuscriptLine:
            return old.merge(new).update_alignments(alignment_map)

        merged_manuscripts = Merger(repr, merge_manuscript).merge(
            self.manuscripts, other.manuscripts
        )
        return attr.evolve(
            other,
            reconstruction=merged_reconstruction,
            manuscripts=tuple(merged_manuscripts),
        )


@attr.s(auto_attribs=True, frozen=True)
class Line:
    number: AbstractLineNumber
    variants: Sequence[LineVariant]
    is_second_line_of_parallelism: bool = False
    is_beginning_of_section: bool = False
    translation: Sequence[TranslationLine] = attr.ib(default=tuple())

    @translation.validator
    def _validate_translations(self, _, value: Sequence[TranslationLine]) -> None:
        if any(line.extent and cast(Extent, line.extent).labels for line in value):
            raise ValueError("Labels are not allowed in line translations.")

    @property
    def manuscript_ids(self) -> Sequence[int]:
        return [
            manuscript_id
            for variant in self.variants
            for manuscript_id in variant.manuscript_ids
        ]

    @property
    def manuscript_line_labels(self) -> Sequence[ManuscriptLineLabel]:
        return [
            label
            for variant in self.variants
            for label in variant.manuscript_line_labels
        ]

    def get_manuscript_text_line(self, manuscript_id: int) -> Optional[TextLine]:
        return (
            pydash.chain(self.variants)
            .map_(lambda variant: variant.get_manuscript_text_line(manuscript_id))
            .reject(pydash.is_none)
            .head()
            .value()
        )

    def merge(self, other: "Line") -> "Line":
        def inner_merge(old: LineVariant, new: LineVariant) -> LineVariant:
            return old.merge(new)

        merged_variants = Merger(repr, inner_merge).merge(self.variants, other.variants)
        return attr.evolve(other, variants=tuple(merged_variants))
