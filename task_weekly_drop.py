# -*-coding=utf-8-*-

# @Time : 2019/10/19 13:47
# @File : weekly_drop.py

# 每周跌幅最多的
from datahub.weekly_drop import WeeklyDrop
import fire


def main(current=True, type_='week'):
    WeeklyDrop().weekly_drop_rank(current=current, type_=type_)  # 正常运行时current = True


if __name__ == '__main__':
    fire.Fire(main)
