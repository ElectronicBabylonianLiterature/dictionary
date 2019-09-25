import os
from base64 import b64decode

import falcon
import sentry_sdk
from cryptography.hazmat.backends import default_backend
from cryptography.x509 import load_pem_x509_certificate
from falcon_auth import FalconAuthMiddleware
from pymongo import MongoClient
from sentry_sdk.integrations.wsgi import SentryWsgiMiddleware

import ebl.error_handler
from ebl.auth0 import Auth0Backend
from ebl.bibliography.infrastructure.bibliography import MongoBibliography
from ebl.bibliography.web.bootstrap import create_bibliography_routes
from ebl.changelog import Changelog
from ebl.context import Context
from ebl.corpus.infrastructure.mongo_text_repository import MongoTextRepository
from ebl.corpus.web.bootstrap import create_corpus_routes
from ebl.cors_component import CorsComponent
from ebl.dictionary.infrastructure.dictionary import MongoDictionary
from ebl.dictionary.web.bootstrap import create_dictionary_routes
from ebl.files.infrastructure.file_repository import GridFsFiles
from ebl.files.web.files import create_files_resource
from ebl.fragmentarium.infrastructure.fragment_repository import \
    MongoFragmentRepository
from ebl.fragmentarium.web.bootstrap import create_fragmentarium_routes
from ebl.openapi.web.bootstrap import create_open_api_route
from ebl.openapi.web.spec import create_spec
from ebl.signs.application.atf_converter import AtfConverter
from ebl.signs.infrastructure.mongo_sign_repository import \
    MongoSignRepository


def create_api(context: Context) -> falcon.API:
    auth_middleware = FalconAuthMiddleware(context.auth_backend)
    api = falcon.API(middleware=[CorsComponent(), auth_middleware])
    ebl.error_handler.set_up(api)
    return api


def create_app(context: Context, issuer: str = '', audience: str = ''):
    api = create_api(context)
    spec = create_spec(api, issuer, audience)

    transliteration_search = AtfConverter(context.sign_repository)
    create_bibliography_routes(api, context, spec)
    create_dictionary_routes(api, context, spec)
    create_fragmentarium_routes(api, context, transliteration_search, spec)
    create_corpus_routes(api, context, transliteration_search, spec)

    files = create_files_resource(context.auth_backend)(context.files)
    api.add_route('/images/{file_name}', files)
    spec.path(resource=files)

    create_open_api_route(api, spec)

    return api


def get_app():
    client = MongoClient(os.environ['MONGODB_URI'])
    database = client.get_database()
    auth_backend = Auth0Backend(
        decode_certificate(os.environ['AUTH0_PEM']),
        os.environ['AUTH0_AUDIENCE'],
        os.environ['AUTH0_ISSUER']
    )

    context = Context(
        auth_backend=auth_backend,
        dictionary=MongoDictionary(database),
        sign_repository=MongoSignRepository(database),
        files=GridFsFiles(database),
        fragment_repository=MongoFragmentRepository(database),
        changelog=Changelog(database),
        bibliography=MongoBibliography(database),
        text_repository=MongoTextRepository(database)
    )

    app = create_app(context,
                     os.environ['AUTH0_ISSUER'],
                     os.environ.get['AUTH0_AUDIENCE'])

    sentry_sdk.init(dsn=os.environ['SENTRY_DSN'])
    return SentryWsgiMiddleware(app)


def decode_certificate(encoded_certificate):
    certificate = b64decode(encoded_certificate)
    cert_obj = load_pem_x509_certificate(certificate, default_backend())
    return cert_obj.public_key()
