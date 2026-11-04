# -*- coding: utf-8 -*-
# TextAnalytics (textanalytics)
__name__ = "mltk"
"""
TextAnalytics - a collection of text analytics tools for python.
===========================================================
'TextAnalytics' is a Python package providing a set of text analytics tools 
for data mining and machine learning projects and end-to-end text analytics 
application development. 

Author
------
- Sumudu Tennakoon

Links
-----
Website: http://sumudu.tennakoon.net/projects/TextAnalytics
Github: https://github.com/sptennak/TextAnalytics

License
-------
Apache License, Version 2.0 (http://www.apache.org/licenses/LICENSE-2.0)
"""
import os
import sys
import gc
import traceback
import warnings
import uuid
import base64
from itertools import product, combinations, permutations, combinations_with_replacement
import datetime
import time
from timeit import default_timer as timer
import re
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import bs4
import email
import mimetypes
from exchangelib import Account, Credentials, Configuration, EWSDateTime, UTC, UTC_NOW, FolderCollection, Q
from exchangelib import DELEGATE, IMPERSONATION
from exchangelib import Message, Mailbox, FileAttachment, ItemAttachment, HTMLBody

warnings.filterwarnings("ignore")


def get_tzinfo(tz_str=None, tz_seconds=None):

    if tz_str != None:
        if re.match(r"[-+]\d\d\d\d", tz_str):
            if tz_str[0] == "-":
                coeff = 1
            else:
                coeff = -1
            hours = float(tz_str[-4:-2])
            minutes = float(tz_str[-2:])
            delta = coeff * (hours * 3600 + minutes * 60)
            name = "UTC" + tz_str
    elif tz_seconds != None:
        if tz_seconds < 0:
            coeff = "+"
        else:
            coeff = "-"
        delta = tz_seconds
        hours = tz_seconds // 3600
        minutes = (tz_seconds % 3600) // 60
        name = "UTC{}{:02d}{:02d}".format(coeff, hours, minutes)
    else:
        tz_seconds = time.timezone
        if tz_seconds < 0:
            coeff = "+"
        else:
            coeff = "-"
        delta = tz_seconds
        hours = tz_seconds // 3600
        minutes = (tz_seconds % 3600) // 60
        name = "UTC{}{:02d}{:02d}".format(coeff, hours, minutes)

    tzinfo = datetime.timezone(offset=datetime.timedelta(seconds=delta), name=name)

    return tzinfo


def datetime_to_ewsdatetime(datetime_object=None, tz_str=None, tz_seconds=None):

    if datetime_object == None:
        datetime_object = datetime.datetime.now()

    if datetime_object.tzinfo == None:
        if tz_str == None and tz_seconds == None:
            seconds = time.timezone
        tz = get_tzinfo(tz_str=tz_str, tz_seconds=tz_seconds)
    else:
        tz = datetime_object.tzinfo

    ews_datetime = EWSDateTime(
        datetime_object.year,
        datetime_object.month,
        datetime_object.day,
        datetime_object.hour,
        datetime_object.minute,
        datetime_object.second,
        datetime_object.microsecond,
        tz,
    )

    return ews_datetime


def get_ews_datetime(datetime_object=None, tz_str=None, tz_seconds=None):

    if type(datetime_object) == str:
        try:
            datetime_object = email.utils.parsedate_to_datetime(datetime_object)
        except:
            try:
                datetime_object = datetime.datetime.strptime(datetime_object, "%Y-%m-%d %H:%M:%S")
            except:
                try:
                    datetime_object = datetime.datetime.strptime(datetime_object, "%Y-%m-%d %H:%M")
                except:
                    try:
                        datetime_object = datetime.datetime.strptime(datetime_object, "%Y-%m-%d %H")
                    except:
                        try:
                            datetime_object = datetime.datetime.strptime(datetime_object, "%Y-%m-%d")
                        except:
                            print(r"Provided date time string is not in accepted fromat: YYYY-MM-DD hh:mm:ss")
                            datetime_object = None
    else:
        pass

    if type(datetime_object) == datetime.datetime:
        ews_datetime = datetime_to_ewsdatetime(datetime_object=datetime_object, tz_str=tz_str, tz_seconds=tz_seconds)
    else:
        print("Returning currrent datetime in local timezone")
        ews_datetime = datetime_to_ewsdatetime()

    return ews_datetime


