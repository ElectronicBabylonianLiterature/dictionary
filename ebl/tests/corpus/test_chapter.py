from typing import Sequence

import attr
import pytest

from ebl.corpus.domain.chapter import Chapter, Classification, TextLineEntry
from ebl.corpus.domain.line import Line, LineVariant, ManuscriptLine
from ebl.corpus.domain.manuscript import (
    Manuscript,
    ManuscriptType,
    Period,
    PeriodModifier,
    Provenance,
    Siglum,
)
from ebl.corpus.domain.stage import Stage
from ebl.corpus.domain.text_id import TextId
from ebl.fragmentarium.domain.museum_number import MuseumNumber
from ebl.tests.factories.bibliography import ReferenceFactory
from ebl.transliteration.domain.atf import Ruling, Surface
from ebl.transliteration.domain.dollar_line import RulingDollarLine
from ebl.transliteration.domain.enclosure_tokens import BrokenAway
from ebl.transliteration.domain.genre import Genre
from ebl.transliteration.domain.labels import ColumnLabel, Label, SurfaceLabel
from ebl.transliteration.domain.line import EmptyLine
from ebl.transliteration.domain.line_number import LineNumber
from ebl.transliteration.domain.markup import StringPart
from ebl.transliteration.domain.normalized_akkadian import AkkadianWord
from ebl.transliteration.domain.note_line import NoteLine
from ebl.transliteration.domain.parallel_line import ParallelComposition
from ebl.transliteration.domain.sign_tokens import Reading
from ebl.transliteration.domain.text import Text as Transliteration
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.tokens import ValueToken
from ebl.transliteration.domain.translation_line import Extent, TranslationLine
from ebl.transliteration.domain.word_tokens import Word


GENRE = Genre.LITERATURE
CATEGORY = 1
INDEX = 2
NAME = "Palm & Vine"
VERSES = 100
APPROXIMATE = True
CLASSIFICATION = Classification.ANCIENT
STAGE = Stage.NEO_BABYLONIAN
VERSION = "A"
CHAPTER_NAME = "IIc"
ORDER = 1
MANUSCRIPT_ID = 9001
SIGLUM_DISAMBIGUATOR = "1c"
MUSEUM_NUMBER = MuseumNumber("BM", "x")
ACCESSION = ""
PERIOD_MODIFIER = PeriodModifier.LATE
PERIOD = Period.OLD_BABYLONIAN
PROVENANCE = Provenance.NINEVEH
TYPE = ManuscriptType.LIBRARY
NOTES = "some notes"
COLOPHON = Transliteration.of_iterable(
    [TextLine(LineNumber(1, True), (Word.of([Reading.of_name("ku")]),))]
)
UNPLACED_LINES = Transliteration.of_iterable(
    [TextLine(LineNumber(4, True), (Word.of([Reading.of_name("bu")]),))]
)
REFERENCES = (ReferenceFactory.build(),)
LINE_NUMBER = LineNumber(1)
LINE_RECONSTRUCTION = (AkkadianWord.of((ValueToken.of("buāru"),)),)
IS_SECOND_LINE_OF_PARALLELISM = True
IS_BEGINNING_OF_SECTION = True
LABELS = (SurfaceLabel.from_label(Surface.OBVERSE),)
PARATEXT = (NoteLine((StringPart("note"),)), RulingDollarLine(Ruling.SINGLE))
OMITTED_WORDS = (1,)

NOTE = None
PARALLEL_LINES = (ParallelComposition(False, "a composition", LineNumber(7)),)
TRANSLATION = (TranslationLine((StringPart("foo"),), "en", None),)
SIGNS = ("FOO BAR",)

MANUSCRIPT_TEXT_1 = TextLine(
    LineNumber(1), (Word.of([Reading.of([ValueToken.of("ku")])]),)
)

LINE_VARIANT_1 = LineVariant(
    LINE_RECONSTRUCTION,
    NOTE,
    (
        ManuscriptLine(
            MANUSCRIPT_ID, LABELS, MANUSCRIPT_TEXT_1, PARATEXT, OMITTED_WORDS
        ),
    ),
    PARALLEL_LINES,
)
LINE_1 = Line(
    LINE_NUMBER,
    (LINE_VARIANT_1,),
    IS_SECOND_LINE_OF_PARALLELISM,
    IS_BEGINNING_OF_SECTION,
    TRANSLATION,
)

