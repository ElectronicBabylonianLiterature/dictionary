import falcon
import pytest


@pytest.mark.parametrize(
    "params, expected",
    [
        (
            {"listsName": "ABZ", "listsNumber": "377n1"},
            [
                {
                    "lists": [{"name": "ABZ", "number": "377n1"}],
                    "logograms": [],
                    "mesZl": "",
                    "name": "P₂",
                    "unicode": [],
                    "values": [{"subIndex": 1, "value": ":"}],
                }
            ],
        ),
        (
            {"value": ":", "subIndex": "1"},
            [
                {
                    "lists": [{"name": "ABZ", "number": "377n1"}],
                    "logograms": [],
                    "mesZl": "",
                    "name": "P₂",
                    "unicode": [],
                    "values": [{"subIndex": 1, "value": ":"}],
                }
            ],
        ),
        (
            {"value": "bu", "isIncludeHomophones": "true", "subIndex": "1"},
            [
                {
                    "lists": [{"name": "ABZ", "number": "377n1"}],
                    "logograms": [],
                    "mesZl": "",
                    "name": "P₂",
                    "unicode": [],
                    "values": [{"subIndex": 1, "value": ":"}],
                }
            ],
        ),
        (
            {"value": "ku", "subIndex": "1", "isComposite": "true"},
            [
                {
                    "lists": [{"name": "ABZ", "number": "377n1"}],
                    "logograms": [],
                    "mesZl": "",
                    "name": "P₂",
                    "unicode": [],
                    "values": [{"subIndex": 1, "value": ":"}],
                }
            ],
        ),
    ],
)
def test_signs_route(params, expected, client, sign_repository, signs):
    for sign in signs:
        sign_repository.create(sign)
    get_result = client.simulate_get("/signs", params=params)
    assert get_result.status == falcon.HTTP_OK
    assert get_result.headers["Access-Control-Allow-Origin"] == "*"
    assert get_result.json == expected


def test_signs_route_error(client, sign_repository, signs):
    for sign in signs:
        sign_repository.create(sign)
    get_result = client.simulate_get("/signs", params={"signs": "P₂"})
    assert get_result.status == falcon.HTTP_UNPROCESSABLE_ENTITY
    assert get_result.headers["Access-Control-Allow-Origin"] == "*"