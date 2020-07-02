from marshmallow import fields, post_load  # pyre-ignore[21]

from ebl.schemas import NameEnum
from ebl.transliteration.application.label_schemas import (ColumnLabelSchema,
                                                           ObjectLabelSchema,
                                                           SurfaceLabelSchema)
from ebl.transliteration.application.line_schemas import LineBaseSchema
from ebl.transliteration.domain import atf
from ebl.transliteration.domain.at_line import (ColumnAtLine, CompositeAtLine,
                                                DiscourseAtLine,
                                                DivisionAtLine, HeadingAtLine,
                                                ObjectAtLine, SealAtLine,
                                                SurfaceAtLine)
from ebl.transliteration.domain.labels import ObjectLabel


class SealAtLineSchema(LineBaseSchema):
    number = fields.Int(required=True)
    display_value = fields.String(data_key="displayValue")

    @post_load
    def make_line(self, data, **kwargs) -> SealAtLine:
        return SealAtLine(data["number"])


class HeadingAtLineSchema(LineBaseSchema):
    number = fields.Int(required=True)
    display_value = fields.String(data_key="displayValue")

    @post_load
    def make_line(self, data, **kwargs) -> HeadingAtLine:
        return HeadingAtLine(data["number"])


class ColumnAtLineSchema(LineBaseSchema):
    column_label = fields.Nested(
        ColumnLabelSchema, required=True
    )
    display_value = fields.String(data_key="displayValue")

    @post_load
    def make_line(self, data, **kwargs) -> ColumnAtLine:
        return ColumnAtLine(data["column_label"])


class DiscourseAtLineSchema(LineBaseSchema):
    discourse_label = NameEnum(atf.Discourse, required=True)
    display_value = fields.String(data_key="displayValue")

    @post_load
    def make_line(self, data, **kwargs) -> DiscourseAtLine:
        return DiscourseAtLine(data["discourse_label"])


class SurfaceAtLineSchema(LineBaseSchema):
    surface_label = fields.Nested(
        SurfaceLabelSchema, required=True
    )
    display_value = fields.String(data_key="displayValue")

    @post_load
    def make_line(self, data, **kwargs) -> SurfaceAtLine:
        return SurfaceAtLine(data["surface_label"])


class ObjectAtLineSchema(LineBaseSchema):
    status = fields.List(NameEnum(atf.Status), load_only=True)
    object_label = NameEnum(atf.Object, load_only=True)
    text = fields.String(default="", load_only=True)
    label = fields.Nested(ObjectLabelSchema)
    display_value = fields.String(data_key="displayValue")

    @post_load
    def make_line(self, data, **kwargs) -> ObjectAtLine:
        return (
            ObjectAtLine(data["label"])
            if "label" in data
            else ObjectAtLine(ObjectLabel(data["status"], data["object_label"], data["text"]))
        )


class DivisionAtLineSchema(LineBaseSchema):
    text = fields.String(required=True)
    number = fields.Int(required=False, allow_none=True, default=None)
    display_value = fields.String(data_key="displayValue")

    @post_load
    def make_line(self, data, **kwargs) -> DivisionAtLine:
        return DivisionAtLine(data["text"], data["number"])


class CompositeAtLineSchema(LineBaseSchema):
    composite = NameEnum(atf.Composite, required=True)
    text = fields.String(required=True)
    number = fields.Int(required=False, allow_none=True, default=None)
    display_value = fields.String(data_key="displayValue")

    @post_load
    def make_line(self, data, **kwargs) -> CompositeAtLine:
        return CompositeAtLine(data["composite"], data["text"], data["number"])
