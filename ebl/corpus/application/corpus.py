from abc import ABC, abstractmethod
from typing import List, Sequence

from ebl.corpus.application.alignment_updater import AlignmentUpdater
from ebl.corpus.application.chapter_hydrator import ChapterHydartor
from ebl.corpus.application.chapter_updater import ChapterUpdater
from ebl.corpus.application.lemmatization import ChapterLemmatization
from ebl.corpus.application.lemmatization_updater import LemmatizationUpdater
from ebl.corpus.application.lines_updater import LinesUpdater
from ebl.corpus.application.manuscripts_updater import ManuscriptUpdater
from ebl.corpus.application.schemas import ChapterSchema
from ebl.corpus.application.text_validator import TextValidator
from ebl.corpus.domain.alignment import Alignment
from ebl.corpus.domain.chapter import Chapter, ChapterId
from ebl.corpus.domain.chapter_info import ChapterInfo
from ebl.corpus.domain.lines_update import LinesUpdate
from ebl.corpus.domain.manuscript import Manuscript
from ebl.corpus.domain.parser import parse_chapter
from ebl.corpus.domain.text import Text, TextId
from ebl.errors import Defect, NotFoundError, DataError
from ebl.fragmentarium.domain.museum_number import MuseumNumber
from ebl.transliteration.application.sign_repository import SignRepository
from ebl.transliteration.domain.transliteration_query import TransliterationQuery
from ebl.users.domain.user import User

COLLECTION = "chapters"


class TextRepository(ABC):
    @abstractmethod
    def create(self, text: Text) -> None:
        ...

    @abstractmethod
    def create_chapter(self, chapter: Chapter) -> None:
        ...

    @abstractmethod
    def find(self, id_: TextId) -> Text:
        ...

    @abstractmethod
    def find_chapter(self, id_: ChapterId) -> Chapter:
        ...

    @abstractmethod
    def list(self) -> List[Text]:
        ...

    @abstractmethod
    def update(self, id_: ChapterId, chapter: Chapter) -> None:
        ...

    @abstractmethod
    def query_by_transliteration(self, query: TransliterationQuery) -> List[Chapter]:
        ...


class Corpus:
    def __init__(
        self,
        repository: TextRepository,
        bibliography,
        changelog,
        sign_repository: SignRepository,
    ):
        self._repository: TextRepository = repository
        self._bibliography = bibliography
        self._changelog = changelog
        self._sign_repository = sign_repository

    def find(self, id_: TextId) -> Text:
        return self._repository.find(id_)

    def find_chapter(self, id_: ChapterId) -> Chapter:
        chapter = self._repository.find_chapter(id_)
        return self._hydrate_references(chapter)

    def search_transliteration(self, query: TransliterationQuery) -> List[ChapterInfo]:
        return (
            []
            if query.is_empty()
            else [
                ChapterInfo.of(chapter, query)
                for chapter in self._repository.query_by_transliteration(query)
            ]
        )

    def list(self) -> List[Text]:
        return self._repository.list()

    def update_alignment(
        self, id_: ChapterId, alignment: Alignment, user: User
    ) -> Chapter:
        return self._update_chapter(id_, AlignmentUpdater(alignment), user)

    def update_manuscript_lemmatization(
        self, id_: ChapterId, lemmatization: ChapterLemmatization, user: User
    ) -> Chapter:
        return self._update_chapter(id_, LemmatizationUpdater(lemmatization), user)

    def update_manuscripts(
        self,
        id_: ChapterId,
        manuscripts: Sequence[Manuscript],
        uncertain_fragments: Sequence[MuseumNumber],
        user: User,
    ) -> Chapter:
        try:
            hydrator = ChapterHydartor(self._bibliography)
            manuscripts = tuple(
                hydrator.hydrate_manuscript(manuscript) for manuscript in manuscripts
            )
        except NotFoundError as error:
            raise DataError(error) from error

        return self._update_chapter(
            id_,
            ManuscriptUpdater(manuscripts, uncertain_fragments, self._sign_repository),
            user,
        )

    def import_lines(self, id_: ChapterId, atf: str, user: User) -> Chapter:
        chapter = self.find_chapter(id_)
        lines = parse_chapter(atf, chapter.manuscripts)
        return self.update_lines(id_, LinesUpdate(lines, set(), {}), user)

    def update_lines(self, id_: ChapterId, lines: LinesUpdate, user: User) -> Chapter:
        return self._update_chapter(
            id_, LinesUpdater(lines, self._sign_repository), user
        )

    def _update_chapter(
        self, id_: ChapterId, updater: ChapterUpdater, user: User
    ) -> Chapter:
        old_chapter = self.find_chapter(id_)
        updated_chapter = updater.update(old_chapter)
        self.update_chapter(id_, old_chapter, updated_chapter, user)
        return updated_chapter

    def update_chapter(
        self, id_: ChapterId, old: Chapter, updated: Chapter, user: User
    ) -> None:
        self._validate_chapter(updated)
        self._create_changelog(old, updated, user)
        self._repository.update(id_, updated)

    def _validate_chapter(self, chapter: Chapter) -> None:
        TextValidator().visit(chapter)

    def _hydrate_references(self, chapter: Chapter) -> Chapter:
        try:
            hydrator = ChapterHydartor(self._bibliography)
            hydrator.visit(chapter)
            return hydrator.chapter
        except NotFoundError as error:
            raise Defect(error) from error

    def _create_changelog(self, old: Chapter, new: Chapter, user: User) -> None:
        old_dict: dict = {**ChapterSchema().dump(old), "_id": old.id_.to_tuple()}
        new_dict: dict = {**ChapterSchema().dump(new), "_id": new.id_.to_tuple()}
        self._changelog.create(COLLECTION, user.profile, old_dict, new_dict)
