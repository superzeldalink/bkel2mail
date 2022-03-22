#!/usr/bin/python3
import os
import smtplib
import requests
import sqlite3
import logging
from datetime import datetime

path = os.path.dirname(os.path.abspath(__file__))

logger = logging.getLogger()

handler = logging.FileHandler(path + '/log.txt')
logger.addHandler(handler)

formatter = logging.Formatter('%(asctime)s - %(message)s')
handler.setFormatter(formatter)

def getUserid(token):
    query = {'wstoken':token, 'wsfunction':'core_webservice_get_site_info'}
    response = requests.get('http://e-learning.hcmut.edu.vn/webservice/rest/server.php?moodlewsrestformat=json', params=query)
    try:
        return response.json()['userid']
    except:
        logger.error("Error: UserID get failed for " + str(token))
        return None

def getNotification(token, userid):
    query = {'wstoken':token, 'useridto':userid, 'limitnum':50, 'read':0, 'wsfunction':'core_message_get_messages', 'type':'both'}
    response = requests.get('http://e-learning.hcmut.edu.vn/webservice/rest/server.php?moodlewsrestformat=json', params=query)
    try:
        return response.json()['messages']
    except:
        logger.error("Error: Notification get failed for " + str(userid))
        return None

def sendNotification(receiver, subject, body):
    sender = 'bkel2mail <bkel2mail@gmail.com>'

    headers = {
        'Content-Type': 'text/html; charset=utf-8',
        'Content-Disposition': 'inline',
        'Content-Transfer-Encoding': '8bit',
        'From': sender,
        'To': receiver,
        'Subject': subject,
    }

    msg = ''
    for key, value in headers.items():
        msg += "%s: %s\n" % (key, value)

    msg += "\n%s\n"  % (body)

    try:
       server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
       server.login('bkel2mail@gmail.com', '<PASSWORD>')
       server.sendmail(sender, receiver, msg.encode("utf8"))
    except smtplib.SMTPException:
       logger.error("Error sending email for " + receiver)

conn = sqlite3.connect(path + '/database.db')

cursor = conn.execute("SELECT * from users")

for row in cursor:
    id = row[0]
    email = row[1]
    token = row[2]
    sentID = row[3]
    
    userid = getUserid(token)
    
    if userid != None:
        noti = getNotification(token, userid)
        if noti != None:
            for messages in noti:
                if str(messages['id']) not in sentID:
                    sentID += str(messages['id']) + ','

                    subject = ''
                    if messages['subject'] != None:
                        subject = messages['subject']
                    else:
                        subject = 'Tin nhắn mới từ ' + messages['userfromfullname']

                    body = messages['fullmessagehtml']
                    if body == '':
                        body = messages['fullmessage']

                    conn.execute("PRAGMA journal_mode=WAL")
                    conn.execute("UPDATE users set sentID = '" + sentID  + "' where id = " + str(id))
                    conn.commit()
                    sendNotification(email, subject, body)

conn.close()
