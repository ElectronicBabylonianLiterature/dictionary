import falcon

from ebl.dispatcher import create_dispatcher
from ebl.fragmentarium.application.fragment_finder import FragmentFinder
from ebl.require_scope import require_scope


class LemmaSearch:

    def __init__(self, finder: FragmentFinder):
        self._dispatch = create_dispatcher({
            'word': finder.find_lemmas,
        })

    @falcon.before(require_scope, 'read:fragments')
    @falcon.before(require_scope, 'read:words')
    def on_get(self, req, resp):
        resp.media = self._dispatch(req.params)