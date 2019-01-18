from pyramid.view import (view_config, view_defaults)

from uuid import uuid4
from datetime import datetime
from sqlalchemy import or_, func, desc

from ..models.gallery import Gallery
from ..models.photo import Photo
from ..models.user import User

import boto3


@view_defaults(
    permission='default_permission'
)
class GalleryViews:
    def __init__(self, request):
        self.request = request

    def is_owner(self, gallery, user_id):
        return gallery.owner_id == user_id

    def is_collaborator(self, gallery, user_id):
        return gallery.collaborators.filter(User.id == user_id).first() is not None

    def is_guest(self, gallery, user_id):
        return gallery.guests.filter(User.id == user_id).first() is not None

    @view_config(
        renderer='../templates/galleries.jinja2',
        route_name='gallery_home'
    )
    def list_view(self):
        return {
            'current_user_name': self.request.user.name
        }

    @view_config(
        renderer='../templates/gallery.jinja2',
        route_name='gallery_detail'
    )
    def detail_view(self):
        request = self.request

        userid = request.authenticated_userid
        gallery_id = request.matchdict['id']

        query_gallery = request.dbsession.query(Gallery)
        gallery = query_gallery.filter(Gallery.id == gallery_id).first()
        is_owner = self.is_owner(gallery, userid)
        is_collaborator = self.is_collaborator(gallery, userid)
        is_guest = self.is_guest(gallery, userid)

        def map_user(u):
            return {
                'name': u.name,
                'email': u.email
            }

        owner = map_user(gallery.owner)
        collaborators = list(map(lambda u: map_user(u), gallery.collaborators)) if gallery.collaborators else []
        guests = list(map(lambda u: map_user(u), gallery.guests)) if gallery.guests else []

        return {
            'current_user_name': request.user.name,
            'gallery': gallery.to_dict(),
            'isOwner': is_owner,
            'isCollaborator': is_collaborator,
            'isGuest': is_guest,
            'owner': owner,
            'collaborators': collaborators,
            'guests': guests
        }

    @view_config(
        renderer='json',
        route_name='gallery_detail_json'
    )
    def json_detail_view(self):
        request = self.request

        userid = request.authenticated_userid
        gallery_id = request.matchdict['id']
        display_option = request.params.get('display', '')
        ordering_option = request.params.get('order', 'date')

        query_gallery = request.dbsession.query(Gallery)
        gallery = query_gallery.filter(Gallery.id == gallery_id).first()

        is_owner = self.is_owner(gallery, userid)
        is_collaborator = self.is_collaborator(gallery, userid)

        query_photos = request.dbsession.query(Photo, func.count(User.id).label('count_likes')) \
            .outerjoin(Photo.likes).group_by(Photo.id)

        if (is_owner or is_collaborator) and display_option == 'review':
            query_photos = query_photos.filter(Photo.review_status == 0)
        elif (is_owner or is_collaborator) and display_option == 'block':
            query_photos = query_photos.filter(Photo.review_status == 2)
        else:
            query_photos = query_photos.filter(Photo.review_status == 1)

        if ordering_option == 'likes':
            query_photos = query_photos.order_by(desc('count_likes'))
        else:
            query_photos = query_photos.order_by(Photo.date.desc())

        photos = query_photos.filter().all()

        s3 = boto3.client('s3')

        def mapper(p):
            url = s3.generate_presigned_url(
                ClientMethod='get_object',
                Params={
                    'Bucket': request.registry.settings['amazons3.bucketname'],
                    'Key': p[0].file_name
                }
            )

            return {
                'id': p[0].id,
                'description': p[0].description,
                'date': datetime.strftime(p[0].date, '%m/%d/%Y'),
                'uploader': p[0].uploader.name,
                'userLiked': p[0].likes.filter(User.id == userid).first() is not None,
                'reviewStatus': p[0].review_status,
                'countLikes': p[1],
                'url': url
            }

        return {
            'photos': list(map(lambda p: mapper(p), photos)) if photos else [],
            'displayOption': display_option,
            'orderOption': ordering_option
        }

    @view_config(
        renderer='json',
        route_name='gallery_list'
    )
    def load_list_view(self):
        request = self.request
        userid = request.authenticated_userid

        query = request.dbsession.query(Gallery)
        galleries = query.filter(or_(
            Gallery.owner_id == userid,
            Gallery.collaborators.any(User.id == userid),
            Gallery.guests.any(User.id == userid)))\
            .all()

        s3 = boto3.client('s3')

        def mapper(g):
            url = ''
            main_photo = g.photos.filter(Photo.review_status == 1).first()

            if main_photo:
                url = s3.generate_presigned_url(
                    ClientMethod='get_object',
                    Params={
                        'Bucket': request.registry.settings['amazons3.bucketname'],
                        'Key': main_photo.file_name
                    }
                )

            return {
                'id': g.id,
                'description': g.description,
                'photo_url': url
            }

        return {
            'galleries': list(map(lambda g: mapper(g), galleries)) if galleries else []
        }

    @view_config(
        renderer='json',
        route_name='gallery_save'
    )
    def save(self):
        request = self.request

        gallery = Gallery()
        gallery.description = request.POST.get('description', '')
        gallery.owner_id = request.authenticated_userid

        request.dbsession.add(gallery)

        return {
            'result': True
        }

    @view_config(
        renderer='json',
        route_name='gallery_save_photo'
    )
    def save_photo(self):
        request = self.request

        file = request.POST.get('file').file

        photo = Photo()
        photo.file_name = str(uuid4())
        photo.description = request.POST.get('description', '')
        photo.date = datetime.strptime(request.POST.get('date'), '%Y-%m-%d')
        photo.gallery_id = request.POST.get('gallery', '')
        photo.uploader_id = request.authenticated_userid

        request.dbsession.add(photo)

        s3 = boto3.client('s3')
        s3.upload_fileobj(file, request.registry.settings['amazons3.bucketname'], photo.file_name)

        return {
            'result': True
        }

    @view_config(
        renderer='json',
        route_name='gallery_update_review_status'
    )
    def update_review_status(self):
        request = self.request

        userid = request.authenticated_userid
        photo_id = request.params.get('id')
        photo_status = request.params.get('status')

        photo = request.dbsession.query(Photo).filter(Photo.id == photo_id).first()
        gallery = photo.gallery

        is_owner = gallery.owner_id == userid
        is_collaborator = gallery.collaborators.filter(User.id == userid)

        result = False

        if photo and (is_owner or is_collaborator):
            photo.review_status = photo_status
            result = True

        return {
            'result': result
        }

    @view_config(
        renderer='json',
        route_name='gallery_like_photo'
    )
    def like(self):
        request = self.request

        userid = request.authenticated_userid
        photo_id = request.params.get('id')

        photo = request.dbsession.query(Photo).filter(Photo.id == photo_id).first()
        user = photo.likes.filter(User.id == userid).first()

        if user is not None:
            photo.likes.remove(request.user)
        else:
            photo.likes.append(request.user)

        return {
            'result': True
        }

    @view_config(
        renderer='json',
        route_name='gallery_invite_user'
    )
    def invite_user(self):
        request = self.request

        userid = request.authenticated_userid
        gallery_id = request.params.get('gallery')
        user_email = request.params.get('user')
        option = request.params.get('option')
        type_invite = request.params.get('type')

        gallery = request.dbsession.query(Gallery).filter(Gallery.id == gallery_id).first()
        is_owner = self.is_owner(gallery, userid)
        is_collaborator = self.is_collaborator(gallery, userid)
        result = False

        if is_owner or is_collaborator:
            if option == 'add':
                user = request.dbsession.query(User).filter(User.email == user_email).first()
                if user is not None:
                    if type_invite == 'collaborator':
                        gallery.collaborators.append(user)
                    elif type_invite == 'guest':
                        gallery.guests.append(user)
                    result = True
            elif option == 'remove':
                if type_invite == 'collaborator':
                    user = gallery.collaborators.filter(User.email == user_email).first()
                    if user is not None:
                        gallery.collaborators.remove(user)
                        result = True
                elif type_invite == 'guest':
                    user = gallery.guests.filter(User.email == user_email).first()
                    if user is not None:
                        gallery.guests.remove(user)
                        result = True

        return {
            'result': result
        }