LINE_VARIANT_2 = LineVariant(
    LINE_RECONSTRUCTION, None, (ManuscriptLine(MANUSCRIPT_ID, tuple(), EmptyLine()),)
)
LINE_2 = Line(LineNumber(2), (LINE_VARIANT_2,))

MANUSCRIPT_TEXT_3 = attr.evolve(MANUSCRIPT_TEXT_1, line_number=LineNumber(3))
LINE_VARIANT_3 = LineVariant(
    LINE_RECONSTRUCTION,
    None,
    (ManuscriptLine(MANUSCRIPT_ID, tuple(), MANUSCRIPT_TEXT_3),),
)
LINE_3 = Line(LineNumber(3), (LINE_VARIANT_3,))

TEXT_ID = TextId(GENRE, CATEGORY, INDEX)
CHAPTER = Chapter(
    TEXT_ID,
    CLASSIFICATION,
    STAGE,
    VERSION,
    CHAPTER_NAME,
    ORDER,
    (
        Manuscript(
            MANUSCRIPT_ID,
            SIGLUM_DISAMBIGUATOR,
            MUSEUM_NUMBER,
            ACCESSION,
            PERIOD_MODIFIER,
            PERIOD,
            PROVENANCE,
            TYPE,
            NOTES,
            COLOPHON,
            UNPLACED_LINES,
            REFERENCES,
        ),
    ),
    (MUSEUM_NUMBER,),
    (LINE_1, LINE_2, LINE_3),
    SIGNS,
)


def test_constructor_sets_correct_fields():
    assert CHAPTER.text_id == TextId(GENRE, CATEGORY, INDEX)
    assert CHAPTER.classification == CLASSIFICATION
    assert CHAPTER.stage == STAGE
    assert CHAPTER.version == VERSION
    assert CHAPTER.name == CHAPTER_NAME
    assert CHAPTER.order == ORDER
    assert CHAPTER.uncertain_fragments == (MUSEUM_NUMBER,)
    assert CHAPTER.manuscripts[0].id == MANUSCRIPT_ID
    assert CHAPTER.manuscripts[0].siglum == Siglum(
        PROVENANCE, PERIOD, TYPE, SIGLUM_DISAMBIGUATOR
    )
    assert CHAPTER.manuscripts[0].siglum_disambiguator == SIGLUM_DISAMBIGUATOR
    assert CHAPTER.manuscripts[0].museum_number == MUSEUM_NUMBER
    assert CHAPTER.manuscripts[0].accession == ACCESSION
    assert CHAPTER.manuscripts[0].period_modifier == PERIOD_MODIFIER
    assert CHAPTER.manuscripts[0].period == PERIOD
    assert CHAPTER.manuscripts[0].provenance == PROVENANCE
    assert CHAPTER.manuscripts[0].type == TYPE
    assert CHAPTER.manuscripts[0].notes == NOTES
    assert CHAPTER.manuscripts[0].colophon == COLOPHON
    assert CHAPTER.manuscripts[0].unplaced_lines == UNPLACED_LINES
    assert CHAPTER.manuscripts[0].references == REFERENCES
    assert CHAPTER.lines[0].number == LINE_NUMBER
    assert CHAPTER.lines[0].variants[0].reconstruction == LINE_RECONSTRUCTION
    assert CHAPTER.lines[0].variants[0].note == NOTE
    assert CHAPTER.lines[0].variants[0].parallel_lines == PARALLEL_LINES
    assert CHAPTER.lines[0].variants[0].manuscripts[0].manuscript_id == MANUSCRIPT_ID
    assert CHAPTER.lines[0].variants[0].manuscripts[0].labels == LABELS
    assert CHAPTER.lines[0].variants[0].manuscripts[0].line == MANUSCRIPT_TEXT_1
    assert CHAPTER.lines[0].variants[0].manuscripts[0].paratext == PARATEXT
    assert CHAPTER.lines[0].variants[0].manuscripts[0].omitted_words == OMITTED_WORDS
    assert (
        CHAPTER.lines[0].is_second_line_of_parallelism == IS_SECOND_LINE_OF_PARALLELISM
    )
    assert CHAPTER.lines[0].is_beginning_of_section == IS_BEGINNING_OF_SECTION
    assert CHAPTER.lines[0].translation == TRANSLATION
    assert CHAPTER.signs == SIGNS


