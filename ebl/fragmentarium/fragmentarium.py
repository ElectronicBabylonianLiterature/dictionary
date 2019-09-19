from abc import ABC, abstractmethod
from typing import Dict, List, Tuple

from ebl.auth0 import User
from ebl.bibliography.reference import Reference
from ebl.fragment.fragment import Fragment, FragmentNumber
from ebl.fragment.fragment_info import FragmentInfo
from ebl.fragment.transliteration import Transliteration
from ebl.fragment.transliteration_query import TransliterationQuery
from ebl.text.lemmatization import Lemmatization

COLLECTION = 'fragments'


class FragmentRepository(ABC):
    @abstractmethod
    def create(self, fragment: Fragment) -> FragmentNumber:
        ...

    @abstractmethod
    def find(self, number: FragmentNumber) -> Fragment:
        ...

    @abstractmethod
    def update_transliteration(self, fragment: Fragment) -> None:
        ...

    @abstractmethod
    def update_lemmatization(self, fragment: Fragment) -> None:
        ...

    @abstractmethod
    def update_references(self, fragment: Fragment) -> None:
        ...

    @abstractmethod
    def count_transliterated_fragments(self) -> int:
        ...

    @abstractmethod
    def count_lines(self) -> int:
        ...

    @abstractmethod
    def search(self, number: str) -> List[Fragment]:
        ...

    @abstractmethod
    def find_random(self) -> List[Fragment]:
        ...

    @abstractmethod
    def find_interesting(self) -> List[Fragment]:
        ...

    @abstractmethod
    def find_latest(self) -> List[Fragment]:
        ...

    @abstractmethod
    def find_needs_revision(self) -> List[FragmentInfo]:
        ...

    @abstractmethod
    def search_signs(self, query: TransliterationQuery) -> List[Fragment]:
        ...

    @abstractmethod
    def folio_pager(self,
                    folio_name: str,
                    folio_number: str,
                    number: FragmentNumber) -> dict:
        ...

    @abstractmethod
    def find_lemmas(self, word: str) -> List[List[dict]]:
        ...


class Fragmentarium:

    def __init__(self,
                 repository: FragmentRepository,
                 changelog,
                 dictionary,
                 bibliography):

        self._repository = repository
        self._changelog = changelog
        self._dictionary = dictionary
        self._bibliography = bibliography

    def update_transliteration(self,
                               number: FragmentNumber,
                               transliteration: Transliteration,
                               user: User) -> Fragment:
        fragment = self._repository.find(number)

        updated_fragment = fragment.update_transliteration(
            transliteration,
            user
        )

        self._create_changlelog(user, fragment, updated_fragment)
        self._repository.update_transliteration(updated_fragment)

        return updated_fragment

    def update_lemmatization(self,
                             number: FragmentNumber,
                             lemmatization: Lemmatization,
                             user: User) -> Fragment:
        fragment = self._repository.find(number)
        updated_fragment = fragment.update_lemmatization(
            lemmatization
        )

        self._create_changlelog(user, fragment, updated_fragment)
        self._repository.update_lemmatization(updated_fragment)

        return updated_fragment

    def update_references(self,
                          number: FragmentNumber,
                          references: Tuple[Reference, ...],
                          user: User) -> Fragment:
        fragment = self._repository.find(number)
        self._bibliography.validate_references(references)

        updated_fragment = fragment.set_references(references)

        self._create_changlelog(user, fragment, updated_fragment)
        self._repository.update_references(updated_fragment)

        return updated_fragment

    def statistics(self) -> Dict[str, int]:
        return {
            'transliteratedFragments': (self
                                        ._repository
                                        .count_transliterated_fragments()),
            'lines': self._repository.count_lines()
        }

    def find(self, number: FragmentNumber) -> Fragment:
        return self._repository.find(number)

    def search(self, number: str) -> List[FragmentInfo]:
        return list(map(FragmentInfo.of, self._repository.search(number)))

    def find_random(self) -> List[FragmentInfo]:
        return list(map(FragmentInfo.of, self._repository.find_random()))

    def find_interesting(self) -> List[FragmentInfo]:
        return list(map(FragmentInfo.of, self._repository.find_interesting()))

    def find_latest(self) -> List[FragmentInfo]:
        return list(map(FragmentInfo.of, self._repository.find_latest()))

    def find_needs_revision(self) -> List[FragmentInfo]:
        return self._repository.find_needs_revision()

    def search_signs(self, query: TransliterationQuery) -> List[FragmentInfo]:
        return [
            FragmentInfo.of(fragment, fragment.get_matching_lines(query))
            for fragment
            in self._repository.search_signs(query)
        ]

    def create(self, fragment: Fragment) -> FragmentNumber:
        return self._repository.create(fragment)

    def folio_pager(self,
                    folio_name: str,
                    folio_number: str,
                    number: FragmentNumber) -> dict:
        return self._repository.folio_pager(folio_name, folio_number, number)

    def find_lemmas(self, word: str) -> List[List[dict]]:
        return [
            [
                self._dictionary.find(unique_lemma)
                for unique_lemma
                in result
            ]
            for result
            in self._repository.find_lemmas(word)
        ]

    def _create_changlelog(self,
                           user: User,
                           fragment: Fragment,
                           updated_fragment: Fragment) -> None:
        self._changelog.create(
            COLLECTION,
            user.profile,
            fragment.to_dict(),
            updated_fragment.to_dict()
        )
