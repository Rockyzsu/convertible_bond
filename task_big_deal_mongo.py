# -*-coding=utf-8-*-

# @Time : 2019/4/4 17:08
# @File : task_cb_deal.py
# 获取每天的大单数据

from big_deal import BigDeal
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
        obj = BigDeal()
        obj.loop_date()

        ts.close_apis(cons)