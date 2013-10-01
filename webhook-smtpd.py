#!/usr/bin/env python

# https://github.com/bcoe/secure-smtpd
# http://documentation.mailgun.net/user_manual.html#um-routes
# https://github.com/benoitc/gunicorn/tree/master/gunicorn
# http://stackoverflow.com/questions/1372694/strip-signatures-and-replies-from-emails
# https://github.com/github/email_reply_parser
# http://stackoverflow.com/questions/2168719/parsing-forwarded-emails
# http://stackoverflow.com/questions/6025184/how-can-i-parse-email-text-for-components-like-salutationbodysignaturerep

# http://untroubled.org/spam/

import gevent
import gevent.monkey

gevent.monkey.patch_all()

import os
import json
import email
import smtpd
import urllib
import urllib2
import logging
import asyncore
import itertools
import mimetools
import mimetypes
import logging.config
from ConfigParser import ConfigParser

CONFIG_PATH = 'webhook-smtpd.ini'
USER_AGENT = 'WebHookSMTPd/0.0'

log = logging.getLogger('webhook-smtpd')

class SMTPResponse(object):
    def __init__(self, code=None, text=None):
        self.code = code or self.__class__.code
        self.text = text or self.__class__.text

    def __str__(self):
        return '%s %s' % (self.code, self.text)

class SMTPSuccess(SMTPResponse):
    code = 200
    text = 'Success'

class SMTPUnavailable(SMTPResponse):
    code = 450
    text = 'Unavailable'

flatten_response = lambda rv: str(rv) if isinstance(rv, SMTPResponse) else rv

class SMTPChannel(smtpd.SMTPChannel, object):
    def __init__(self, *args, **kwargs):
        super(SMTPChannel, self).__init__(*args, **kwargs)
        self.log = logging.getLogger(self.__class__.__name__)

class WebHookSMTPServer(smtpd.SMTPServer, object):

    channel_class = SMTPChannel

    def __init__(self, localaddr, remoteaddr, endpoint):
        super(WebHookSMTPServer, self).__init__(localaddr, remoteaddr)
        self.endpoint = endpoint
        self.log = logging.getLogger(self.__class__.__name__)

    def handle_accept(self):
        pair = self.accept()
        if pair is not None:
            conn, addr = pair
            channel = self.channel_class(self, conn, addr)

    def process_message(self, peer, from_address, recipient_addresses, data):
        peer_ip, peer_port = peer

        message = email.message_from_string(data)

        message['X-Peer-IP'] = peer_ip
        message['X-From-Address'] = from_address
        message['X-Recipient-Addresses'] = '; '.join(recipient_addresses)

        self.log.info('New connection from %s', peer_ip)
        self.log.info('Mail from %s to %s', from_address,
                      ', '.join(recipient_addresses))
        
        self.log.info('Dispatching email to %s', self.endpoint)

        body = message.as_string()

        request = urllib2.Request(self.endpoint)
        request.add_header('User-agent', USER_AGENT)
        request.add_header('Content-type', message.get_content_type())
        request.add_header('Content-length', len(body))
        request.add_data(body)
        
        try:
            f = urllib2.urlopen(request)
            rv = None
        except urllib2.URLError, e:
            self.log.exception('Could not post message to endpoing %s',
                               self.endpoint)
            rv = SMTPUnavailable()

        return flatten_response(rv)

    def start(self):
        self.log.debug('Starting server...')
        
        try: 
            asyncore.loop()
        finally:
            self.log.debug('Server closed.')

def main():

    logging.config.fileConfig(CONFIG_PATH)

    config = ConfigParser()
    config.read(CONFIG_PATH)

    localaddr = (config.get('webhook-smtpd', 'host'),
                 config.getint('webhook-smtpd', 'port'))
    remoteaddr = None
    endpoint = config.get('webhook-smtpd', 'endpoint')
    server = WebHookSMTPServer(localaddr, remoteaddr, endpoint)

    # for i in range(3):
    #     if os.fork() == 0:
    #         server.start()

    server.start()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
    finally:
        log.debug('goodbye')
