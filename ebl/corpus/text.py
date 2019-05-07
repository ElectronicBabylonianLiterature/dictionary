import collections
from enum import Enum, auto
from typing import Tuple

import attr

from ebl.corpus.label_validator import LabelValidator
from ebl.corpus.enums import Classification, ManuscriptType, Provenance, \
    PeriodModifier, Period, Stage
from ebl.bibliography.reference import Reference
from ebl.text.labels import Label, LineNumberLabel
from ebl.text.line import TextLine
from ebl.text.text import create_tokens

TextId = collections.namedtuple('TextId', ['category', 'index'])


@attr.s(auto_attribs=True, frozen=True)
class Manuscript:
    id: int
    siglum_disambiguator: str = ''
    museum_number: str = ''
    accession: str = attr.ib(default='')
    period_modifier: PeriodModifier = PeriodModifier.NONE
    period: Period = Period.NEO_ASSYRIAN
    provenance: Provenance = Provenance.NINEVEH
    type: ManuscriptType = ManuscriptType.LIBRARY
    notes: str = ''
    references: Tuple[Reference, ...] = tuple()

    @accession.validator
    def validate_accession(self, _, value):
        if self.museum_number and value:
            raise ValueError(f'Accession given when museum number present.')

    @property
    def siglum(self):
        return (self.provenance,
                self.period,
                self.type,
                self.siglum_disambiguator)

    def accept(self, visitor: 'TextVisitor') -> None:
        visitor.visit_manuscript(self)

    @staticmethod
    def from_dict(manuscript: dict) -> 'Manuscript':
        return Manuscript(
            manuscript['id'],
            manuscript['siglumDisambiguator'],
            manuscript['museumNumber'],
            manuscript['accession'],
            PeriodModifier(manuscript['periodModifier']),
            Period.from_name(manuscript['period']),
            Provenance.from_name(manuscript['provenance']),
            ManuscriptType.from_name(manuscript['type']),
            manuscript['notes'],
            tuple(
                Reference.from_dict(reference)
                for reference in manuscript['references']
            )
        )


def validate_labels(_instance, _attribute, value: Tuple[Label, ...]) -> None:
    validator = LabelValidator()
    for label in value:
        label.accept(validator)

    if not validator.is_valid:
        raise ValueError(
            f'Invalid labels "{[value.to_value() for value in value]}".'
        )


@attr.s(auto_attribs=True, frozen=True)
class ManuscriptLine:
    manuscript_id: int
    labels: Tuple[Label, ...] = attr.ib(validator=validate_labels)
    line: TextLine

    def accept(self, visitor: 'TextVisitor') -> None:
        visitor.visit_manuscript_line(self)

    @staticmethod
    def from_dict(data):
        return ManuscriptLine(
            data['manuscriptId'],
            tuple(Label.parse(label) for label in data['labels']),
            TextLine.of_iterable(
                LineNumberLabel.from_atf(data['line']['prefix']),
                create_tokens(data['line']['content'])
            )
        )


@attr.s(auto_attribs=True, frozen=True)
class Line:
    number: LineNumberLabel
    reconstruction: str = ''
    manuscripts: Tuple[ManuscriptLine, ...] = tuple()

    def accept(self, visitor: 'TextVisitor') -> None:
        if visitor.is_pre_order:
            visitor.visit_line(self)

        for manuscript_line in self.manuscripts:
            manuscript_line.accept(visitor)

        if visitor.is_post_order:
            visitor.visit_line(self)

    @staticmethod
    def from_dict(data):
        return Line(LineNumberLabel(data['number']),
                    data['reconstruction'],
                    tuple(ManuscriptLine.from_dict(line)
                          for line in data['manuscripts']))


