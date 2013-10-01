from pyramid.response import Response
from pyramid.view import view_config

from .models import Session, Domain, Route, Message
from .utils import EmailAddress, clean_body
from .mailbox_manager import MailboxManager
from .serializer import JSONRenderer

import json
import email
import logging
import urllib2
import pprint
from datetime import datetime

USER_AGENT = 'MailWebService/0.0'

log = logging.getLogger(__name__)

def match_message(recipients, message):
    for domain, recipient in Domain.match_recipients(recipients):
        for route in domain.routes:
            match = route.match(recipient, message)

            if match:
                yield recipient, route, match

# FIXME
def dispatch_message(message, match):

    log.debug('Dispatching message to %s', message.route.endpoint)

    def encode(value):
        if isinstance(value, datetime):
            return value.isoformat()

        raise TypeError('%s is not JSON serializable' % value.__class__)

    data = {
        'message': message.to_dict(),
        'route': match,
        'envelope': dict(message.envelope)
    }

    request = urllib2.Request(message.route.endpoint)
    request.add_header('User-Agent', USER_AGENT)
    request.add_header('Content-Type', 'application/json')
    request.add_header('Content-Length', len(data))
    request.add_data(json.dumps(data, default=encode))
    
    response = urllib2.urlopen(request)
    rv = json.load(response)
    response.close()

    return rv

def email_addresses(s):
    return [EmailAddress(i) for i in s.split('; ')]

@view_config(route_name='incoming', request_method='POST', renderer='json')
def incoming(request):

    email_message = email.message_from_file(request.body_file)
    
    peer = email_message['X-Peer-IP']
    from_address = EmailAddress(email_message['X-From-Address'])
    recipients = email_addresses(email_message['X-Recipient-Addresses'])
    
    matches = match_message(recipients, email_message)

    for recipient, route, match in matches:
        log.debug('Matched %s to route %s@%s -> %s', 
                  recipient.address, route.route,
                  route.domain.name, route.endpoint)

        message = Message.create_from_message(
            route, peer, from_address.address, recipient.address, email_message
        )        

        message.maildir_id = MailboxManager.add(email_message)

        Session.commit()

        dispatch_message(message, match)

    return {}

@view_config(route_name='dummy', request_method='POST', renderer='json')
def dummy(request):
    data = json.load(request.body_file)
    pprint.pprint(data)
    return {'status': 'ok'}
