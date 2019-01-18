import argparse
import sys

from pyramid.paster import bootstrap, setup_logging
from sqlalchemy.exc import OperationalError

from .. import models


def setup_models(dbsession):
    """
    Add or update models / fixtures in the database.

    """
    user1 = models.user.User(name='Jack', email='jack@imagegallery.com', password='123')
    user2 = models.user.User(name='Erica', email='erica@imagegallery.com', password='123')
    user3 = models.user.User(name='Shara', email='shara@imagegallery.com', password='123')
    user4 = models.user.User(name='Rondi', email='rondi@imagegallery.com', password='123')

    dbsession.add(user1)
    dbsession.add(user2)
    dbsession.add(user3)
    dbsession.add(user4)


def parse_args(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'config_uri',
        help='Configuration file, e.g., development.ini',
    )
    return parser.parse_args(argv[1:])


def main(argv=sys.argv):
    args = parse_args(argv)
    setup_logging(args.config_uri)
    env = bootstrap(args.config_uri)

    try:
        with env['request'].tm:
            dbsession = env['request'].dbsession
            setup_models(dbsession)
    except OperationalError:
        print('''
Pyramid is having a problem using your SQL database.  The problem
might be caused by one of the following things:

1.  You may need to initialize your database tables with `alembic`.
    Check your README.txt for description and try to run it.

2.  Your database server may not be running.  Check that the
    database server referred to by the "sqlalchemy.url" setting in
    your "development.ini" file is running.
            ''')
