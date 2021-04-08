import re
from typing import Optional, cast, Sequence

from marshmallow import EXCLUDE, Schema, fields, post_dump, post_load
from pymongo.database import Database

from ebl.errors import NotFoundError
from ebl.mongo_collection import MongoCollection
from ebl.transliteration.application.sign_repository import SignRepository
from ebl.transliteration.domain.sign import (
    Sign,
    SignListRecord,
    SignName,
    Value,
    Logogram,
)

COLLECTION = "signs"


class SignListRecordSchema(Schema):
    name = fields.String(required=True)
    number = fields.String(required=True)

    @post_load
    def make_sign_list_record(self, data, **kwargs):
        return SignListRecord(**data)


class ValueSchema(Schema):
    value = fields.String(required=True)
    sub_index = fields.Int(missing=None, data_key="subIndex")

    @post_load
    def make_value(self, data, **kwargs):
        return Value(**data)

    @post_dump
    def filter_none(self, data, **kwargs):
        return {key: value for key, value in data.items() if value is not None}


class LogogramSchema(Schema):
    logogram = fields.String(required=True)
    atf = fields.String(required=True)
    word_id = fields.List(fields.String(), required=True, data_key="wordId")
    schramm_logogramme = fields.String(required=True, data_key="schrammLogogramme")

    @post_load
    def make_logogram(self, data, **kwargs) -> Logogram:
        data["word_id"] = tuple(data["word_id"])
        return Logogram(**data)


class SignSchema(Schema):
    name = fields.String(required=True, data_key="_id")
    lists = fields.Nested(SignListRecordSchema, many=True, required=True)
    values = fields.Nested(ValueSchema, many=True, required=True, unknown=EXCLUDE)
    logograms = fields.Nested(LogogramSchema, many=True, missing=tuple())
    mes_zl = fields.String(data_key="mesZl", missing=None)

    @post_load
    def make_sign(self, data, **kwargs) -> Sign:
        data["lists"] = tuple(data["lists"])
        data["values"] = tuple(data["values"])
        data["logograms"] = tuple(data["logograms"])
        return Sign(**data)


class MongoSignRepository(SignRepository):
    def __init__(self, database: Database):
        self._collection = MongoCollection(database, COLLECTION)

    def create(self, sign: Sign) -> str:
        return self._collection.insert_one(SignSchema().dump(sign))

    def find(self, name: SignName) -> Sign:
        data = self._collection.find_one_by_id(name)
        return cast(Sign, SignSchema(unknown=EXCLUDE).load(data))

    def search_by_id(self, query: str) -> Sequence[Sign]:
        cursor = self._collection.aggregate([
            {"$match": {"_id": {"$regex": re.escape(query), "$options": "i"}}}
        ])
        return [SignSchema().load(sign, unknown=EXCLUDE) for sign in cursor]

    def search_all(self, reading: str, sub_index: Optional[str] = None) -> Sequence[Sign]:
        if sub_index:
            nested_query = {"value": reading, "subIndex": sub_index}
            cursor = self._collection.find_many(
                {
                    "values": {
                        "$elemMatch": nested_query
                    }
                }
            )
            return [SignSchema().load(sign, unknown=EXCLUDE) for sign in cursor]

    def search_composite_signs(self, reading: str, sub_index: Optional[str] = None) -> Sequence[Sign]:
        intermediate_results = self.search_all(reading, sub_index)
        return [self.search_by_id(result.name) for result in intermediate_results]

    def search(self, reading, sub_index) -> Optional[Sign]:
        sub_index_query = {"$exists": False} if sub_index is None else sub_index
        try:
            data = self._collection.find_one(
                {
                    "values": {
                        "$elemMatch": {"value": reading, "subIndex": sub_index_query}
                    }
                }
            )
            return cast(Sign, SignSchema(unknown=EXCLUDE).load(data))
        except NotFoundError:
            return None
