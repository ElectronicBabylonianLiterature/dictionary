from typing import Sequence, Tuple

import attr

from ebl.bibliography.domain.reference import Reference
from ebl.fragmentarium.domain.fragment import Fragment, FragmentNumber
from ebl.fragmentarium.domain.record import RecordEntry, RecordType

Lines = Sequence[Sequence[str]]


@attr.s(frozen=True, auto_attribs=True)
class FragmentInfo:
    number: FragmentNumber
    accession: str
    script: str
    description: str
    matching_lines: Lines
    editor: str
    edition_date: str
    references: Tuple[Reference, ...] = tuple()

    @staticmethod
    def of(fragment: Fragment, matching_lines: Lines = tuple()) -> "FragmentInfo":
        def is_transliteration(entry: RecordEntry) -> bool:
            return entry.type == RecordType.TRANSLITERATION

        def get_date(entry: RecordEntry) -> str:
            return entry.date

        sorted_transliterations = [entry
                                   for entry in fragment.record.entries
                                   if is_transliteration(entry)]
        sorted_transliterations.sort(key=get_date)

        first_transliteration = (sorted_transliterations[0]
                                 if sorted_transliterations
                                 else RecordEntry("", RecordType.TRANSLITERATION, ""))

        return FragmentInfo(
            fragment.number,
            fragment.accession,
            fragment.script,
            fragment.description,
            matching_lines,
            first_transliteration.user,
            first_transliteration.date,
            fragment.references,
        )
