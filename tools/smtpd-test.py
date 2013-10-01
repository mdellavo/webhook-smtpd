import smtplib
import email.utils
from email.mime.text import MIMEText


def sendmail():
    msg = MIMEText('This is the body of the message.')
    msg['To'] = email.utils.formataddr(('Recipient', 'recipient@example.com'))
    msg['From'] = email.utils.formataddr(('Author', 'author@example.com'))
    msg['Subject'] = 'Simple test message'
    
    server = smtplib.SMTP('127.0.0.1', 1025)
#server.set_debuglevel(True) # show communication with the server
    try:
        server.sendmail('author@example.com', ['recipient@example.com'],
                        msg.as_string())
    finally:
        server.quit()

for i in range(25):
    print 'sending mail', i
    sendmail()
