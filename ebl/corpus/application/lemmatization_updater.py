from typing import List, Sequence

import attr
from singledispatchmethod import singledispatchmethod  # pyre-ignore[21]

from ebl.corpus.application.chapter_updater import ChapterUpdater
from ebl.corpus.domain.chapter import Chapter, Line, LineVariant, ManuscriptLine
from ebl.corpus.domain.text import TextItem
from ebl.transliteration.domain.lemmatization import (
    LemmatizationToken,
    LemmatizationError,
)


class LemmatizationUpdater(ChapterUpdater):
    def __init__(
        self,
        chapter_index: int,
        lemmatization: Sequence[Sequence[Sequence[Sequence[LemmatizationToken]]]],
    ):
        super().__init__(chapter_index)
        self._lemmatization = lemmatization
        self._lines: List[Line] = []
        self._variants: List[LineVariant] = []
        self._manuscript_lines: List[ManuscriptLine] = []

    @property
    def line_index(self) -> int:
        return len(self._lines)

    @property
    def variant_index(self) -> int:
        return len(self._variants)

    @property
    def manuscript_line_index(self) -> int:
        return len(self._manuscript_lines)

    @property
    def current_lemmatization(self) -> Sequence[LemmatizationToken]:
        try:
            return self._lemmatization[self.line_index][self.variant_index][
                self.manuscript_line_index + 1
            ]
        except IndexError:
            raise LemmatizationError(
                f"No lemmatization for line {self.line_index} "
                f"variant {self.variant_index} "
                f"manuscript {self.manuscript_line_index}."
            )

    @singledispatchmethod  # pyre-ignore[56]
    def visit(self, item: TextItem) -> None:
        super().visit(item)

    @visit.register(Line)  # pyre-ignore[56]
    def _visit_line(self, line: Line) -> None:
        for variant in line.variants:
            self.visit(variant)

        if len(self._lemmatization[self.line_index]) == len(line.variants):
            self._lines.append(attr.evolve(line, variants=tuple(self._variants)))
            self._variants = []
        else:
            raise LemmatizationError()

    @visit.register(LineVariant)  # pyre-ignore[56]
    def _visit_line_variant(self, variant: LineVariant) -> None:
        for manuscript_line in variant.manuscripts:
            self.visit(manuscript_line)

        if (
            len(self._lemmatization[self.line_index][self.variant_index])
            == len(variant.manuscripts) + 1
        ):
            self._variants.append(
                attr.evolve(
                    variant,
                    text=variant.text.update_lemmatization(
                        self._lemmatization[self.line_index][self.variant_index][0]
                    ),
                    manuscripts=tuple(self._manuscript_lines),
                )
            )
            self._manuscript_lines = []
        else:
            raise LemmatizationError()

    @visit.register(ManuscriptLine)  # pyre-ignore[56]
    def _visit_manuscript_line(self, manuscript_line: ManuscriptLine) -> None:
        updated_line = manuscript_line.line.update_lemmatization(
            self.current_lemmatization
        )
        self._manuscript_lines.append(attr.evolve(manuscript_line, line=updated_line))

    def _update_chapter(self, chapter: Chapter) -> Chapter:
        if len(self._lemmatization) == len(chapter.lines):
            return attr.evolve(chapter, lines=tuple(self._lines))
        else:
            raise LemmatizationError()

    def _after_chapter_update(self) -> None:
        self._lines = []
