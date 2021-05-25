import falcon

from ebl.context import Context
from ebl.signs.web.sign_search import SignsSearch


def create_signs_routes(api: falcon.API, context: Context, spec):
    signs_search = SignsSearch(context.sign_repository)
    api.add_route("/signs", signs_search)
    spec.path(resource=signs_search)