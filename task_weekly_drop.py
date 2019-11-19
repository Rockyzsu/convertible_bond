# -*-coding=utf-8-*-

# @Time : 2019/10/19 13:47
# @File : weekly_drop.py

# 每周跌幅最多的
from filter_bond import weekly_drop_rank
import tushare as ts
import datetime

today = datetime.datetime.now().strftime('%Y-%m-%d')
cons=ts.get_apis()


if __name__=='__main__':

    # if ts.is_holiday(today):
    #     ts.close_apis(cons)
    #     exit()
    #
    # else:
    #     TODO
        weekly_drop_rank()

        ts.close_apis(cons)