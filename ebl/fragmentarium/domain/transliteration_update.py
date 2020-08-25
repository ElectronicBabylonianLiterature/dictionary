from typing import Optional

import attr

from ebl.transliteration.domain.clean_atf import CleanAtf
from ebl.transliteration.domain.text import Text
from ebl.transliteration.domain.transliteration_error import TransliterationError


@attr.s(auto_attribs=True, frozen=True)
class TransliterationUpdate:
    text: Text = Text()
    notes: str = ""
    signs: Optional[str] = attr.ib(default=None)

    @signs.validator
    def _check_signs(self, _attribute, value):
        clean_atf = CleanAtf(self.text.atf)
        lines = clean_atf.atf.split("\n")

        def get_line_number(filtered_line_number):
            line = clean_atf.filtered[filtered_line_number]
            return lines.index(line) + 1

        if value is not None:
            signs = value.split("\n")
            questionable_lines = [
                get_line_number(index)
                for index, line in enumerate(signs)
                if "?" in line
            ]
            if questionable_lines:
                raise TransliterationError(
                    [
                        {"description": "Invalid value", "lineNumber": line_number,}
                        for line_number in questionable_lines
                    ]
                )