def test_duplicate_ids_are_invalid():
    with pytest.raises(ValueError):
        Chapter(
            TEXT_ID,
            manuscripts=(
                Manuscript(MANUSCRIPT_ID, siglum_disambiguator="a"),
                Manuscript(MANUSCRIPT_ID, siglum_disambiguator="b"),
            ),
        )


def test_duplicate_sigla_are_invalid():
    with pytest.raises(ValueError):
        Chapter(
            TEXT_ID,
            manuscripts=(
                Manuscript(
                    MANUSCRIPT_ID,
                    siglum_disambiguator=SIGLUM_DISAMBIGUATOR,
                    period=PERIOD,
                    provenance=PROVENANCE,
                    type=TYPE,
                ),
                Manuscript(
                    MANUSCRIPT_ID + 1,
                    siglum_disambiguator=SIGLUM_DISAMBIGUATOR,
                    period=PERIOD,
                    provenance=PROVENANCE,
                    type=TYPE,
                ),
            ),
        )


def test_missing_manuscripts_are_invalid():
    with pytest.raises(ValueError):
        Chapter(
            TEXT_ID,
            manuscripts=(Manuscript(MANUSCRIPT_ID),),
            lines=(
                Line(
                    LINE_NUMBER,
                    (
                        LineVariant(
                            LINE_RECONSTRUCTION,
                            NOTE,
                            (
                                ManuscriptLine(
                                    MANUSCRIPT_ID + 1, LABELS, MANUSCRIPT_TEXT_1
                                ),
                            ),
                        ),
                    ),
                    IS_SECOND_LINE_OF_PARALLELISM,
                    IS_BEGINNING_OF_SECTION,
                ),
            ),
        )


@pytest.mark.parametrize(
    "make_chapter",
    [
        lambda: Chapter(
            TEXT_ID,
            manuscripts=(Manuscript(MANUSCRIPT_ID),),
            lines=(
                Line(
                    LINE_NUMBER,
                    (
                        LineVariant(
                            LINE_RECONSTRUCTION,
                            NOTE,
                            (
                                ManuscriptLine(
                                    MANUSCRIPT_ID, LABELS, MANUSCRIPT_TEXT_1
                                ),
                                ManuscriptLine(
                                    MANUSCRIPT_ID, LABELS, MANUSCRIPT_TEXT_1
                                ),
                            ),
                        ),
                    ),
                    IS_SECOND_LINE_OF_PARALLELISM,
                    IS_BEGINNING_OF_SECTION,
                ),
            ),
        ),
        lambda: Chapter(
            TEXT_ID,
            manuscripts=(Manuscript(MANUSCRIPT_ID),),
            lines=(
                Line(
                    LINE_NUMBER,
                    (
                        LineVariant(
                            LINE_RECONSTRUCTION,
                            NOTE,
                            (ManuscriptLine(MANUSCRIPT_ID, LABELS, MANUSCRIPT_TEXT_1),),
                        ),
                    ),
                    IS_SECOND_LINE_OF_PARALLELISM,
                    IS_BEGINNING_OF_SECTION,
                ),
                Line(
                    LineNumber(2),
                    (
                        LineVariant(
                            LINE_RECONSTRUCTION,
                            NOTE,
                            (ManuscriptLine(MANUSCRIPT_ID, LABELS, MANUSCRIPT_TEXT_1),),
                        ),
                    ),
                    IS_SECOND_LINE_OF_PARALLELISM,
                    IS_BEGINNING_OF_SECTION,
                ),
            ),
        ),
    ],
)
def test_duplicate_manuscript_line_labels_are_invalid(make_chapter):
    with pytest.raises(ValueError):
        make_chapter()


def test_duplicate_line_numbers_invalid():
    with pytest.raises(ValueError):
        Chapter(TEXT_ID, lines=(LINE_1, LINE_1))


@pytest.mark.parametrize(  # pyre-ignore[56]
    "labels",
    [
        (ColumnLabel.from_label("i"), ColumnLabel.from_label("ii")),
        (
            SurfaceLabel.from_label(Surface.OBVERSE),
            SurfaceLabel.from_label(Surface.REVERSE),
        ),
        (ColumnLabel.from_label("i"), SurfaceLabel.from_label(Surface.REVERSE)),
    ],
)
def test_invalid_labels(labels: Sequence[Label]):
    with pytest.raises(ValueError):
        ManuscriptLine(manuscript_id=1, labels=labels, line=TextLine(LineNumber(1)))


