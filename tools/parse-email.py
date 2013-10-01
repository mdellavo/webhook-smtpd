import re
import sys
import email

# FIXME if the content is interspersed with the quoted text, there will be 
# problems

pattern = lambda s: re.compile(s)

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


def clean_body(body):
    return ("\n".join(filter_response(split_body(body)))).strip()

def main():
    message = email.message_from_file(sys.stdin)

    for part in message.walk():
        content_type = part.get_content_type()
        filename = part.get_filename()
        if content_type == 'text/plain':
            
            body = part.get_payload(decode=True)
            print clean_body(body)
        elif filename:
            with open(filename, 'w') as f:
                print 'Saving attachment', content_type, filename
                f.write(part.get_payload(decode=True))
                
if __name__ == '__main__':
    main()
