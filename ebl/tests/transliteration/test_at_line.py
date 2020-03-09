import pytest

from ebl.transliteration.domain import atf
from ebl.transliteration.domain.at_line import (
    DiscourseAtLine,
    SurfaceAtLine,
    ColumnAtLine,
    ObjectAtLine,
    CompositeAtLine,
    HeadingAtLine,
)
from ebl.transliteration.domain.labels import SurfaceLabel, ColumnLabel
from ebl.transliteration.domain.tokens import ValueToken


def test_at_line_heading():
    at_line = HeadingAtLine(1)

    assert at_line.prefix == "@"
    assert at_line.content == (ValueToken("h1"),)


def test_at_line_column():
    at_line = ColumnAtLine(ColumnLabel.from_int(1, (atf.Status.COLLATION,)))

    assert at_line.prefix == "@"
    assert at_line.content == (ValueToken("column 1*"),)


def test_at_line_column_no_status():
    at_line = ColumnAtLine(ColumnLabel.from_int(1))

    assert at_line.prefix == "@"
    assert at_line.content == (ValueToken("column 1"),)


def test_at_line_discourse():
    at_line = DiscourseAtLine(atf.Discourse.SIGNATURES)

    assert at_line.prefix == "@"
    assert at_line.content == (ValueToken("signatures"),)
    assert at_line.discourse_label == atf.Discourse.SIGNATURES


def test_at_line_surface():

    at_line = SurfaceAtLine(
        SurfaceLabel((atf.Status.CORRECTION,), atf.Surface.SURFACE, "Stone wig")
    )

    assert at_line.prefix == "@"
    assert at_line.content == (ValueToken("surface Stone wig!"),)
    assert at_line.surface_label == SurfaceLabel(
        (atf.Status.CORRECTION,), atf.Surface.SURFACE, "Stone wig"
    )


def test_at_line_surface_no_status():

    at_line = SurfaceAtLine(SurfaceLabel([], atf.Surface.SURFACE, "Stone wig"))

    assert at_line.prefix == "@"
    assert at_line.content == (ValueToken("surface Stone wig"),)
    assert at_line.surface_label == SurfaceLabel([], atf.Surface.SURFACE, "Stone wig")


def test_at_line_surface_instantiate_text_with_wrong_surface():

    with pytest.raises(ValueError):
        at_line = SurfaceAtLine(
            SurfaceLabel((atf.Status.CORRECTION,), atf.Surface.OBVERSE, "Stone wig")
        )
        assert at_line.prefix == "@"
        assert at_line.content == (ValueToken("obverse Stone wig!"),)
        assert at_line.surface_label == SurfaceLabel(
            (atf.Status.CORRECTION,), atf.Surface.OBVERSE, "Stone wig"
        )


def test_at_line_object_no_status():
    at_line = ObjectAtLine([], atf.Object.OBJECT, "Stone wig")

    assert at_line.prefix == "@"
    assert at_line.content == (ValueToken("object Stone wig"),)
    assert at_line.object_label == atf.Object.OBJECT
    assert at_line.status == []
    assert at_line.text == "Stone wig"


def test_at_line_object():
    at_line = ObjectAtLine([atf.Status.CORRECTION], atf.Object.OBJECT, "Stone wig")

    assert at_line.prefix == "@"
    assert at_line.content == (ValueToken("object Stone wig!"),)
    assert at_line.object_label == atf.Object.OBJECT
    assert at_line.status == [atf.Status.CORRECTION]
    assert at_line.text == "Stone wig"


def test_at_line_composite():
    at_line = CompositeAtLine(atf.Composite.DIV, "paragraph", 1)

    assert at_line.prefix == "@"
    assert at_line.content == (ValueToken("div paragraph 1"),)
    assert at_line.composite == atf.Composite.DIV
    assert at_line.text == "paragraph"
    assert at_line.number == 1


def test_at_line_composite_raise_error():
    with pytest.raises(ValueError):
        CompositeAtLine(atf.Composite.END, "paragraph", 1)