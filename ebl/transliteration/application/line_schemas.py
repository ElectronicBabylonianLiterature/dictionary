from marshmallow import EXCLUDE, fields, post_load, Schema

from ebl.transliteration.application.line_number_schemas import (
    dump_line_number,
    load_line_number,
)
from ebl.transliteration.application.note_line_part_schemas import (
    dump_parts,
    load_parts,
)
from ebl.transliteration.application.token_schemas import dump_tokens, load_tokens
from ebl.transliteration.domain.labels import LineNumberLabel
from ebl.transliteration.domain.line import ControlLine, EmptyLine
from ebl.transliteration.domain.note_line import NoteLine
from ebl.transliteration.domain.text_line import TextLine


class LineBaseSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    prefix = fields.String(required=True)
    content = fields.Function(
        lambda line: dump_tokens(line.content), load_tokens, required=True
    )


class TextLineSchema(LineBaseSchema):
    line_number = fields.Function(
        lambda line: dump_line_number(line.line_number),
        load_line_number,
        missing=None,
        data_key="lineNumber",
    )

    @post_load
    def make_line(self, data, **kwargs):
        return TextLine.of_legacy_iterable(
            LineNumberLabel.from_atf(data["prefix"]),
            data["content"],
            data["line_number"],
        )


class ControlLineSchema(LineBaseSchema):
    @post_load
    def make_line(self, data, **kwargs):
        return ControlLine(data["prefix"], data["content"])


class EmptyLineSchema(LineBaseSchema):
    @post_load
    def make_line(self, data, **kwargs):
        return EmptyLine()


class NoteLineSchema(LineBaseSchema):
    parts = fields.Function(
        lambda line: dump_parts(line.parts), load_parts, required=True
    )

    @post_load
    def make_line(self, data, **kwargs):
        return NoteLine(data["parts"])