@attr.s(auto_attribs=True, frozen=True)
class Chapter:
    classification: Classification = Classification.ANCIENT
    stage: Stage = Stage.NEO_ASSYRIAN
    version: str = ''
    name: str = ''
    order: int = 0
    manuscripts: Tuple[Manuscript, ...] = tuple()
    lines: Tuple[Line, ...] = tuple()

    def __attrs_post_init__(self) -> None:
        self.accept(ManuscriptIdValidator())

    def accept(self, visitor: 'TextVisitor') -> None:
        if visitor.is_pre_order:
            visitor.visit_chapter(self)

        for manuscript in self.manuscripts:
            manuscript.accept(visitor)

        for line in self.lines:
            line.accept(visitor)

        if visitor.is_post_order:
            visitor.visit_chapter(self)

    @staticmethod
    def from_dict(chapter: dict) -> 'Chapter':
        return Chapter(
            Classification(chapter['classification']),
            Stage(chapter['stage']),
            chapter['version'],
            chapter['name'],
            chapter['order'],
            tuple(
                Manuscript.from_dict(manuscript)
                for manuscript in chapter['manuscripts']
            ),
            tuple(
                Line.from_dict(line)
                for line in chapter.get('lines', [])
            )
        )


@attr.s(auto_attribs=True, frozen=True)
class Text:
    category: int
    index: int
    name: str
    number_of_verses: int
    approximate_verses: bool
    chapters: Tuple[Chapter, ...] = tuple()

    @property
    def id(self) -> TextId:
        # pylint: disable=C0103
        return TextId(self.category, self.index)

    def accept(self, visitor: 'TextVisitor') -> None:
        if visitor.is_pre_order:
            visitor.visit_text(self)

        for chapter in self.chapters:
            chapter.accept(visitor)

        if visitor.is_post_order:
            visitor.visit_text(self)

    @staticmethod
    def from_dict(text: dict) -> 'Text':
        return Text(
            text['category'],
            text['index'],
            text['name'],
            text['numberOfVerses'],
            text['approximateVerses'],
            tuple(
                Chapter.from_dict(chapter)
                for chapter in text['chapters']
            )
        )


class TextVisitor:

    class Order(Enum):
        PRE = auto()
        POST = auto()

    def __init__(self, order: 'TextVisitor.Order'):
        self._order = order

    @property
    def is_post_order(self) -> bool:
        return self._order == TextVisitor.Order.POST

    @property
    def is_pre_order(self) -> bool:
        return self._order == TextVisitor.Order.PRE

    def visit_text(self, text: Text) -> None:
        pass

    def visit_chapter(self, chapter: Chapter) -> None:
        pass

    def visit_manuscript(self, manuscript: Manuscript) -> None:
        pass

    def visit_line(self, line: Line) -> None:
        pass

    def visit_manuscript_line(self, manuscript_line: ManuscriptLine) -> None:
        pass


class ManuscriptIdValidator(TextVisitor):

    def __init__(self):
        super().__init__(TextVisitor.Order.POST)
        self._manuscripts_ids = []
        self._sigla = []
        self._used_manuscripts_ids = set()

    def visit_chapter(self, _) -> None:
        def get_duplicates(collection: list) -> list:
            return [item
                    for item, count
                    in collections.Counter(collection).items()
                    if count > 1]

        errors = []

        orphans = self._used_manuscripts_ids - set(self._manuscripts_ids)
        if orphans:
            errors.append(f'Missing manuscripts: {orphans}.')

        duplicate_ids = get_duplicates(self._manuscripts_ids)
        if duplicate_ids:
            errors.append(f'Duplicate manuscript IDs: {duplicate_ids}.')

        duplicate_sigla = get_duplicates(self._sigla)
        if duplicate_sigla:
            errors.append(f'Duplicate sigla: {duplicate_sigla}.')

        if errors:
            raise ValueError(f'Invalid manuscripts: {errors}.')

        self._manuscripts_ids = []
        self._sigla = []
        self._used_manuscripts_ids = set()

    def visit_manuscript(self, manuscript: Manuscript) -> None:
        self._manuscripts_ids.append(manuscript.id)
        self._sigla.append(manuscript.siglum)

    def visit_manuscript_line(self, manuscript_line: ManuscriptLine) -> None:
        self._used_manuscripts_ids.add(manuscript_line.manuscript_id)
