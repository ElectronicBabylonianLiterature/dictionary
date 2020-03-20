from marshmallow import Schema, fields, post_load

from ebl.transliteration.application.one_of_line_schema import OneOfLineSchema
from ebl.transliteration.domain.atf import DEFAULT_ATF_PARSER_VERSION
from ebl.transliteration.domain.text import Text


class TextSchema(Schema):
    lines = fields.Nested(OneOfLineSchema, many=True, required=True)
    parser_version = fields.String(missing=DEFAULT_ATF_PARSER_VERSION)

    @post_load
    def make_text(self, data, **kwargs):
        return Text.of_iterable(data["lines"], data["parser_version"])