def test_invalid_reconstruction():
    with pytest.raises(ValueError):
        Line(
            LINE_NUMBER,
            (LineVariant((AkkadianWord.of((BrokenAway.open(),)),), NOTE, tuple()),),
            False,
            False,
        )


def test_stage():
    periods = [period.long_name for period in Period if period is not Period.NONE]
    stages = [stage.value for stage in Stage]
    assert stages == [*periods, "Standard Babylonian"]


def test_update_manuscript_alignment():
    word1 = Word.of(
        [Reading.of_name("ku")], alignment=0, variant=Word.of([Reading.of_name("uk")])
    )
    word2 = Word.of(
        [Reading.of_name("ra")], alignment=1, variant=Word.of([Reading.of_name("ar")])
    )
    word3 = Word.of(
        [Reading.of_name("pa")], alignment=2, variant=Word.of([Reading.of_name("ap")])
    )
    manuscript = ManuscriptLine(
        MANUSCRIPT_ID,
        LABELS,
        TextLine(LineNumber(1), (word1, word2, word3)),
        PARATEXT,
        (1, 3),
    )
    expected = ManuscriptLine(
        MANUSCRIPT_ID,
        LABELS,
        TextLine(
            LineNumber(1),
            (
                word1.set_alignment(None, None),
                word2.set_alignment(0, word2.variant),
                word3.set_alignment(None, None),
            ),
        ),
        PARATEXT,
        (0,),
    )

    assert manuscript.update_alignments([None, 0]) == expected


def test_text_lines() -> None:
    assert CHAPTER.text_lines == [
        [
            TextLineEntry(MANUSCRIPT_TEXT_1, 0),
            TextLineEntry(MANUSCRIPT_TEXT_3, 2),
            *[TextLineEntry(line, None) for line in COLOPHON.text_lines],
            *[TextLineEntry(line, None) for line in UNPLACED_LINES.text_lines],
        ]
    ]


def test_invalid_extent() -> None:
    with pytest.raises(ValueError):
        Chapter(
            TextId(GENRE, 0, 0),
            manuscripts=(Manuscript(MANUSCRIPT_ID),),
            lines=(
                Line(
                    LineNumber(1),
                    (LINE_VARIANT_1,),
                    translation=(
                        TranslationLine(tuple(), extent=Extent(LineNumber(2))),
                    ),
                ),
            ),
        )


def test_extent_before_translation() -> None:
    with pytest.raises(ValueError):
        Chapter(
            TextId(GENRE, 0, 0),
            manuscripts=(Manuscript(MANUSCRIPT_ID),),
            lines=(
                Line(LineNumber(1), (LINE_VARIANT_1,)),
                Line(
                    LineNumber(2),
                    (LINE_VARIANT_2,),
                    translation=(
                        TranslationLine(tuple(), extent=Extent(LineNumber(1))),
                    ),
                ),
            ),
        )


def test_overlapping() -> None:
    with pytest.raises(ValueError):
        Chapter(
            TextId(GENRE, 0, 0),
            manuscripts=(Manuscript(MANUSCRIPT_ID),),
            lines=(
                Line(
                    LineNumber(1),
                    (LINE_VARIANT_1,),
                    translation=(
                        TranslationLine(tuple(), extent=Extent(LineNumber(2))),
                    ),
                ),
                Line(
                    LineNumber(2),
                    (LINE_VARIANT_2,),
                    translation=(TranslationLine(tuple()),),
                ),
            ),
        )


def test_overlapping_languages() -> None:
    Chapter(
        TextId(GENRE, 0, 0),
        manuscripts=(Manuscript(MANUSCRIPT_ID),),
        lines=(
            Line(
                LineNumber(1),
                (LINE_VARIANT_1,),
                translation=(TranslationLine(tuple(), "en", Extent(LineNumber(2))),),
            ),
            Line(
                LineNumber(2),
                (LINE_VARIANT_2,),
                translation=(TranslationLine(tuple(), "de"),),
            ),
        ),
    )
