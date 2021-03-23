# -*-coding=utf-8-*-
# @Time : 2019/9/2 9:35
# @File : task_jsler_double_low.py
# 发送邮件的,集思录双低

from datahub.jsl_double_low import JslCbDoubleLow
def main():
    app = JslCbDoubleLow(remote='qq')
    app.jsl_cb_double_low_monitor()


if __name__ == '__main__':
    main()
