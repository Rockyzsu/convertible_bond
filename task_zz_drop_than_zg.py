# -*-coding=utf-8-*-

# @Time : 2019/4/24 16:55
# @File : task_zz_drop_than_zg.py
from bond_statistics import find_zz_zg_diff
import tushare as ts
import datetime

today = datetime.datetime.now().strftime('%Y-%m-%d')

if __name__=='__main__':
    find_zz_zg_diff()