import json

import attr
import falcon  # pyre-ignore[21]
import pytest  # pyre-ignore[21]

from ebl.corpus.web.api_serializer import serialize
from ebl.tests.factories.corpus import TextFactory
from ebl.transliteration.domain.enclosure_tokens import BrokenAway
from ebl.transliteration.domain.line_number import LineNumber
from ebl.transliteration.domain.sign_tokens import Reading
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.tokens import Joiner
from ebl.transliteration.domain.word_tokens import Word
from ebl.users.domain.user import Guest

ANY_USER = Guest()
DTO = {"lemmatization": [[[{"value": "ku-[nu-ši]", "uniqueLemma": ["aklu I"]}]]]}


def create_text_dto(text):
    return serialize(text)


def allow_references(text, bibliography):
    for chapter in text.chapters:
        for manuscript in chapter.manuscripts:
            for reference in manuscript.references:
                bibliography.create(reference.document, ANY_USER)


def allow_signs(signs, sign_list):
    for sign in signs:
        sign_list.create(sign)


def create_text(client, text):
    post_result = client.simulate_post("/texts", body=json.dumps(create_text_dto(text)))
    assert post_result.status == falcon.HTTP_CREATED


def test_updating_lemmatization(client, bibliography, sign_repository, signs):
    allow_signs(signs, sign_repository)
    text = TextFactory.build()
    allow_references(text, bibliography)
    create_text(client, text)
    chapter_index = 0
    updated_text = attr.evolve(
        text,
        chapters=(
            attr.evolve(
                text.chapters[chapter_index],
                lines=(
                    attr.evolve(
                        text.chapters[0].lines[0],
                        manuscripts=(
                            attr.evolve(
                                text.chapters[0].lines[0].manuscripts[0],
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
                                            unique_lemma=["aklu I"],
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

    expected_text = create_text_dto(updated_text)

    post_result = client.simulate_post(
        f"/texts/{text.category}/{text.index}"
        f"/chapters/{chapter_index}/manuscriptLemmatization",
        body=json.dumps(DTO),
    )

    assert post_result.status == falcon.HTTP_OK
    assert post_result.headers["Access-Control-Allow-Origin"] == "*"
    assert post_result.json == expected_text

    get_result = client.simulate_get(f"/texts/{text.category}/{text.index}")

    assert get_result.status == falcon.HTTP_OK
    assert get_result.json == expected_text


def test_updating_invalid_chapter(client, bibliography, sign_repository, signs):
    allow_signs(signs, sign_repository)
    text = TextFactory.build()
    allow_references(text, bibliography)
    create_text(client, text)

    post_result = client.simulate_post(
        f"/texts/{text.category}/{text.index}" f"/chapters/1/manuscriptLemmatization",
        body=json.dumps(DTO),
    )

    assert post_result.status == falcon.HTTP_NOT_FOUND


@pytest.mark.parametrize(
    "dto,expected_status",
    [
        ({"lemmatization": [[[]]]}, falcon.HTTP_UNPROCESSABLE_ENTITY),
        ({}, falcon.HTTP_BAD_REQUEST),
    ],
)
def test_updating_invalid_lemmatization(
    dto, expected_status, client, bibliography, sign_repository, signs
):
    allow_signs(signs, sign_repository)
    text = TextFactory.build()
    allow_references(text, bibliography)
    create_text(client, text)

    post_result = client.simulate_post(
        f"/texts/{text.category}/{text.index}" f"/chapters/0/manuscriptLemmatization",
        body=json.dumps(dto),
    )

    assert post_result.status == expected_status