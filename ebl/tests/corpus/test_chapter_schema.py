import attr

from ebl.bibliography.application.reference_schema import (
    ApiReferenceSchema,
    ReferenceSchema,
)
from ebl.corpus.application.schemas import ChapterSchema
from ebl.corpus.domain.chapter import Chapter
from ebl.fragmentarium.application.museum_number_schema import MuseumNumberSchema
from ebl.fragmentarium.domain.museum_number import MuseumNumber
from ebl.tests.factories.bibliography import ReferenceFactory
from ebl.tests.factories.corpus import (
    ChapterFactory,
    LineFactory,
    LineVariantFactory,
    ManuscriptFactory,
    ManuscriptLineFactory,
)
from ebl.transliteration.application.line_number_schemas import OneOfLineNumberSchema
from ebl.transliteration.application.line_schemas import (
    NoteLineSchema,
    TranslationLineSchema,
)
from ebl.transliteration.application.one_of_line_schema import (
    OneOfLineSchema,
    ParallelLineSchema,
)
from ebl.transliteration.application.text_schema import TextSchema
from ebl.transliteration.application.token_schemas import OneOfTokenSchema
from ebl.transliteration.domain.line_number import LineNumber
from ebl.transliteration.domain.parallel_line import ParallelComposition
from ebl.transliteration.domain.translation_line import TranslationLine
from ebl.transliteration.domain.markup import StringPart


REFERENCES = (ReferenceFactory.build(with_document=True),)
MANUSCRIPT = ManuscriptFactory.build(references=REFERENCES)
UNCERTAIN_FRAGMENTS = (MuseumNumber.of("K.1"),)
FIRST_MANUSCRIPT_LINE = ManuscriptLineFactory.build(manuscript_id=MANUSCRIPT.id)
SECOND_MANUSCRIPT_LINE = ManuscriptLineFactory.build(manuscript_id=MANUSCRIPT.id)

LINE_VARIANT = LineVariantFactory.build(
    manuscripts=(FIRST_MANUSCRIPT_LINE, SECOND_MANUSCRIPT_LINE),
    parallel_lines=(ParallelComposition(False, "name", LineNumber(2)),),
)
TRANSLATION_LINE = TranslationLine((StringPart("foo"),), "en", None)
LINE = LineFactory.build(variants=(LINE_VARIANT,), translation=(TRANSLATION_LINE,))
CHAPTER = ChapterFactory.build(
    manuscripts=(MANUSCRIPT,), uncertain_fragments=UNCERTAIN_FRAGMENTS, lines=(LINE,)
)


def strip_documents(chapter: Chapter) -> Chapter:
    return attr.evolve(
        chapter,
        manuscripts=tuple(
            attr.evolve(
                manuscript,
                references=tuple(
                    attr.evolve(reference, document=None)
                    for reference in MANUSCRIPT.references
                ),
            )
            for manuscript in chapter.manuscripts
        ),
    )


def to_dict(chapter: Chapter, include_documents=False):
    return {
        "textId": {
            "genre": chapter.text_id.genre.value,
            "category": chapter.text_id.category,
            "index": chapter.text_id.index,
        },
        "classification": chapter.classification.value,
        "stage": chapter.stage.value,
        "version": chapter.version,
        "name": chapter.name,
        "order": chapter.order,
        "signs": list(chapter.signs),
        "parserVersion": chapter.parser_version,
        "manuscripts": [
            {
                "id": manuscript.id,
                "siglumDisambiguator": manuscript.siglum_disambiguator,
                "museumNumber": (
                    (str(manuscript.museum_number) if manuscript.museum_number else "")
                    if include_documents
                    else manuscript.museum_number
                    and MuseumNumberSchema().dump(manuscript.museum_number)
                ),
                "accession": manuscript.accession,
                "periodModifier": manuscript.period_modifier.value,
                "period": manuscript.period.long_name,
                "provenance": manuscript.provenance.long_name,
                "type": manuscript.type.long_name,
                "notes": manuscript.notes,
                "colophon": TextSchema().dump(manuscript.colophon),
                "unplacedLines": TextSchema().dump(manuscript.unplaced_lines),
                "references": (
                    ApiReferenceSchema if include_documents else ReferenceSchema
                )().dump(manuscript.references, many=True),
            }
            for manuscript in chapter.manuscripts
        ],
        "uncertainFragments": MuseumNumberSchema().dump(UNCERTAIN_FRAGMENTS, many=True),
        "lines": [
            {
                "number": OneOfLineNumberSchema().dump(line.number),
                "variants": [
                    {
                        "reconstruction": OneOfTokenSchema().dump(
                            variant.reconstruction, many=True
                        ),
                        "note": variant.note and NoteLineSchema().dump(variant.note),
                        "parallelLines": ParallelLineSchema().dump(
                            variant.parallel_lines, many=True
                        ),
                        "manuscripts": [
                            {
                                "manuscriptId": manuscript_line.manuscript_id,
                                "labels": [
                                    label.to_value() for label in manuscript_line.labels
                                ],
                                "line": OneOfLineSchema().dump(manuscript_line.line),
                                "paratext": OneOfLineSchema().dump(
                                    manuscript_line.paratext, many=True
                                ),
                                "omittedWords": list(manuscript_line.omitted_words),
                            }
                            for manuscript_line in variant.manuscripts
                        ],
                    }
                    for variant in line.variants
                ],
                "isSecondLineOfParallelism": line.is_second_line_of_parallelism,
                "isBeginningOfSection": line.is_beginning_of_section,
                "translation": TranslationLineSchema().dump(
                    line.translation, many=True
                ),
            }
            for line in chapter.lines
        ],
    }


def test_dump():
    assert ChapterSchema().dump(CHAPTER) == to_dict(CHAPTER)


def test_load():
    assert ChapterSchema().load(to_dict(CHAPTER)) == strip_documents(CHAPTER)
