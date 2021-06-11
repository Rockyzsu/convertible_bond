# -*-coding=utf-8-*-

# @Time : 2019/4/4 17:08
# @File : task_cb_deal.py
# 获取每天的大单数据

from bigdeal import BigDeal

use_today = False # 是否今天最新数据
def main():
    app = BigDeal()
    app.fetch_bigdeal(today=use_today)


if __name__ == '__main__':
    main()
