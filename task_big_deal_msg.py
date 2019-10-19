# -*-coding=utf-8-*-

# @Time : 2019/10/19 14:13
# @File : big_deal_msg.py

# 获取大单并发送前10的到手机
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
        obj.analysis(head=15)

        ts.close_apis(cons)
