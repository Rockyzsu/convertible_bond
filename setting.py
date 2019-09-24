# -*-coding=utf-8-*-
# 常用的配置信息

import datetime
import logging
import smtplib
import time
from email.mime.text import MIMEText
from sqlalchemy import create_engine
import os
import itchat
import json
import pymysql
import tushare as ts
import config
import random
from email_list import email_list, email_list1
from email.mime.text import MIMEText
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.utils import parseaddr, formataddr
import redis

cfg_file = os.path.join(os.path.dirname(__file__), 'data.cfg')
with open(cfg_file, 'r') as f:
    json_data = json.load(f)

# 本地用户
MYSQL_HOST = json_data['MYSQL_HOST']
MYSQL_PORT = json_data['MYSQL_PORT']
MYSQL_USER = json_data['MYSQL_USER']
MYSQL_PASSWORD = json_data['MYSQL_PASSWORD']

MYSQL_USER_Ali = json_data['MYSQL_USER_Ali']

MYSQL_PASSWORD_Ali = json_data['MYSQL_PASSWORD_Ali']
MYSQL_HOST_Ali = json_data['MYSQL_HOST_Ali']

MYSQL_REMOTE_USER = json_data['MYSQL_REMOTE_USER']
MYSQL_REMOTE = json_data['MYSQL_REMOTE']

REDIS_HOST = 'localhost'
LOGIN_EMAIL_USER = json_data['LOGIN_EMAIL_USER']
LOGIN_EMAIL_PASS = json_data['LOGIN_EMAIL_PASSWORD']
SMTP_HOST = json_data['SMTP_HOST']
FROM_MAIL = json_data['FROM_MAIL']
TO_MAIL = json_data['TO_MAIL']
Ali_DB = json_data['Ali_DB']
EMAIL_USER_XT = json_data['EMAIL_USER_XT']

MYSQL_XGD_HOST = json_data['MYSQL_XGD_HOST']
MYSQL_XGD_USER = json_data['MYSQL_XGD_USER']
MYSQL_XGD_PASSWORD = json_data['MYSQL_XGD_PASSWORD']
MYSQL_XGD_PORT = json_data['MYSQL_XGD_PORT']
EMAIL_USER_ALY = json_data['EMAIL_USER_ALY']
LOGIN_EMAIL_ALY_PASS = json_data['LOGIN_EMAIL_ALY_PASS']
DATA_PATH = json_data['DATA_PATH']


def get_engine(db, local=True):
    '''

    :param db:
    :param local:
    :return:
    '''
    if local:
        engine = create_engine(
            'mysql+pymysql://{}:{}@{}:{}/{}?charset=utf8'.format(MYSQL_USER, MYSQL_PASSWORD, MYSQL_HOST,
                                                                 MYSQL_PORT, db))
    else:
        db = Ali_DB
        engine = create_engine(
            'mysql+pymysql://{}:{}@{}:{}/{}?charset=utf8'.format(MYSQL_USER_Ali, MYSQL_PASSWORD_Ali, MYSQL_HOST_Ali,
                                                                 MYSQL_PORT, db))
    return engine


def get_mysql_conn(db, local):
    '''

    :param db: 数据库名字
    :param local: 本地还是远程还是xgd
    :return:返回conn
    '''
    if local == 'local':
        conn = pymysql.connect(MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, db, charset='utf8')

    elif local == 'XGD':
        conn = pymysql.connect(host=MYSQL_XGD_HOST, port=int(MYSQL_XGD_PORT), user=MYSQL_XGD_USER,
                               password=MYSQL_XGD_PASSWORD, db=db, charset='utf8')

    elif local == 'ali':
        db = Ali_DB
        conn = pymysql.connect(MYSQL_HOST_Ali, MYSQL_USER_Ali, MYSQL_PASSWORD_Ali, db, charset='utf8')

    return conn


