import attr
import pytest  # pyre-ignore[21]

from ebl.corpus.application.text_serializer import serialize
from ebl.transliteration.domain.normalized_akkadian import AkkadianWord
from ebl.corpus.domain.text import Line, ManuscriptLine
from ebl.dictionary.domain.word import WordId
from ebl.errors import DataError, Defect, NotFoundError
from ebl.tests.factories.corpus import TextFactory
from ebl.transliteration.domain.alignment import (
    Alignment,
    AlignmentError,
    AlignmentToken,
)
from ebl.transliteration.domain.atf import ATF_PARSER_VERSION
from ebl.transliteration.domain.enclosure_tokens import BrokenAway
from ebl.transliteration.domain.line_number import LineNumber
from ebl.transliteration.domain.sign_tokens import Reading
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.tokens import Joiner, ValueToken
from ebl.transliteration.domain.word_tokens import Word
from ebl.users.domain.user import Guest
from ebl.transliteration.domain.lemmatization import LemmatizationToken

COLLECTION = "texts"
TEXT = TextFactory.build()  # pyre-ignore[16]
TEXT_WITHOUT_DOCUMENTS = attr.evolve(
    TEXT,
    chapters=tuple(
        attr.evolve(
            chapter,
            manuscripts=tuple(
                attr.evolve(
                    manuscript,
                    references=tuple(
                        attr.evolve(reference, document=None)
                        for reference in manuscript.references
                    ),
                )
                for manuscript in chapter.manuscripts
            ),
        )
        for chapter in TEXT.chapters
    ),
)
ANY_USER = Guest()


def expect_bibliography(bibliography, when):
    for chapter in TEXT.chapters:
        for manuscript in chapter.manuscripts:
            for reference in manuscript.references:
                (when(bibliography).find(reference.id).thenReturn(reference.document))


def expect_validate_references(bibliography, when, text=TEXT):
    manuscript_references = [
        manuscript.references
        for chapter in text.chapters
        for manuscript in chapter.manuscripts
    ]

    for references in manuscript_references:
        when(bibliography).validate_references(references).thenReturn()


def allow_validate_references(bibliography, when):
    when(bibliography).validate_references(...).thenReturn()


def expect_invalid_references(bibliography, when):
    when(bibliography).validate_references(...).thenRaise(DataError())


def expect_signs(signs, sign_repository):
    for sign in signs:
        sign_repository.create(sign)


def expect_text_update(
    bibliography,
    changelog,
    old_text,
    updated_text,
    signs,
    sign_repository,
    text_repository,
    user,
    when,
):
    expect_signs(signs, sign_repository)
    expect_validate_references(bibliography, when, old_text)
    when(text_repository).update(TEXT.id, updated_text).thenReturn(updated_text)
    when(changelog).create(
        COLLECTION,
        user.profile,
        {**serialize(old_text), "_id": old_text.id},
        {**serialize(updated_text), "_id": updated_text.id},
    ).thenReturn()


def expect_text_find_and_update(
    bibliography,
    changelog,
    old_text,
    updated_text,
    signs,
    sign_repository,
    text_repository,
    user,
    when,
):
    when(text_repository).find(TEXT.id).thenReturn(old_text)
    expect_text_update(
        bibliography,
        changelog,
        old_text,
        updated_text,
        signs,
        sign_repository,
        text_repository,
        user,
        when,
    )


def test_creating_text(
    corpus, text_repository, bibliography, changelog, signs, sign_repository, user, when
):
    expect_signs(signs, sign_repository)
    expect_validate_references(bibliography, when)
    when(changelog).create(
        COLLECTION, user.profile, {"_id": TEXT.id}, {**serialize(TEXT), "_id": TEXT.id}
    ).thenReturn()
    when(text_repository).create(TEXT).thenReturn()

    corpus.create(TEXT, user)


