# -*-coding=utf-8-*-

# @Time : 2019/10/19 13:47
# @File : weekly_drop.py

# 每周跌幅最多的
from filter_bond import weekly_drop_rank
import tushare as ts
import datetime

today = datetime.datetime.now().strftime('%Y-%m-%d')
cons=ts.get_apis()

def main():
    if ts.is_holiday(today):
        ts.close_apis(cons)
        exit()

    else:
        weekly_drop_rank(current=True) # 正常运行时current = True
        ts.close_apis(cons)

if __name__=='__main__':
    main()
