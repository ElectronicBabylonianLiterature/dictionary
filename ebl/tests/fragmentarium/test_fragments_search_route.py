import falcon  # pyre-ignore

from ebl.fragmentarium.application.fragment_info_schema import FragmentInfoSchema
from ebl.fragmentarium.domain.fragment_info import FragmentInfo
from ebl.tests.factories.bibliography import ReferenceFactory
from ebl.tests.factories.fragment import (
    FragmentFactory,
    InterestingFragmentFactory,
    TransliteratedFragmentFactory,
)


def expected_fragment_info_dto(fragment, lines=tuple()):
    return FragmentInfoSchema().dump(FragmentInfo.of(fragment, lines))


def test_search_fragment(client, fragmentarium):
    fragment = FragmentFactory.build()
    fragment_number = fragmentarium.create(fragment)
    result = client.simulate_get(f"/fragments", params={"number": fragment_number})

    assert result.status == falcon.HTTP_OK
    assert result.json == [expected_fragment_info_dto(fragment)]
    assert result.headers["Access-Control-Allow-Origin"] == "*"
    assert "Cache-Control" not in result.headers


def test_search_fragment_not_found(client):
    result = client.simulate_get(f"/fragments", params={"number": "K.1"})

    assert result.json == []


def test_search_references(client, fragmentarium, bibliography, bibliography_entry, user):
    bib_1 = bibliography_entry['pages'] = "254"
    fragment = FragmentFactory.build(
        references=(ReferenceFactory.build(id=bibliography_entry['id'], pages="254"), ReferenceFactory.build(id='RN.0'))
    )
    fragmentarium.create(fragment)
    bibliography.create(bibliography_entry, user)
    bib_2 = bibliography_entry['id'] = 'RN.0'
    bibliography.create(bibliography_entry, user)
    reference_id = fragment.references[0].id
    reference_pages = fragment.references[0].pages
    result = client.simulate_get(f"/fragments", params={
        "id": reference_id, "pages": reference_pages
    })

    assert result.status == falcon.HTTP_OK
    assert result.json == {fragment.number:[bibliography_entry]}
    assert result.headers["Access-Control-Allow-Origin"] == "*"
    assert "Cache-Control" not in result.headers


def test_search_references_invalid_query(client, fragmentarium):
    fragment = FragmentFactory.build(
        references=(ReferenceFactory.build(), ReferenceFactory.build())
    )
    fragmentarium.create(fragment)
    reference_id = fragment.references[0].id
    reference_pages = "should be a number"
    result = client.simulate_get(f"/fragments", params={
        "id": reference_id, "pages": reference_pages
    })

    assert result.status == falcon.HTTP_UNPROCESSABLE_ENTITY


def test_search_signs(client, fragmentarium, sign_repository, signs):
    transliterated_fragment = TransliteratedFragmentFactory.build()
    fragmentarium.create(transliterated_fragment)
    for sign in signs:
        sign_repository.create(sign)

    result = client.simulate_get(f"/fragments", params={"transliteration": "ma-tu₂"})

    assert result.status == falcon.HTTP_OK
    assert result.json == [
        expected_fragment_info_dto(
            transliterated_fragment, (("6'. [...] x# mu ta-ma;-tu₂",),)
        )
    ]
    assert result.headers["Access-Control-Allow-Origin"] == "*"
    assert "Cache-Control" not in result.headers


def test_random(client, fragmentarium):
    transliterated_fragment = TransliteratedFragmentFactory.build()
    fragmentarium.create(transliterated_fragment)

    result = client.simulate_get(f"/fragments", params={"random": True})

    assert result.status == falcon.HTTP_OK
    assert result.json == [expected_fragment_info_dto(transliterated_fragment)]
    assert result.headers["Access-Control-Allow-Origin"] == "*"
    assert "Cache-Control" not in result.headers


def test_interesting(client, fragmentarium):
    interesting_fragment = InterestingFragmentFactory.build()
    fragmentarium.create(interesting_fragment)

    result = client.simulate_get(f"/fragments", params={"interesting": True})

    assert result.status == falcon.HTTP_OK
    assert result.json == [expected_fragment_info_dto(interesting_fragment)]
    assert result.headers["Access-Control-Allow-Origin"] == "*"
    assert "Cache-Control" not in result.headers


def test_latest(client, fragmentarium):
    transliterated_fragment = TransliteratedFragmentFactory.build()
    fragmentarium.create(transliterated_fragment)

    result = client.simulate_get(f"/fragments", params={"latest": True})

    assert result.status == falcon.HTTP_OK
    assert result.json == [expected_fragment_info_dto(transliterated_fragment)]
    assert result.headers["Access-Control-Allow-Origin"] == "*"
    assert result.headers["Cache-Control"] == "private, max-age=600"


def test_needs_revision(client, fragmentarium):
    transliterated_fragment = TransliteratedFragmentFactory.build()
    fragmentarium.create(transliterated_fragment)

    result = client.simulate_get(f"/fragments", params={"needsRevision": True})

    assert result.status == falcon.HTTP_OK
    assert result.json == [expected_fragment_info_dto(transliterated_fragment)]
    assert result.headers["Access-Control-Allow-Origin"] == "*"
    assert result.headers["Cache-Control"] == "private, max-age=600"


def test_search_fragment_no_query(client):
    result = client.simulate_get(f"/fragments")

    assert result.status == falcon.HTTP_UNPROCESSABLE_ENTITY


def test_search_too_many_params(client):
    params = {"random": True, "interesting": True, "page": "25"}
    result = client.simulate_get(f"/fragments", params=params)

    assert result.status == falcon.HTTP_UNPROCESSABLE_ENTITY


def test_search_invalid_param(client):
    params = {"this_param": "is wrong"}
    result = client.simulate_get(f"/fragments", params=params)

    assert result.status == falcon.HTTP_UNPROCESSABLE_ENTITY
