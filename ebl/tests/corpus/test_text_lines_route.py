import json

import attr
import falcon
import pytest

from ebl.auth0 import Guest
from ebl.corpus.api_serializer import serialize
from ebl.tests.factories.corpus import TextFactory
from ebl.text.labels import LineNumberLabel

ANY_USER = Guest()


def create_dto(text, include_documents=False):
    return serialize(text, include_documents)


def allow_references(text, bibliography):
    for chapter in text.chapters:
        for manuscript in chapter.manuscripts:
            for reference in manuscript.references:
                bibliography.create(reference.document, ANY_USER)


def allow_signs(signs, sign_list):
    for sign in signs:
        sign_list.create(sign)


def create_text(client, text):
    post_result = client.simulate_post(
        f'/texts',
        body=json.dumps(create_dto(text))
    )
    assert post_result.status == falcon.HTTP_CREATED
    assert post_result.headers['Location'] == \
        f'/texts/{text.category}/{text.index}'
    assert post_result.headers['Access-Control-Allow-Origin'] == '*'
    assert post_result.json == create_dto(text, True)


def test_updating(client, bibliography, sign_list, signs):
    allow_signs(signs, sign_list)
    text = TextFactory.build()
    allow_references(text, bibliography)
    create_text(client, text)
    updated_text = attr.evolve(text, chapters=(
        attr.evolve(text.chapters[0], lines=(
            attr.evolve(text.chapters[0].lines[0],
                        number=LineNumberLabel.from_atf("1'.")),
        )),
    ))

    body = {
        'lines': create_dto(
            updated_text
        )['chapters'][0]['lines']
    }
    post_result = client.simulate_post(
        f'/texts/{text.category}/{text.index}/chapters/0/lines',
        body=json.dumps(body)
    )

    assert post_result.status == falcon.HTTP_OK
    assert post_result.headers['Access-Control-Allow-Origin'] == '*'
    assert post_result.json == create_dto(updated_text, True)

    get_result = client.simulate_get(
        f'/texts/{updated_text.category}/{updated_text.index}'
    )

    assert get_result.status == falcon.HTTP_OK
    assert get_result.headers['Access-Control-Allow-Origin'] == '*'
    assert get_result.json == create_dto(updated_text, True)


def test_updating_text_not_found(client, bibliography):
    post_result = client.simulate_post(
        f'/texts/1/1/chapters/0/lines',
        body=json.dumps({'lines': []})
    )

    assert post_result.status == falcon.HTTP_NOT_FOUND


def test_updating_text_category(client):
    post_result = client.simulate_post(
        f'/texts/invalid/1/chapters/0/lines',
        body=json.dumps({'lines': []})
    )

    assert post_result.status == falcon.HTTP_NOT_FOUND


def test_updating_invalid_id(client):
    post_result = client.simulate_post(
        f'/texts/1/invalid/chapters/0/lines',
        body=json.dumps({'lines': []})
    )

    assert post_result.status == falcon.HTTP_NOT_FOUND


def test_updating_invalid_chapter_index(client):
    post_result = client.simulate_post(
        f'/texts/1/1/chapters/invalid/lines',
        body=json.dumps({'lines': []})
    )

    assert post_result.status == falcon.HTTP_NOT_FOUND


@pytest.mark.parametrize('lines,expected_status', [
    [[{}], falcon.HTTP_BAD_REQUEST]
])
def test_update_invalid_entity(client,
                               bibliography,
                               lines,
                               expected_status,
                               sign_list,
                               signs):
    allow_signs(signs, sign_list)
    text = TextFactory.build()
    allow_references(text, bibliography)
    create_text(client, text)

    post_result = client.simulate_post(
        f'/texts/{text.category}/{text.index}/chapters/0/lines',
        body=json.dumps({'lines': lines})
    )

    assert post_result.status == expected_status