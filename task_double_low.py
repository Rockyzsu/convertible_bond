# -*-coding=utf-8-*-

# @Time : 2019/10/19 14:56
# @File : task_double_low.py
import tushare as ts
import datetime
from filterbond import main

today = datetime.datetime.now().strftime('%Y-%m-%d')
cons=ts.get_apis()

if __name__=='__main__':
    if ts.is_holiday(today):
        ts.close_apis(cons)
        exit()

    else:
        main()
        ts.close_apis(cons)