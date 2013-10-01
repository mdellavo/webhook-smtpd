from pyramid.config import Configurator
from sqlalchemy import engine_from_config

from .models import Session
from .mailbox_manager import MailboxManager

def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """

    engine = engine_from_config(settings, 'sqlalchemy.')
    Session.configure(bind=engine)

    MailboxManager.init(settings['maildir_path'])

    config = Configurator(settings=settings)

    config.add_renderer(
        name='json',
        factory='mailwebservice.serializer.JSONRenderer'
    )

    config.add_static_view('static', 'static', cache_max_age=3600)
    config.add_route('home', '/')
    config.add_route('incoming', '/incoming')
    config.add_route('dummy', '/dummy')
    config.scan()

    return config.make_wsgi_app()

