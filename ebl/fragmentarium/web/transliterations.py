import falcon
from falcon.media.validators.jsonschema import validate

from ebl.atf.domain.atf import Atf
from ebl.fragmentarium.application.fragment_updater import FragmentUpdater
from ebl.fragmentarium.web.dtos import create_response_dto
from ebl.require_scope import require_scope
from ebl.transliteration.domain.transliteration_error import \
    TransliterationError

TRANSLITERATION_DTO_SCHEMA = {
    'type': 'object',
    'properties': {
        'transliteration': {
            'type': 'string'
        },
        'notes': {
            'type': 'string'
        }
    },
    'required': [
        'transliteration',
        'notes'
    ]
}


class TransliterationResource:

    def __init__(self, updater: FragmentUpdater, transliteration_factory):
        self._updater = updater
        self._transliteration_factory = transliteration_factory

    @falcon.before(require_scope, 'transliterate:fragments')
    @validate(TRANSLITERATION_DTO_SCHEMA)
    def on_post(self, req, resp, number):
        try:
            user = req.context.user
            updated_fragment = self._updater.update_transliteration(
                number,
                self._create_transliteration(req.media),
                user
            )
            resp.media = create_response_dto(updated_fragment, user)
        except TransliterationError as error:
            resp.status = falcon.HTTP_UNPROCESSABLE_ENTITY
            resp.media = {
                'title': resp.status,
                'description': str(error),
                'errors': error.errors
            }

    def _create_transliteration(self, media):
        return self._transliteration_factory.create(
            Atf(media['transliteration']),
            media['notes']
        )