def save_binary_file(folder_path, file_name, content, content_type=None):
    file_path = os.path.join(folder_path, file_name)
    with open(file_path, "wb") as f:
        f.write(content)


def save_text(folder_path, file_name, content, content_type=None):
    file_path = os.path.join(folder_path, file_name)
    with open(file_path, "w") as f:
        f.write(content)


def save_email(folder_path, file_name, mime_content):
    save_text(folder_path, file_name, content=mime_content, content_type=None)


def read_eml(eml_file_path):
    return email.message_from_file(open(eml_file_path))


def save_attachment(folder_path, file_prefix, attachment):
    file_name = "{}_{}".format(file_prefix, file_name)
    try:
        content = attachment.content
    except:
        content = None
    try:
        content_type = attachment.content_type
    except:
        content_type = None

    save_binary_file(folder_path, file_name, content, content_type=content_type)


def decode_header_item(header_item):
    try:
        if header_item != None:
            decoder = email.header.decode_header(header_item)
            value = decoder[0][0]
            encoding = decoder[0][1]
            if encoding != None:
                header_item = value.decode(encoding)
            else:
                pass
        else:
            pass
    except:
        pass
    return header_item


def extract_contacts(raw_contacts):
    contacts = []
    if type(raw_contacts) == list:
        for contact in raw_contacts:
            try:
                contacts.append({"name": contact[0], "email": contact[1]})
            except:
                contacts.append({"contact": contact})
    else:
        try:
            contacts = {"name": raw_contacts[0], "email": raw_contacts[1]}
        except:
            contacts.append({"contact": raw_contacts})

    return contacts


def email_to_dataframe(email_data, fields_order=None):
    if fields_order == None:
        try:
            fields_order = list(email_data.keys())
        except:
            return pd.DataFrame(data=[email_data])

    return pd.DataFrame(data=[email_data])[fields_order]


def extract_mime_part(part, pid, encode_erros="strict"):

    part_data = {
        "pid": pid,
        "content_id": part.get("Content-id"),
        "content_main_type": part.get_content_maintype(),
        "content_sub_type": part.get_content_subtype(),
        "content_disposition": part.get_content_disposition(),
        "content_transfer_encoding": part.get("Content-Transfer-Encoding"),
        "content_charset": part.get_content_charset(),
    }

    content_main_type = part_data["content_main_type"]
    content_sub_type = part_data["content_sub_type"]
    content_charset = part_data["content_charset"]
    content_disposition = part_data["content_disposition"]
    content_transfer_encoding = part_data["content_transfer_encoding"]

    if (
        (content_disposition != "attachment")
        and (content_main_type == "text")
        and (content_sub_type in ("plain", "html"))
    ):
        isbody = True
        if content_charset is None:
            try:
                payload = part.get_payload(decode=True)
                for charset in ("ascii", "latin1", "utf-8", "iso8859_1", "Windows-1251", "Windows-1252", "iso8859_15"):
                    try:
                        payload = payload.decode(charset)
                    except:
                        raise
                decoded = True
            except:
                try:
                    payload = part.get_payload()
                    decoded = False
                except:
                    pass
        else:
            try:
                payload = part.get_payload(decode=True).decode(encoding=content_charset, errors=encode_erros)
                decoded = True
            except:
                try:
                    payload = part.get_payload()
                    decoded = False
                except:
                    pass

        part_data.update({"isbody": isbody, "payload": payload, "decoded": decoded})
    elif content_main_type == "message" and content_sub_type == "rfc822":
        subject = part.get("subject")
        isbody = False
        payload = part.get_payload(decode=True)
        decoded = True
        part_data.update({"isbody": isbody, "payload": payload, "decoded": decoded})
    elif (content_disposition == "attachment" or content_disposition == "inline") or (part.get_filename() != None):
        isbody = False
        payload = part.get_payload(decode=True)
        decoded = True
        part_data.update({"isbody": isbody, "payload": payload, "decoded": decoded, "file_name": part.get_filename()})
    return part_data


