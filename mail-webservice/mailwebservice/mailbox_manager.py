import mailbox
import logging

class MailboxManager(object):
    
    PATH = None
    
    @classmethod
    def init(cls, path):
        cls.PATH = path
        cls.log = logging.getLogger(cls.__name__)
        
    @classmethod
    def add(cls, message):
        mbox = mailbox.Maildir(cls.PATH)
        msg = mailbox.MaildirMessage(message)
        msg_id = mbox.add(msg)

        cls.log.debug('Filed message %s', msg_id)

        return msg_id

    @classmethod
    def get(cls, message):
        return mailbox.Maildir(cls.PATH).get(message.maildir_id)
