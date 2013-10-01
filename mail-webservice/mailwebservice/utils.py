import re
import sys
import email

# FIXME if the content is interspersed with the quoted text, there will be 
# problems

pattern = lambda s: re.compile(s)

def find(f, seq):
    for item in seq:
        if f(item): 
            return item
            
JUNK_PATTERNS = [
    pattern(r'^>\s*'), 
    pattern(r'^On(.+)wrote:$'), 
    pattern(r'^Sent from my(.+)'),
    pattern(r'^-- ?$'),
    pattern(r'^-----Original Message-----'),
    pattern(r'^_{32}'),
    pattern(r'^From: ')
]

def split_body(s):
    return (i.strip() for i in s.splitlines())

def junk_test(s):
    return any([pattern.match(s) for pattern in JUNK_PATTERNS])
    
def filter_response(lines):
    for i in lines:
        if junk_test(i):
            return 

        yield i

def text_body(message):
    is_text_body = lambda i: i.get_content_type() == 'text/plain'
    body = find(is_text_body, message.walk())
    return body.get_payload(decode=True)

def clean_body(message):
    body = filter_response(split_body(text_body(message)))
    return ("\n".join(body)).strip()

def split_email(s):
    return s[:s.index('@')], s[s.index('@') + 1:]

class EmailAddress(object):
    def __init__(self, recipient):
        self.address = recipient
        self.user, self.domain = split_email(recipient)
    
