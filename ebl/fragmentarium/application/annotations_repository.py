from abc import ABC, abstractmethod

from ebl.fragmentarium.domain.annotation import Annotations
from ebl.fragmentarium.domain.museum_number import MuseumNumber


class AnnotationsRepository(ABC):
    @abstractmethod
    def query_by_museum_number(self, number: MuseumNumber) -> Annotations:
        ...

    @abstractmethod
    def create_or_update(self, annotations: Annotations) -> None:
        ...
