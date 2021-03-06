from typing import Sequence

import attr

from ebl.fragmentarium.domain.museum_number import MuseumNumber


@attr.attrs(auto_attribs=True, frozen=True)
class Geometry:
    x: float
    y: float
    width: float
    height: float


@attr.attrs(auto_attribs=True, frozen=True)
class AnnotationData:
    id: str
    value: str
    path: Sequence[int]


@attr.attrs(auto_attribs=True, frozen=True)
class Annotation:
    geometry: Geometry
    data: AnnotationData


@attr.attrs(auto_attribs=True, frozen=True)
class Annotations:
    fragment_number: MuseumNumber
    annotations: Sequence[Annotation] = tuple()
