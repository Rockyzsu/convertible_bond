# 热门正股推送

import sys

import pandas as pd

sys.path.append("..")
from configure.settings import DBSelector
import datetime
from configure.util import send_from_aliyun_ssl
def get_zg_info():
    conn = DBSelector().get_mysql_conn('db_stock','qq')
    cursor = conn.cursor() 
    query = 'select 正股代码 from tb_bond_jisilu'
    cursor.execute(query)
    data = cursor.fetchall()
    zg_code_list = []
    for item in data:
        zg_code_list.append(item[0])

    return zg_code_list

def main():
    zg_code_list =  get_zg_info()
    get_hot_dfcf(zg_code_list)

def get_hot_dfcf(zg_code_list):
    today = datetime.datetime.now().strftime('%Y%m%d')
    conn = DBSelector().get_mysql_conn('db_zdt','qq')
    cursor = conn.cursor()
    query = 'select 代码,名称,涨停统计,入选理由,所属行业 from {}_strong where 代码 in ({})'.format(today,','.join(zg_code_list))
    cursor.execute(query)
    data = cursor.fetchall()
    msg_list = []
    for item in data:
        code = item[0]
        name = item[1]
        zt_count = item[2]
        reason = item[3]
        industry = item[4]
        obj = {}
        obj['名称'] = name
        obj['涨停'] = zt_count
        obj['原因'] = reason
        obj['行业'] = industry
        msg_list.append(obj)

    df = pd.DataFrame(msg_list)
    send_content = df.to_html(index=False, border=1, justify='center')
    send_from_aliyun_ssl('{}热门正股'.format(today), send_content, types='html')



if __name__ == "__main__":
    weekday = datetime.datetime.now().weekday()
    if weekday == 5 or weekday == 6:
        # 周六周日不执行
        print('today is weekend')
    else:
        main()
