import sys
import smtplib

server = smtplib.SMTP('127.0.0.1', 1025)
try:
    server.sendmail('author@example.com',
                    ['recipient@example.com'], 
                    sys.stdin.read())
finally:
    server.quit()
