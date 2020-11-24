# -*-coding=utf-8-*-

# @Time : 2019/10/19 14:13
# @File : big_deal_msg.py

# 获取大单并发送前10的到手机
from bigdeal import BigDeal


def main():
    obj = BigDeal()
    obj.analysis(head=15)


if __name__ == '__main__':
    main()
