from pyramid.config import Configurator
from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy

from pyramid.security import Allow, Authenticated
from .models.user import User


class Root(object):
    __acl__ = [
        (Allow, Authenticated, 'default_permission')
    ]

    def __init__(self, request):
        self.request = request


def get_user(request):
    userid = request.authenticated_userid
    if userid is not None:
        return request.dbsession.query(User).filter(User.id == userid).first()


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    with Configurator(settings=settings) as config:
        authn_policy = AuthTktAuthenticationPolicy('seekrit', hashalg='sha512')
        authz_policy = ACLAuthorizationPolicy()

        config.set_authentication_policy(authn_policy)
        config.set_authorization_policy(authz_policy)
        config.set_default_permission('default_permission')
        config.set_root_factory(Root)
        config.add_request_method(get_user, 'user', reify=True)

        config.include('.models')
        config.include('pyramid_jinja2')
        config.include('.routes')
        config.scan()
    return config.make_wsgi_app()