class WechatSend:
    def __init__(self, name):
        # name为微信要发送的人的微信名称
        self.name = name
        itchat.auto_login(hotReload=True)
        account = itchat.get_friends(self.name)
        self.toName = None
        for i in account:
            if i[u'PYQuanPin'] == self.name:
                self.toName = i['UserName']
        if not self.toName:
            print('please input the right person name')

    def send_price(self, name, real_price, real_percent, types):
        content = name + ' ' + str(real_price) + ' ' + str(real_percent) + ' percent ' + types
        itchat.send(content, toUserName=self.toName)

    def send_ceiling(self, name, vol):
        current = datetime.datetime.now().strftime('%Y %m %d %H:%M %S')
        content = '{} Warning {} : ceiling volume is {}'.format(current, name, vol)
        itchat.send(content, toUserName=self.toName)

    def send_content(self, content):
        itchat.send(content, toUserName=self.toName)


def sendmail_many(content, subject):
    '''
    发送邮件
    '''
    # obj = ClsLogger(__file__)

    username = LOGIN_EMAIL_USER
    password = LOGIN_EMAIL_PASS
    smtp_host = SMTP_HOST
    smtp = smtplib.SMTP(smtp_host)
    TO_MAIL = ','.join(email_list)
    # smtp.ehlo()
    # smtp.starttls()
    try:
        smtp.login(username, password)
        msg = MIMEText(content, 'plain', 'utf-8')
        msg['from'] = FROM_MAIL
        msg['to'] = TO_MAIL
        msg['subject'] = subject
        smtp.sendmail(msg['from'], msg['to'], msg.as_string())
        smtp.quit()
    except Exception as e:
        # obj.error(e)
        print('>>>>>{}'.format(e))


def sendmail(content, subject):
    '''
    发送邮件
    '''
    # obj = ClsLogger(__file__)

    username = LOGIN_EMAIL_USER
    password = LOGIN_EMAIL_PASS
    smtp_host = SMTP_HOST
    smtp = smtplib.SMTP(smtp_host)
    # smtp.ehlo()
    # smtp.starttls()
    try:
        smtp.login(username, password)
        msg = MIMEText(content, 'plain', 'utf-8')
        msg['from'] = FROM_MAIL
        msg['to'] = TO_MAIL
        msg['subject'] = subject
        smtp.sendmail(msg['from'], msg['to'], msg.as_string())
        smtp.quit()
    except Exception as e:
        # obj.error(e)
        print('>>>>>{}'.format(e))


class ClsLogger:
    def __init__(self, file_name):
        self.logger = logging.getLogger('default')
        self.logger.setLevel(logging.DEBUG)
        profix = os.path.splitext(file_name)[0]
        file_path = os.path.join(os.path.dirname(__file__), profix + '.log')
        f_handler = logging.FileHandler(file_path)

        f_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('[%(asctime)s][%(filename)s][line: %(lineno)d] [%(levelname)s] ## %(message)s')

        f_handler.setFormatter(formatter)
        self.logger.addHandler(f_handler)

    def debug(self, content):
        self.logger.debug(content)

    def info(self, content):
        self.logger.info(content)

    def warning(self, content):
        self.logger.warning(content)

    def error(self, content):
        self.logger.error(content)


def llogger(filename):
    pre_fix = os.path.splitext(filename)[0]
    # 创建一个logger
    logger = logging.getLogger('mylogger')
    logger.setLevel(logging.DEBUG)

    # 创建一个handler，用于写入日志文件
    fh = logging.FileHandler(pre_fix + '.log')

    # 再创建一个handler，用于输出到控制台
    ch = logging.StreamHandler()

    # # 定义handler的输出格式
    formatter = logging.Formatter(
        '[%(asctime)s][Filename: %(filename)s][line: %(lineno)d][%(levelname)s] :: %(message)s')

    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    # 给logger添加handler
    logger.addHandler(fh)
    logger.addHandler(ch)

    return logger


def _format_addr(s):
    name, addr = parseaddr(s)
    return formataddr((Header(name, 'utf-8').encode(), addr))


