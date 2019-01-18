from pyramid.view import (
    view_config,
    view_defaults,
    forbidden_view_config
)

from pyramid.security import (
    NO_PERMISSION_REQUIRED,
    authenticated_userid,
    remember,
    forget
)

from pyramid.httpexceptions import (
    HTTPForbidden,
    HTTPFound
)

from ..models.user import(
    User
)


class SecurityViews:
    def __init__(self, request):
        self.request = request

    @forbidden_view_config()
    def forbidden_view(self):
        request = self.request
        if authenticated_userid(request):
            return HTTPForbidden()

        loc = request.route_url('login', _query=(('next', request.path),))
        return HTTPFound(location=loc)

    @view_config(
        route_name='login',
        permission=NO_PERMISSION_REQUIRED,
        renderer='../templates/login.jinja2',
    )
    def login_view(self):
        request = self.request

        next_url = request.params.get('next') or request.route_url('gallery_home')
        login = ''
        failed_attempt = False

        if 'form.submitted' in request.POST:
            login = request.POST.get('login', '')
            password = request.POST.get('password', '')
            user = request.dbsession.query(User).filter(User.email == login).first()

            if user and user.password == password:
                headers = remember(request, user.id)
                return HTTPFound(location=next_url, headers=headers)

            failed_attempt = True

        return {
            'login': login,
            'url': request.application_url + '/login',
            'next': next_url,
            'failed_attempt': failed_attempt
        }

    @view_config(
        route_name='logout',
        permission=NO_PERMISSION_REQUIRED
    )
    def logout_view(self):
        request = self.request
        headers = forget(request)
        loc = request.route_url('login')
        return HTTPFound(location=loc, headers=headers)
