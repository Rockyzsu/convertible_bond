# -*-coding=utf-8-*-

# @Time : 2019/4/24 16:55
# @File : task_zz_drop_than_zg.py
from bond_statistics import find_zz_zg_diff
import tushare as ts
import datetime

today = datetime.datetime.now().strftime('%Y-%m-%d')
cons=ts.get_apis()

if __name__=='__main__':
    if ts.is_holiday(today):
        ts.close_apis(cons)
        exit()

    else:
        # TODO
        find_zz_zg_diff()

        ts.close_apis(cons)