# 使用阿里云发送
def send_aliyun(title, content, types='plain'):
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    username = EMAIL_USER_ALY  # 阿里云
    password = LOGIN_EMAIL_ALY_PASS
    logger = llogger('send_mail_aliyun')
    obj = smtplib.SMTP()
    msg = MIMEText(content, types, 'utf-8')
    subject = title
    msg['Subject'] = Header(subject, 'utf-8')
    msg['From'] = _format_addr('{} <{}>'.format('datasender', username))
    msg['To'] = TO_MAIL

    try:
        obj.connect('smtp.qiye.aliyun.com', 25)
        obj.login(username, password)
        obj.sendmail(username, TO_MAIL, msg.as_string())

    except Exception as e:
        logger.error(e)
        logger.error(TO_MAIL)
        time.sleep(10 + random.randint(1, 5))
        obj = smtplib.SMTP()
        obj.connect('smtp.qiye.aliyun.com', 25)
        obj.login(username, password)
        obj.sendmail(username, TO_MAIL, msg.as_string())


def sender_139_jsl(title, content, types='plain'):
    r = redis.StrictRedis('10.18.6.46', db=10, decode_responses=True)
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    key = 'email_{}'.format(today)
    for i in email_list:
        r.sadd(key, i)

    username = EMAIL_USER_XT
    password = LOGIN_EMAIL_PASS
    logger = llogger('send_mail')
    obj = smtplib.SMTP()

    try:
        username = 'datasender@30daydo.com'
        obj.connect('smtp.qiye.aliyun.com', 25)
        obj.login(username, 'Jsl12345')
        # for to_name in email_list1:
        # to_='xtgotousa@139.com'
        # send_set = set(email_list)

        failed_dict = {}
        while 1:
            # for name in send_set:
            name = r.srandmember(key)

            if name is None:
                break

            msg = MIMEText(content, types, 'utf-8')
            subject = title
            msg['Subject'] = Header(subject, 'utf-8')
            msg['From'] = _format_addr('{} <{}>'.format('datasender', username))
            msg['To'] = name
            # print(name)
            # to_list=[to_]+email_list1
            # msg['Bcc']=','.join(email_list1)
            # print(f'send to {to_name}')
            try:
                obj.sendmail(username, [name], msg.as_string())
            except Exception as e:
                logger.error(e)
                logger.error(name)
                time.sleep(10 + random.randint(1, 5))

                failed_dict.setdefault(name, 0)
                failed_dict[name] += 1

                if failed_dict[name] >= 2:
                    logger.error(f'{name} failed for 3 times, remove')
                    r.srem(key, name)
                obj = smtplib.SMTP()

                obj.connect('smtp.qiye.aliyun.com', 25)
                obj.login(username, password)

                continue

            else:
                logger.info(f'{name} has been sent')
                r.srem(key, name)
                time.sleep(10 + random.randint(1, 5))


    except Exception as e:
        logger.error(e)
        obj.connect('smtp.qiye.aliyun.com', 25)
        obj.login(username, password)


def trading_time():
    '''

    :return:
    收盘：1
    盘中：0
    未开盘：-1
    '''
    current = datetime.datetime.now()
    start = datetime.datetime(current.year, current.month, current.day, 9, 23, 0)
    noon_start = datetime.datetime(current.year, current.month, current.day, 12, 58, 0)

    morning_end = datetime.datetime(current.year, current.month, current.day, 11, 31, 0)
    # 收盘
    end = datetime.datetime(current.year, current.month, current.day, 15, 2, 5)
    if current > start and current < morning_end:
        return 0

    elif current > noon_start and current < end:
        return 0

    elif current > end:
        return 1

    elif current < start:
        return -1

    elif current >= morning_end and current <= noon_start:
        return -1


def is_holiday():
    current = datetime.datetime.now().strftime('%Y-%m-%d')
    return ts.is_holiday(current)


def push_redis():
    r = redis.StrictRedis('10.18.6.46', db=10, decode_responses=True)
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    key = 'email_{}'.format(today)
    for i in email_list:
        r.sadd(key, i)


if __name__ == '__main__':
    #     msg=WechatSend(u'wei')
    #     msg.send_price('hsdq',12,12,'sell')
    # print(FROM_MAIL)
    # mylogger('test.log','just for test')
    # trading_time()
    # sendmail('content--------', 'subject------')
    push_redis()
