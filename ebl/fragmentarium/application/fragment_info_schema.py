from marshmallow import Schema, fields, post_load  # pyre-ignore

from ebl.bibliography.application.reference_schema import ReferenceSchema, \
    ApiReferenceSchema
from ebl.fragmentarium.domain.fragment_info import FragmentInfo
from ebl.fragmentarium.application.museum_number_schema import MuseumNumberSchema


class FragmentInfoSchema(Schema):  # pyre-ignore[11]
    number = fields.Nested(MuseumNumberSchema, required=True, data_key="museumNumber")
    accession = fields.String(required=True)
    script = fields.String(required=True)
    description = fields.String(required=True)
    editor = fields.String(missing="")
    edition_date = fields.String(data_key="editionDate", missing="")
    matching_lines = fields.List(
        fields.List(fields.String()), data_key="matchingLines", missing=tuple()
    )
    references = fields.Nested(ReferenceSchema, many=True, missing=tuple())

    @post_load
    def make_fragment_info(self, data, **kwargs):
        data["matching_lines"] = tuple(map(tuple, data["matching_lines"]))
        return FragmentInfo(**data)


class ApiFragmentInfoSchema(FragmentInfoSchema):
    number = fields.String(dump_only=True)
    references = fields.Nested(ApiReferenceSchema, many=True, required=True)
