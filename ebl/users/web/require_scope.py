import falcon

from ebl.users.domain.user import User


def require_scope(req: falcon.Request, _resp, _resource, _params, scope: str):
    user: User = req.context.user
    if not user or not user.has_scope(scope):
        raise falcon.HTTPForbidden()
