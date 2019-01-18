import sqlalchemy as sa
import sqlalchemy.orm as orm

from .gallery import Gallery
from .meta import Base


class User(Base):
    __tablename__ = 'users'

    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.Unicode(100))
    email = sa.Column(sa.Unicode(100), unique=True)
    password = sa.Column(sa.Unicode(100))

    galleries = orm.relationship('Gallery', order_by=Gallery.id, back_populates="owner")
