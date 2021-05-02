import smtplib
import re


class Gmail(object):
    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.server = 'smtp.gmail.com'
        self.port = 587
        session = smtplib.SMTP(self.server, self.port)        
        session.ehlo()
        session.starttls()
        session.login(self.email, self.password)
        self.session = session

    def send_message(self, receiver, subject, body):
        ''' This must be removed '''
        headers = [
            "From: " + self.email,
            "Subject: " + subject,
            "To: " + receiver,
            "MIME-Version: 1.0",
            "Content-Type: text/html"]
        headers = "\r\n".join(headers)

        try:
            self.session.sendmail(
                self.email,
                receiver,
                headers + "\r\n\r\n" + body)
        except Exception as e:
            print(e)


def validate_email(email):

    regex = '^(\w|\.|\_|\-)+[@](\w|\_|\-|\.)+[.]\w{2,3}$'

    if(re.search(regex, email)):
        return True
    else:
        return False


def validate_pincode(pincode):
    regex = "^[1-9][0-9]{5}$"

    if(re.search(regex, pincode)):
        return True
    else:
        return False
