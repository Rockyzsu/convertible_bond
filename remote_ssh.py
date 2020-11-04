# -*- coding: utf-8 -*-
# @Time : 2020/11/4 8:58
# @File : remote_ssh.py
# @Author : Rocky C@www.30daydo.com
from settings import ssh_server, _json_data
import pymysql

user = _json_data['mysql']['qq']['user']
password = _json_data['mysql']['qq']['password']

local_port = 8887
server = ssh_server(local_port)
server.start()
conn = pymysql.connect(
    host='127.0.0.1',
    port=local_port,
    user=user,
    password=password,
    db='db_stock'
)

cursor = conn.cursor()
cursor.execute('select count(*) from tb_cb_index')
ret = cursor.fetchall()
print(ret)
conn.close()
server.stop()
print('stop')