def test_create_raises_exception_if_invalid_signs(corpus, bibliography, when):
    allow_validate_references(bibliography, when)

    with pytest.raises(DataError):
        corpus.create(TEXT, ANY_USER)


def test_create_raises_exception_if_invalid_references(corpus, bibliography, when):
    expect_invalid_references(bibliography, when)

    with pytest.raises(DataError):
        corpus.create(TEXT, ANY_USER)


def test_finding_text(corpus, text_repository, bibliography, when):
    when(text_repository).find(TEXT.id).thenReturn(TEXT_WITHOUT_DOCUMENTS)
    expect_bibliography(bibliography, when)

    assert corpus.find(TEXT.id) == TEXT


def test_listing_texts(corpus, text_repository, when):
    when(text_repository).list().thenReturn([TEXT_WITHOUT_DOCUMENTS])

    assert corpus.list() == [TEXT_WITHOUT_DOCUMENTS]


def test_find_raises_exception_if_references_not_found(
    corpus, text_repository, bibliography, when
):
    when(text_repository).find(TEXT.id).thenReturn(TEXT_WITHOUT_DOCUMENTS)
    when(bibliography).find(...).thenRaise(NotFoundError())

    with pytest.raises(Defect):
        corpus.find(TEXT.id)


def test_updating_text(
    corpus, text_repository, bibliography, changelog, signs, sign_repository, user, when
):
    updated_text = attr.evolve(TEXT_WITHOUT_DOCUMENTS, name="New Name")
    expect_text_update(
        bibliography,
        changelog,
        TEXT_WITHOUT_DOCUMENTS,
        updated_text,
        signs,
        sign_repository,
        text_repository,
        user,
        when,
    )

    corpus.update_text(
        TEXT_WITHOUT_DOCUMENTS.id, TEXT_WITHOUT_DOCUMENTS, updated_text, user
    )


