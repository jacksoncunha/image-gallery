import sqlalchemy as sa
import sqlalchemy.orm as orm

from .meta import Base
from datetime import datetime

table_photos_likes = sa.Table(
    'photos_likes',
    Base.metadata,
    sa.Column('photo_id', sa.Integer, sa.ForeignKey('photos.id')),
    sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id')),
    sa.UniqueConstraint('photo_id', 'user_id', name='const_photos_likes')
)


class Photo(Base):
    __tablename__ = 'photos'

    id = sa.Column(sa.Integer, primary_key=True)
    description = sa.Column(sa.Unicode(100))
    file_name = sa.Column(sa.Unicode(100))
    review_status = sa.Column(sa.SMALLINT, default=0)
    date = sa.Column(sa.Date, default=datetime.now())

    gallery_id = sa.Column(sa.Integer, sa.ForeignKey('galleries.id'))
    gallery = orm.relationship('Gallery', back_populates='photos')

    uploader_id = sa.Column(sa.Integer, sa.ForeignKey('users.id'))
    uploader = orm.relationship('User')

    likes = orm.relationship('User', secondary=table_photos_likes, lazy='dynamic')
