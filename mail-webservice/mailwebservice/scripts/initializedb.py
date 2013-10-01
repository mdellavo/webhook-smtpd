import os
import sys
import transaction

from sqlalchemy import engine_from_config, and_

from pyramid.paster import get_appsettings, setup_logging

from ..models import Session, Base, Domain, Route

def usage(argv):
    cmd = os.path.basename(argv[0])
    print('usage: %s <config_uri>\n'
          '(example: "%s development.ini")' % (cmd, cmd)) 
    sys.exit(1)

def main(argv=sys.argv):

    if len(argv) != 2:
        usage(argv)

    config_uri = argv[1]
    setup_logging(config_uri)
    settings = get_appsettings(config_uri)

    engine = engine_from_config(settings, 'sqlalchemy.')
    Session.configure(bind=engine)
    Base.metadata.create_all(engine)

    domain, created = Domain.get_by_or_create(Domain.name, 'example.com', 
                                              {'name': 'example.com'})
    Session.commit()
        
    criteria = and_(Route.domain == domain, 
                    Route.route == '{mbox}', 
                    Route.endpoint == 'http://localhost:6543')
    data = {
        'domain': domain, 
        'route': '{mbox}', 
        'endpoint': 'http://localhost:6543'
    }
    route, created = Route.find_or_create(criteria, data)

    Session.commit()
