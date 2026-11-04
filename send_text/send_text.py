import os
from email.encoders import encode_base64
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from smtplib import SMTP, SMTP_SSL, SMTPConnectError
from typing import Union


MMS_CARRIER_MAP = {
    "at&t": "mms.att.net",
    "boost": "myboostmobile.com",
    "boost mobile": "myboostmobile.com",
    "c spire": "cspire1.com",
    "c-spire": "cspire1.com",
    "cricket": "mms.cricketwireless.net",
    "google fi": "msg.fi.google.com",
    "metro pcs": "mymetropcs.com",
    "metro": "mymetropcs.com",
    "mint mobile": "mailmymobile.net",
    "mint": "mailmymobile.net",
    "sprint": "pm.sprint.com",
    "tmobile": "tmomail.net",
    "t-mobile": "tmomail.net",
    "tracfone": "mmst5.tracfone.com",
    "uscellular": "mms.uscc.net",
    "us cellular": "mms.uscc.net",
    "verizon": "vzwpix.com",
    "virgin mobile": "vmpix.com",
    "virgin": "vmpix.com",
    "xfinity mobile": "mypixmessages.com",
    "xfinity": "mypixmessages.com",
}

SMTP_SERVERS = [
    {"Email extension": "gmail.com", "Port number": "587", "SMTP server": "smtp.gmail.com"},
    {"Email extension": "outlook.com", "Port number": "587", "SMTP server": "smtp.live.com"},
    {"Email extension": "yahoo.com", "Port number": "465", "SMTP server": "smtp.mail.yahoo.com"},
    {"Email extension": "aol.com", "Port number": "587", "SMTP server": "smtp.aol.com"},
    {"Email extension": "hotmail.com", "Port number": "465", "SMTP server": "smtp.live.com"},
    {"Email extension": "comcast.net", "Port number": "587", "SMTP server": "smtp.comcast.net"},
    {"Email extension": "verizon.net", "Port number": "465", "SMTP server": "outgoing.verizon.net"},
    {"Email extension": "icloud.com", "Port number": "587", "SMTP server": "smtp.mail.me.com"},
    {"Email extension": "zohomail.com", "Port number": "465", "SMTP server": "smtp.zoho.com"},
]


class SendTextError(Exception):
    pass


class CarrierNotFound(SendTextError):
    pass


class CouldNotConnectToServer(SendTextError):
    pass


class InvalidRecipient(SendTextError):
    pass


class NoPortNumber(SendTextError):
    pass


class NoSMTPServer(SendTextError):
    pass


class SenderNotStarted(SendTextError):
    pass


class Sender:
    def __init__(self, email: str, passwd: str, smtp_server: str = None, port: str = None) -> None:

        self.email: str = email
        self.passwd: str = passwd

        if not smtp_server:
            try:
                email_ext = email.split("@")[1]
            except IndexError:
                raise NoSMTPServer("An SMTP server was not provided nor found")

            else:
                for server in SMTP_SERVERS:
                    if email_ext == server["Email extension"]:
                        smtp_server = server["SMTP server"]
                        self.smtp_server: str = smtp_server

                        if not port:
                            port = server["Port number"]
                            self.port: int = port
                            return

                        break

                if not smtp_server:
                    raise NoSMTPServer("An SMTP server was not provided nor found")

        else:
            self.smtp_server: str = smtp_server

        if not port:
            for server in SMTP_SERVERS:
                if smtp_server == server["SMTP server"]:
                    self.port: int = server["Port number"]
                    return

            raise NoPortNumber(
                "A port number was not provided nor found. Common port numbers include 587 and 465; maybe try one of those?"
            )

        else:
            self.port: int = port

    def start(self):
        if self.port == 587:
            self.server: SMTP = SMTP(self.smtp_server, self.port)
            self.server.starttls()

        elif self.port == 465:
            self.server: SMTP_SSL = SMTP_SSL(self.smtp_server, self.port)

        else:
            try:
                self.server: Union[SMTP, SMTP_SSL] = SMTP(self.smtp_server, self.port)
            except SMTPConnectError:
                self.server: Union[SMTP, SMTP_SSL] = SMTP_SSL(self.smtp_server, self.port)
            else:
                self.server.starttls()

        if self.server.ehlo()[0] != 250:
            raise CouldNotConnectToServer("Failed to connect to the SMTP server.")

        self.server.login(self.email, self.passwd)

    def quit(self):
        self.server.quit()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.quit()

    def text(self, recipient: str, message: str, carrier: str = None) -> None:

        if "@" not in recipient:
            if not carrier:
                raise InvalidRecipient(
                    "The recipient of the text message is invalid. It have an @ symbol in it and look like an email address."
                )

            carrier = carrier.lower()

            if carrier in MMS_CARRIER_MAP:
                recipient += "@" + MMS_CARRIER_MAP[carrier]
            else:
                raise CarrierNotFound(
                    "A carrier wasn't found. Try changing the recipient to include the MMS gateway domain."
                )

        msg = MIMEText(message, "plain", "utf-8")

        try:
            self.server.sendmail(self.email, recipient, msg.as_string())
        except AttributeError:
            raise SenderNotStarted(
                "The Sender object has not been started. Did you forget to call Sender.start (and Sender.quit)?"
            )

    def text_image(self, recipient: str, image: str, carrier: str = None) -> None:

        if "@" not in recipient:
            if not carrier:
                raise InvalidRecipient(
                    "The recipient of the text message is invalid. It should have an @ symbol in it and look like an email address."
                )

            carrier = carrier.lower()

            if carrier in MMS_CARRIER_MAP:
                recipient += "@" + MMS_CARRIER_MAP[carrier]
            else:
                raise CarrierNotFound(
                    "A carrier wasn't found. Try changing the recipient to include the MMS gateway domain."
                )

        with open(image, "rb") as f:
            img_data = f.read()

        img = MIMEImage(img_data, name=os.path.basename(image))
        img.add_header("Content-Disposition", "attachment", filename=os.path.basename(image))

        msg = MIMEMultipart()
        msg.attach(img)

        try:
            self.server.sendmail(self.email, recipient, msg.as_string())
        except AttributeError:
            raise SenderNotStarted(
                "The Sender object has not been started. Did you forget to call Sender.start (and Sender.quit)?"
            )

    def text_video(self, recipient: str, video: str, carrier: str = None) -> None:

        if "@" not in recipient:
            if not carrier:
                raise InvalidRecipient(
                    "The recipient of the text message is invalid. It should have an @ symbol in it and look like an email address."
                )

            carrier = carrier.lower()

            if carrier in MMS_CARRIER_MAP:
                recipient += "@" + MMS_CARRIER_MAP[carrier]
            else:
                raise CarrierNotFound(
                    "A carrier wasn't found. Try changing the recipient to include the MMS gateway domain."
                )

        with open(video, "rb") as f:
            vid_data = f.read()

        vid = MIMEBase("application", "octet-stream")
        vid.set_payload(vid_data)
        encode_base64(vid)

        vid.add_header("Content-Disposition", "attachment", filename=os.path.basename(video))

        msg = MIMEMultipart()
        msg.attach(vid)

        try:
            self.server.sendmail(self.email, recipient, msg.as_string())
        except AttributeError:
            raise SenderNotStarted(
                "The Sender object has not been started. Did you forget to call Sender.start (and Sender.quit)?"
            )
