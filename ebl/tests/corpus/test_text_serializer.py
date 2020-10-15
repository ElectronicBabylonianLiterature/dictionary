from ebl.bibliography.application.reference_schema import (
    ApiReferenceSchema,
    ReferenceSchema,
)
from ebl.corpus.application.text_serializer import serialize, deserialize
from ebl.tests.factories.bibliography import ReferenceFactory
from ebl.tests.factories.corpus import (
    ChapterFactory,
    LineFactory,
    ManuscriptFactory,
    ManuscriptLineFactory,
    TextFactory,
)
from ebl.transliteration.application.line_schemas import NoteLineSchema, TextLineSchema
from ebl.transliteration.application.one_of_line_schema import OneOfLineSchema
from ebl.fragmentarium.application.museum_number_schema import MuseumNumberSchema
import attr


REFERENCES = (ReferenceFactory.build(with_document=True),)  # pyre-ignore[16]
MANUSCRIPT = ManuscriptFactory.build(references=REFERENCES)  # pyre-ignore[16]
MANUSCRIPT_LINE = ManuscriptLineFactory.build(  # pyre-ignore[16]
    manuscript_id=MANUSCRIPT.id
)
LINE = LineFactory.build(manuscripts=(MANUSCRIPT_LINE,))  # pyre-ignore[16]
CHAPTER = ChapterFactory.build(  # pyre-ignore[16]
    manuscripts=(MANUSCRIPT,), lines=(LINE,)
)
TEXT = TextFactory.build(chapters=(CHAPTER,))  # pyre-ignore[16]
TEXT_WITHOUT_DOCUMENTS = attr.evolve(
    TEXT,
    chapters=(
        attr.evolve(
            CHAPTER,
            manuscripts=(
                attr.evolve(
                    MANUSCRIPT,
                    references=tuple(
                        attr.evolve(reference, document=None)
                        for reference in MANUSCRIPT.references
                    ),
                ),
            ),
        ),
    ),
)


def to_dict(include_documents=False):
    return {
        "category": TEXT.category,
        "index": TEXT.index,
        "name": TEXT.name,
        "numberOfVerses": TEXT.number_of_verses,
        "approximateVerses": TEXT.approximate_verses,
        "chapters": [
            {
                "classification": CHAPTER.classification.value,
                "stage": CHAPTER.stage.value,
                "version": CHAPTER.version,
                "name": CHAPTER.name,
                "order": CHAPTER.order,
                "parserVersion": CHAPTER.parser_version,
                "manuscripts": [
                    {
                        "id": MANUSCRIPT.id,
                        "siglumDisambiguator": MANUSCRIPT.siglum_disambiguator,
                        "museumNumber": (
                            (
                                str(MANUSCRIPT.museum_number)
                                if MANUSCRIPT.museum_number
                                else ""
                            )
                            if include_documents
                            else MANUSCRIPT.museum_number
                            and MuseumNumberSchema().dump(MANUSCRIPT.museum_number)
                        ),
                        "accession": MANUSCRIPT.accession,
                        "periodModifier": MANUSCRIPT.period_modifier.value,
                        "period": MANUSCRIPT.period.long_name,
                        "provenance": MANUSCRIPT.provenance.long_name,
                        "type": MANUSCRIPT.type.long_name,
                        "notes": MANUSCRIPT.notes,
                        "references": (
                            ApiReferenceSchema if include_documents else ReferenceSchema
                        )().dump(MANUSCRIPT.references, many=True),
                    }
                ],
                "lines": [
                    {
                        "text": TextLineSchema().dump(LINE.text),
                        "note": LINE.note and NoteLineSchema().dump(LINE.note),
                        "isSecondLineOfParallelism": LINE.is_second_line_of_parallelism,
                        "isBeginningOfSection": LINE.is_beginning_of_section,
                        "manuscripts": [
                            {
                                "manuscriptId": MANUSCRIPT_LINE.manuscript_id,
                                "labels": [
                                    label.to_value() for label in MANUSCRIPT_LINE.labels
                                ],
                                "line": TextLineSchema().dump(MANUSCRIPT_LINE.line),
                                "paratext": OneOfLineSchema().dump(
                                    MANUSCRIPT_LINE.paratext, many=True
                                ),
                            }
                        ],
                    }
                ],
            }
        ],
    }


def test_serialize():
    assert serialize(TEXT) == to_dict()


def test_deserialize():
    assert deserialize(to_dict()) == TEXT_WITHOUT_DOCUMENTS
