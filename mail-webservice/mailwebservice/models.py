from sqlalchemy import engine_from_config, Table, Column, Integer, String, \
    ForeignKey, and_
from sqlalchemy.orm import relation
from sqlalchemy.ext.associationproxy import association_proxy

from athanor import Base, Session, UTCDateTime, DeclEnum, build_eav

from pytz import UTC

import re
import uuid
import email.utils
from datetime import datetime

from .utils import find

generate_uid = lambda: uuid.uuid4().hex
utcnow = UTC.localize(datetime.utcnow())

class Domain(Base):
    id = Column(Integer, primary_key=True)
    uid = Column(String, nullable=False, unique=True, index=True,
                 default=generate_uid)
    name = Column(String, nullable=False, unique=True, index=True)

    @classmethod
    def match_recipients(cls, recipients):
        recipient_domains = [i.domain for i in recipients]
        criteria = cls.name.in_(recipient_domains)
        domain_map = dict((i.name, i) for i in cls.objects.filter(criteria))
        return [ (domain_map[i.domain], i) for i in recipients \
                     if i.domain in domain_map]

class RouteType(DeclEnum):
    HEADER = 'HEADER', 'Header'
    MAILBOX = 'MAILBOX', 'Mailbox'

class Route(Base):
    id = Column(Integer, primary_key=True)
    uid = Column(String, nullable=False, unique=True, index=True,
                 default=generate_uid)
    type = Column(RouteType.db_type(), nullable=False)
    domain_id = Column(Integer, ForeignKey('domains.id'), nullable=False,
                       index=True)
    order = Column(Integer)

    endpoint = Column(String, nullable=False)

    domain = relation(Domain, backref='routes')

    __mapper_args__ = {'polymorphic_on': type}

class HeaderRoute(Route):
    __mapper_args__ = {'polymorphic_on': RouteType.HEADER}

    id = Column(Integer, ForeignKey('routes.id'), primary_key=True)
    
    header_pattern = Column(String, nullable=False)
    value_pattern = Column(String, nullable=False)

    @property
    def header_re(self):
        sub = lambda m: r'(?P<%s>[\w-]+)' % m.groups(0)
        return re.sub(r'\{(\w+)\}', sub, self.header)

    @property
    def value_re(self):
        sub = lambda m: r'(?P<%s>[\w-]+)' % m.groups(0)
        return re.sub(r'\{(\w+)\}', sub, self.pattern)

    def match(self, recipient, message):
        header_re = self.header_re
        value_re = self.value_re

        for header, value in message.items():
            header_match = re.match(header_re, header)
            value_match = re.match(value_re, value)

            if all([header_match, value_match]):
                return { 'header': header_match.matchdict(),
                         'value': value_match.matchdict() }

        return None

class MailboxRoute(Route):
    __mapper_args__ = {'polymorphic_on': RouteType.MAILBOX}

    id = Column(Integer, ForeignKey('routes.id'), primary_key=True)
  
    pattern = Column(String, nullable=False)    

    @property
    def pattern_re(self):
        sub = lambda m: r'(?P<%s>[\w.]+)' % m.groups(0)
        return re.sub(r'\{(\w+)\}', sub, self.pattern) + r'(\+[^@])?'
  
    def match(self, recipient, message):
        match = re.match(self.pattern_re, recipient.user)
        return match.matchdict() if match else None

class MessageStatus(DeclEnum):
    INCOMING = 'INCOMING', 'Incoming'
    QUEUED = 'QUEUED', 'Queued'
    REJECTED = 'REJECTED', 'Rejected'
    DELIVERED = 'DELIVERED', 'Delivered'
    FAILED = 'FAILED', 'Failed'

class Message(Base):
    id = Column(Integer, primary_key=True)
    uid = Column(String, nullable=False, unique=True, index=True,
                 default=generate_uid)
    status = Column(MessageStatus.db_type(), nullable=False,
                    default=MessageStatus.INCOMING)
    received_at = Column(UTCDateTime, nullable=False, default=utcnow)
    delivered_at = Column(UTCDateTime, nullable=True)
    
    route_id = Column(Integer, ForeignKey('routes.id'))

    peer = Column(String, nullable=False)

    to_name = Column(String)
    to_address = Column(String, nullable=False)
    from_name = Column(String)
    from_address = Column(String, nullable=False)
    subject = Column(String)

    maildir_id = Column(String)

    route = relation(Route)

    def to_dict(self):
        return super(Message, self).to_dict(exclude=('id', 'route_id',
                                                     'maildir_id'))

    @classmethod
    def create_from_message(cls, route, peer, from_address, to_address, msg):

        to_name = find(lambda x: x[0]==to_address, 
                       email.utils.getaddresses(msg.get_all('to')))

        obj = cls.create(
            route=route,
            peer=peer,
            from_address=from_address,
            from_name=email.utils.parseaddr(msg.get('from'))[0] or None,
            to_address=to_address,
            to_name=to_name,
            subject=msg.get('subject'),
        )

        obj.envelope.update(dict(msg))

        return obj

    def get_message(self):
        return MailboxManager.get(self)

    @property
    def envelope(self):
        return self.data

MessageEnvelope = build_eav(Message)

class MessageAttachment(Base):
    id = Column(Integer, primary_key=True)
    uid = Column(String, nullable=False, unique=True, index=True,
                 default=generate_uid)
    message_id = Column(Integer, ForeignKey('messages.id'), nullable=False)
    filename = Column(String)
    mime_type = Column(String)
    

class BayesWord(Base):
    word = Column(String(convert_unicode='force'), primary_key=True)
    nspam = Column(Integer, nullable=False, default=0)
    nham = Column(Integer, nullable=False, default=0)
