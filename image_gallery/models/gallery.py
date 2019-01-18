import sqlalchemy as sa
import sqlalchemy.orm as orm

from .meta import Base


table_galleries_guests = sa.Table(
    'galleries_guests',
    Base.metadata,
    sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id')),
    sa.Column('gallery_id', sa.Integer, sa.ForeignKey('galleries.id')),
    sa.UniqueConstraint('user_id', 'gallery_id', name='const_galleries_guests')
)

table_galleries_collaborators = sa.Table(
    'galleries_collaborators',
    Base.metadata,
    sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id')),
    sa.Column('gallery_id', sa.Integer, sa.ForeignKey('galleries.id')),
    sa.UniqueConstraint('user_id', 'gallery_id', name='const_galleries_collaborators')
)


class Gallery(Base):
    __tablename__ = 'galleries'

    id = sa.Column(sa.Integer, primary_key=True)
    description = sa.Column(sa.Unicode(100))

    owner_id = sa.Column(sa.Integer, sa.ForeignKey('users.id'))
    owner = orm.relationship('User', back_populates='galleries')

    photos = orm.relationship('Photo', order_by='Photo.id', back_populates='gallery', lazy='dynamic')
    guests = orm.relationship('User', secondary=table_galleries_guests, lazy='dynamic')
    collaborators = orm.relationship('User', secondary=table_galleries_collaborators, lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'description': self.description
        }