def read_email_eml(email_object, return_type="dict"):
    try:
        email_date = email.utils.format_datetime(
            email.utils.parsedate_to_datetime(email_object.get(name="date", failobj=""))
        )
    except:
        email_date = email_object.get(name="date", failobj=None)

    email_data = {
        "message_id": email_object.get(name="message-id", failobj=None),
        "date": email_date,
        "recieved_date": None,
        "recieved": email_object.get_all("received", failobj=None),
        "from": extract_contacts(email.utils.parseaddr(email_object.get(name="from", failobj=None))),
        "to": extract_contacts(email.utils.getaddresses(email_object.get_all(name="to", failobj=[]))),
        "cc": extract_contacts(email.utils.getaddresses(email_object.get_all(name="cc", failobj=[]))),
        "bcc": extract_contacts(email.utils.getaddresses(email_object.get_all(name="bcc", failobj=[]))),
        "reply_to": extract_contacts(email.utils.getaddresses(email_object.get_all(name="reply_to", failobj=[]))),
        "author_name": None,
        "author_email": None,
        "subject": email_object.get(name="subject", failobj=None),
        "references": email_object.get(name="references", failobj=[]),
        "has_attachments": email_object.get(name="x-ms-has-attach", failobj=None),
        "message_body": None,
        "attachments": None,
        "error": None,
    }

    try:
        email_data["author_name"] = email_data["from"]["name"]
        email_data["author_email"] = email_data["from"]["email"]
    except:
        pass

    email_parts = []
    pid = 0
    for part in email_object.walk():
        if part.get_content_maintype() == "multipart":
            continue

        pid = pid + 1
        email_parts.append(extract_mime_part(part, pid))

    email_data.update({"parts": email_parts})

    if return_type == "frame":
        fields_order = [
            "message_id",
            "date",
            "recieved_date",
            "recieved",
            "references",
            "author_name",
            "author_email",
            "reply_to",
            "from",
            "to",
            "cc",
            "bcc",
            "has_attachments",
            "subject",
            "message_body",
            "parts",
            "attachments",
            "error",
        ]
        email_to_dataframe(email_data, fields_order)

    return email_data


def connect_ews_user_account(
    username, password, server, primary_smtp_address, autodiscover=False, access_type=IMPERSONATION
):
    credentials = Credentials(username=username, password=password)
    config = Configuration(server=server, credentials=credentials)
    account = Account(
        primary_smtp_address=primary_smtp_address,
        credentials=credentials,
        autodiscover=autodiscover,
        config=config,
        access_type=access_type,
    )
    return account


def fetch_emails_ews(account, folder="INBOX", filters={}, print_tree=False):
    account.root.refresh()
    email_folder = account.root.glob("**/{}".format(folder)).folders[0]
    if "datetime_received__range" in filters:
        start_time = get_ews_datetime(filters["datetime_received__range"]["start"])
        end_time = get_ews_datetime(ffilters["datetime_received__range"]["end"])
        email_objects = email_folder.filter(datetime_received__range=(start_time, end_time))

    email_objects = list(email_objects)
    print("Number of emails", len(email_objects))

    if print_tree:
        print(account.root.tree())

    return email_objects


def read_email_ews(ews_object, return_type="dict"):
    if return_type == "dict":
        email_data = [
            {
                "message_id": ews_object.message_id,
                "sent_date": ews_object.datetime_sent,
                "recieved_date": ews_object.datetime_received,
                "from": ews_object.sender,
                "to": ews_object.to_recipients,
                "cc": ews_object.cc_recipients,
                "bcc": ews_object.bcc_recipients,
                "reply_to": ews_object.reply_to,
                "author_name": ews_object.author.name,
                "author_email": ews_object.author.email_address,
                "subject": ews_object.subject,
                "references": ews_object.references,
                "has_attachments": ews_object.has_attachments,
                "message_body": ews_object.body,
                "error": None,
            }
        ]

        email_parts = []
        for parts in ews_object.attachments:
            part_data = {
                "pid": None,
                "content_id": attachment.content_id,
                "content_type": attachment.content_type,
                "isbody": False,
                "payload": attachment.content,
                "decoded": None,
                "file_name": attachment.name,
                "size": attachment.size,
                "is_inline": attachment.is_inline,
            }
            email_parts.append(part_data)

        email_data.update({"parts": email_parts})
    elif return_type == "mime":
        email_data = ews_object.mime_content
    else:
        email_data = None

    return email_data


def ews_to_email_object(ews_object):

    return email.message_from_string(read_email_ews(ews_object, return_type="mime"))


def save_ews_to_eml(ews_object, folder_path, file_name):
    mime_content = read_email_ews(ews_object, return_type="mime")
    save_text(folder_path, file_name, mime_content, content_type=None)