def test_updating_alignment(
    corpus, text_repository, bibliography, changelog, signs, sign_repository, user, when
):
    updated_text = attr.evolve(
        TEXT_WITHOUT_DOCUMENTS,
        chapters=(
            attr.evolve(
                TEXT_WITHOUT_DOCUMENTS.chapters[0],
                lines=(
                    attr.evolve(
                        TEXT_WITHOUT_DOCUMENTS.chapters[0].lines[0],
                        manuscripts=(
                            attr.evolve(
                                TEXT_WITHOUT_DOCUMENTS.chapters[0]
                                .lines[0]
                                .manuscripts[0],
                                line=TextLine.of_iterable(
                                    LineNumber(1),
                                    (
                                        Word.of(
                                            [
                                                Reading.of_name("ku"),
                                                Joiner.hyphen(),
                                                BrokenAway.open(),
                                                Reading.of_name("nu"),
                                                Joiner.hyphen(),
                                                Reading.of_name("ši"),
                                                BrokenAway.close(),
                                            ],
                                            alignment=0,
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                ),
            ),
        ),
    )
    expect_text_find_and_update(
        bibliography,
        changelog,
        TEXT_WITHOUT_DOCUMENTS,
        updated_text,
        signs,
        sign_repository,
        text_repository,
        user,
        when,
    )

    alignment = Alignment((((AlignmentToken("ku-[nu-ši]", 0),),),))
    corpus.update_alignment(TEXT.id, 0, alignment, user)


def test_updating_manuscript_lemmatization(
    corpus, text_repository, bibliography, changelog, signs, sign_repository, user, when
):
    updated_text = attr.evolve(
        TEXT_WITHOUT_DOCUMENTS,
        chapters=(
            attr.evolve(
                TEXT_WITHOUT_DOCUMENTS.chapters[0],
                lines=(
                    attr.evolve(
                        TEXT_WITHOUT_DOCUMENTS.chapters[0].lines[0],
                        manuscripts=(
                            attr.evolve(
                                TEXT_WITHOUT_DOCUMENTS.chapters[0]
                                .lines[0]
                                .manuscripts[0],
                                line=TextLine.of_iterable(
                                    LineNumber(1),
                                    (
                                        Word.of(
                                            [
                                                Reading.of_name("ku"),
                                                Joiner.hyphen(),
                                                BrokenAway.open(),
                                                Reading.of_name("nu"),
                                                Joiner.hyphen(),
                                                Reading.of_name("ši"),
                                                BrokenAway.close(),
                                            ],
                                            unique_lemma=("aklu I",),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                ),
            ),
        ),
    )
    expect_text_find_and_update(
        bibliography,
        changelog,
        TEXT_WITHOUT_DOCUMENTS,
        updated_text,
        signs,
        sign_repository,
        text_repository,
        user,
        when,
    )

    lemmatization = (((LemmatizationToken("ku-[nu-ši]", ("aklu I",)),),),)
    corpus.update_manuscript_lemmatization(TEXT.id, 0, lemmatization, user)


@pytest.mark.parametrize(
    "alignment",
    [
        Alignment(
            (((AlignmentToken("ku-[nu-ši]", 0), AlignmentToken("ku-[nu-ši]", 0)),),)
        ),
        Alignment(((tuple(),),)),
        Alignment(
            (((AlignmentToken("ku-[nu-ši]", 0),), (AlignmentToken("ku-[nu-ši]", 0),)),)
        ),
        Alignment((tuple())),
        Alignment(
            (
                ((AlignmentToken("ku-[nu-ši]", 0),),),
                ((AlignmentToken("ku-[nu-ši]", 0),),),
            )
        ),
        Alignment(tuple()),
        Alignment((((AlignmentToken("invalid value", 0),),),)),
    ],
)
def test_invalid_alignment(alignment, corpus, text_repository, when):
    when(text_repository).find(TEXT.id).thenReturn(TEXT_WITHOUT_DOCUMENTS)
    with pytest.raises(AlignmentError):
        corpus.update_alignment(TEXT.id, 0, alignment, ANY_USER)


def test_updating_manuscripts(
    corpus, text_repository, bibliography, changelog, signs, sign_repository, user, when
):
    updated_text = attr.evolve(
        TEXT_WITHOUT_DOCUMENTS,
        chapters=(
            attr.evolve(
                TEXT_WITHOUT_DOCUMENTS.chapters[0],
                manuscripts=(
                    attr.evolve(
                        TEXT_WITHOUT_DOCUMENTS.chapters[0].manuscripts[0],
                        notes="Updated manuscript.",
                    ),
                ),
            ),
        ),
    )
    expect_text_find_and_update(
        bibliography,
        changelog,
        TEXT_WITHOUT_DOCUMENTS,
        updated_text,
        signs,
        sign_repository,
        text_repository,
        user,
        when,
    )

    manuscripts = (updated_text.chapters[0].manuscripts[0],)
    corpus.update_manuscripts(TEXT.id, 0, manuscripts, user)


@pytest.mark.parametrize(
    "manuscripts",
    [
        tuple(),
        (
            TEXT_WITHOUT_DOCUMENTS.chapters[0].manuscripts[0],
            TEXT_WITHOUT_DOCUMENTS.chapters[0].manuscripts[0],
        ),
    ],
)
def test_invalid_manuscripts(manuscripts, corpus, text_repository, when):
    when(text_repository).find(TEXT.id).thenReturn(TEXT_WITHOUT_DOCUMENTS)
    with pytest.raises(DataError):
        corpus.update_manuscripts(TEXT.id, 0, manuscripts, ANY_USER)


def test_update_manuscripts_raises_exception_if_invalid_references(
    corpus, text_repository, bibliography, when
):
    manuscripts = TEXT.chapters[0].manuscripts
    when(text_repository).find(TEXT.id).thenReturn(TEXT_WITHOUT_DOCUMENTS)
    expect_invalid_references(bibliography, when)

    with pytest.raises(DataError):
        corpus.update_manuscripts(TEXT.id, 0, manuscripts, ANY_USER)


def test_updating_lines(
    corpus, text_repository, bibliography, changelog, signs, sign_repository, user, when
):
    updated_text = attr.evolve(
        TEXT_WITHOUT_DOCUMENTS,
        chapters=(
            attr.evolve(
                TEXT_WITHOUT_DOCUMENTS.chapters[0],
                lines=(
                    attr.evolve(
                        TEXT_WITHOUT_DOCUMENTS.chapters[0].lines[0],
                        text=attr.evolve(
                            TEXT_WITHOUT_DOCUMENTS.chapters[0].lines[0].text,
                            line_number=LineNumber(1, True),
                        ),
                    ),
                ),
                parser_version=ATF_PARSER_VERSION,
            ),
        ),
    )
    expect_text_find_and_update(
        bibliography,
        changelog,
        TEXT_WITHOUT_DOCUMENTS,
        updated_text,
        signs,
        sign_repository,
        text_repository,
        user,
        when,
    )

    lines = updated_text.chapters[0].lines
    corpus.update_lines(TEXT.id, 0, lines, user)


def test_merging_lines(
    corpus, text_repository, bibliography, changelog, signs, sign_repository, user, when
):
    reconstruction = TextLine.of_iterable(
        LineNumber(1), (AkkadianWord.of((ValueToken.of("buāru"),)),)
    )
    is_second_line_of_parallelism = False
    is_beginning_of_section = False
    text_line = TextLine.of_iterable(
        LineNumber(1),
        (
            Word.of(
                [Reading.of_name("ku")], unique_lemma=(WordId("word1"),), alignment=0
            ),
            Word.of(
                [Reading.of_name("nu")], unique_lemma=(WordId("word2"),), alignment=1
            ),
        ),
    )
    manuscript_id = TEXT_WITHOUT_DOCUMENTS.chapters[0].manuscripts[0].id
    line = Line(
        reconstruction,
        None,
        not is_second_line_of_parallelism,
        not is_beginning_of_section,
        (ManuscriptLine(manuscript_id, tuple(), text_line),),
    )
    new_text_line = TextLine.of_iterable(
        LineNumber(1),
        (Word.of([Reading.of_name("ku")]), Word.of([Reading.of_name("ši")])),
    )
    new_line = Line(
        reconstruction,
        None,
        is_second_line_of_parallelism,
        is_beginning_of_section,
        (ManuscriptLine(manuscript_id, tuple(), text_line.merge(new_text_line)),),
    )
    dehydrated_text = attr.evolve(
        TEXT_WITHOUT_DOCUMENTS,
        chapters=(attr.evolve(TEXT_WITHOUT_DOCUMENTS.chapters[0], lines=(line,)),),
    )
    updated_text = attr.evolve(
        TEXT_WITHOUT_DOCUMENTS,
        chapters=(
            attr.evolve(
                TEXT_WITHOUT_DOCUMENTS.chapters[0],
                lines=(new_line,),
                parser_version=ATF_PARSER_VERSION,
            ),
        ),
    )
    expect_text_find_and_update(
        bibliography,
        changelog,
        dehydrated_text,
        updated_text,
        signs,
        sign_repository,
        text_repository,
        user,
        when,
    )

    lines = (
        Line(
            reconstruction,
            None,
            is_second_line_of_parallelism,
            is_beginning_of_section,
            (ManuscriptLine(manuscript_id, tuple(), new_text_line),),
        ),
    )
    corpus.update_lines(TEXT.id, 0, lines, user)


def test_update_lines_raises_exception_if_invalid_signs(
    corpus, text_repository, bibliography, when
):
    lines = TEXT.chapters[0].lines
    when(text_repository).find(TEXT.id).thenReturn(TEXT_WITHOUT_DOCUMENTS)
    allow_validate_references(bibliography, when)

    with pytest.raises(DataError):
        corpus.update_lines(TEXT.id, 0, lines, ANY_USER)
