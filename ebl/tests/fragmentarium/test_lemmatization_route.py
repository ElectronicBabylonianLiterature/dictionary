import json

import falcon  # pyre-ignore
import pytest  # pyre-ignore

from ebl.fragmentarium.web.dtos import create_response_dto
from ebl.tests.factories.fragment import (
    FragmentFactory,
    TransliteratedFragmentFactory,
)
from ebl.transliteration.domain.lemmatization import Lemmatization
from ebl.fragmentarium.domain.museum_number import MuseumNumber


def test_update_lemmatization(client, fragmentarium, user, database):
    transliterated_fragment = TransliteratedFragmentFactory.build()
    fragmentarium.create(transliterated_fragment)
    tokens = transliterated_fragment.text.lemmatization.to_list()
    tokens[1][3]["uniqueLemma"] = ["aklu I"]
    body = json.dumps({"lemmatization": tokens})
    url = f"/fragments/{transliterated_fragment.number}/lemmatization"
    post_result = client.simulate_post(url, body=body)

    expected_json = create_response_dto(
        transliterated_fragment.update_lemmatization(Lemmatization.from_list(tokens)),
        user,
        transliterated_fragment.number == MuseumNumber("K", "1"),
    )

    assert post_result.status == falcon.HTTP_OK
    assert post_result.headers["Access-Control-Allow-Origin"] == "*"
    assert post_result.json == expected_json

    get_result = client.simulate_get(f"/fragments/{transliterated_fragment.number}")
    assert get_result.json == expected_json

    assert database["changelog"].find_one(
        {
            "resource_id": str(transliterated_fragment.number),
            "resource_type": "fragments",
            "user_profile.name": user.profile["name"],
        }
    )


def test_update_lemmatization_not_found(client):
    url = "/fragments/unknown.fragment/lemmatization"
    body = json.dumps({"lemmatization": []})
    post_result = client.simulate_post(url, body=body)

    assert post_result.status == falcon.HTTP_NOT_FOUND


def test_update_lemmatization_invalid_number(client):
    url = "/fragments/invalid/lemmatization"
    body = json.dumps({"lemmatization": []})
    post_result = client.simulate_post(url, body=body)

    assert post_result.status == falcon.HTTP_UNPROCESSABLE_ENTITY


@pytest.mark.parametrize(
    "body",
    [
        "lemmatization",
        '"lemmatization"',
        json.dumps([[{"value": "u₄-šu", "uniqueLemma": []}]]),
        json.dumps({"lemmatization": [{"value": "u₄-šu", "uniqueLemma": []}]}),
        json.dumps({"lemmatization": [["u₄-šu"]]}),
        json.dumps({"lemmatization": [[{"value": 1, "uniqueLemma": []}]]}),
        json.dumps({"lemmatization": [[{"value": "u₄-šu", "uniqueLemma": 1}]]}),
        json.dumps({"lemmatization": [[{"value": "u₄-šu", "uniqueLemma": [1]}]]}),
        json.dumps({"lemmatization": [[{"value": None, "uniqueLemma": []}]]}),
    ],
)
def test_update_lemmatization_invalid_entity(client, fragmentarium, body):
    fragment = FragmentFactory.build()
    fragmentarium.create(fragment)
    url = f"/fragments/{fragment.number}/lemmatization"

    post_result = client.simulate_post(url, body=body)

    assert post_result.status == falcon.HTTP_BAD_REQUEST


def test_update_lemmatization_atf_change(client, fragmentarium):
    transliterated_fragment = TransliteratedFragmentFactory.build()
    fragmentarium.create(transliterated_fragment)
    tokens = transliterated_fragment.text.lemmatization.to_list()
    tokens[0][0]["value"] = "ana"
    body = json.dumps({"lemmatization": tokens})
    url = f"/fragments/{transliterated_fragment.number}/lemmatization"
    post_result = client.simulate_post(url, body=body)

    assert post_result.status == falcon.HTTP_UNPROCESSABLE_ENTITY
