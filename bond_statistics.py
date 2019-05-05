# -*-coding=utf-8-*-
'''
http://30daydo.com
Contact: weigesysu@qq.com
'''

import datetime
import pymongo
from send_mail import sender_139
from scipy import stats
import tushare as ts
from setting import get_engine, get_mysql_conn,llogger
import pandas as pd
import numpy as np
# from filter_stock import Filter_Stock
# 筛选出 新股 的可转债
# current = datetime.datetime.now()
# last_week = current + datetime.timedelta(days=7 * -2)
# conn = get_engine('db_stock')
# df = pd.read_sql('tb_bond_jisilu', con=conn)
# code_list = df['正股代码'].values
# kzz_code_list = df['可转债代码'].values
# kzz_name_list = df['可转债名称'].values
# db = pymongo.MongoClient('10.18.6.46', port=27001)

logger = llogger('log/'+'bond_statistic')
# 获取次新股的可转债数据
def get_zhenggu():
    obj = Filter_Stock()
    ns_df = obj.get_new_stock('2016', '2018')
    zg_code = ns_df[ns_df['code'].isin(code_list)]['code'].values

    ret_df = df[df['正股代码'].isin(zg_code)]
    ret_df = ret_df.reset_index(drop=True)
    ret_df.to_sql('tb_new_stock_bond', con=conn, if_exists='replace')


# 筛选出每周 （月）涨幅排名倒数的10个
def sort_top_raise(count=10, ktype='W', reverse=True):
    p_list = [get_percentage(code, ktype) for code in kzz_code_list]
    kzz_dict = dict(zip(kzz_name_list, p_list))

    # 去重未上市的
    kzz_dict_copy = kzz_dict.copy()
    for k, v in kzz_dict_copy.items():
        if v == -999:
            del kzz_dict[k]

    top_raise_list = sorted(kzz_dict.items(), key=lambda x: x[1], reverse=True)
    return top_raise_list


def get_percentage(code, ktype):
    last_week_str = last_week.strftime('%Y-%m-%d')
    count = 0
    retry = 5
    # 重试5次
    while 1:
        try:
            df = ts.get_k_data(code, ktype=ktype, start=last_week_str)
        except Exception as e:
            print(e)
            count += 1
            print('retry >> {}'.format(count))
            if count == retry:
                df = pd.DataFrame()
                break
            else:
                continue
        else:
            break

    # 未上市
    if len(df) == 0:
        percentage = -999
    else:
        weeks_close = df['close'].values

        if len(weeks_close) == 2:
            percentage = round((weeks_close[1] - weeks_close[0]) / weeks_close[0] * 100, 2)
        else:
            percentage = -999

    return percentage


# 将list保存为mongo
def save_list_mongo(source_list):
    current = datetime.datetime.now()
    title = current.strftime('%Y-%m-%d') + '可转债周涨幅的前10和后10'
    top10 = source_list[:10]
    last10 = source_list[-10:]
    top_str = ['{} : {}'.format(i[0], i[1]) for i in top10]
    last_str = ['{} : {}'.format(i[0], i[1]) for i in last10[::-1]]
    top_str = '\n'.join(top_str)
    last_str = '\n'.join(last_str)
    content = '跌幅前10:::\n' + last_str + '\n涨幅前10:::\n' + top_str
    try:
        sender_139(title, content)
    except Exception as e:
        print(e)

    d = dict(source_list)
    d['updated'] = current

    try:
        db['db_parker']['kzz_weekly_raise'].insert(d)
    except Exception as e:
        print(e)


# 导出一些基本数据，可转债的
def convert_name_db():
    conn = get_mysql_conn('db_stock', 'local')
    cursor = conn.cursor()
    query_cmd = '''
    select * from tb_bond_jisilu
    '''

    cursor.execute(query_cmd)
    ret = cursor.fetchall()

    for item in ret:
        name = item[1]
        code = item[0]
        zg_name = item[3]
        zg_code = item[4]
        grade = item[17]


        get_area = '''
        select area from tb_basic_info where code = %s
        '''

        cursor.execute(get_area,zg_code)
        result= cursor.fetchone()[0]


        insert_cmd = '''
        insert into tb_bond_kind_info (可转债名称,可转债代码,正股名称,正股代码,评级,地区,更新时间) values(%s,%s,%s,%s,%s,%s,%s)
        '''

        cursor.execute(insert_cmd,(name,code,zg_name,zg_code,grade,result,datetime.datetime.now().strftime('%Y-%m-%d')))

    conn.commit()

# 根据评级找出一些低于均值的个债
def find_lower_bond():
    # 和均值的比较因子，正常为1

    percent = 1
    con = get_mysql_conn('db_stock','local')
    cursor = con.cursor()
    query_avg_sql = '''
    SELECT `评级`,count(*) as n,round(AVG(`最小值`),2) as `均值` FROM `tb_bond_kind_info` GROUP BY `评级`
    '''
    cursor.execute(query_avg_sql)
    ret = cursor.fetchall()
    d= {}
    for item in ret:
        d[item[0]]=item[2]

    print(d)
    query_all_bond_sql = '''
    select `可转债代码`,`评级`,`可转债价格`,`可转债名称` from tb_bond_jisilu
    '''
    cursor.execute(query_all_bond_sql)
    total_bond_ret = cursor.fetchall()
    for item in total_bond_ret:
        if item[2] <= percent * d.get(item[1]):
            ration = round((item[2]-d.get(item[1]))/d.get(item[1])*100,2)

            print(f'{item[3]}:评级{item[1]},当前价格：{item[2]},低于比例{ration}')

    print('done')

# 统计每天转债跌得比正股多的
def find_zz_zg_diff():
    current=datetime.date.today().strftime('%Y-%m-%d')
    if ts.is_holiday(current):
        logger.info('假期')
        return

    # engine=get_engine('db_stock','local')
    # df = pd.read_sql('tb_bond_jisilu',con=engine)
    # df[(df['正股涨跌幅']<=0) & (df['正股涨跌幅']>=df['可转债涨幅'])]
    con=get_mysql_conn('db_stock','local')
    cursor=con.cursor()
    query_cmd = 'select count(*) from tb_bond_jisilu WHERE `正股涨跌幅`>=`可转债涨幅` and `正股涨跌幅`<=0'
    minus_count_cmd = 'select count(*) from tb_bond_jisilu where `可转债涨幅`<0'
    plug_count_cmd = 'select count(*) from tb_bond_jisilu where `可转债涨幅`>=0'

    cursor.execute(query_cmd)
    get_count = cursor.fetchone()
    num=get_count[0]

    cursor.execute(minus_count_cmd)
    minus_count=cursor.fetchone()[0]


    cursor.execute(plug_count_cmd)
    plug_count=cursor.fetchone()[0]

    title='{} 转债跌大于正股数 {}'.format(current,num)
    content='转债跌大于正股数 {}\n可转债涨幅大于0:\t{}\n可转债涨幅小于0:\t{}'.format(num,plug_count,minus_count)
    try:
        sender_139(title,content)
    except Exception as e:
        logger.error(e)
    else:
        logger.info('发送成功')
        logger.info(content)

    # 写入数据库
    insert_sql = 'insert into tb_bond_analysis (date,转债跌大于正股数量,可转债涨幅大于0,可转债涨幅小于0) values (%s,%s,%s,%s)'
    try:
        cursor.execute(insert_sql,(current,num,plug_count,minus_count))
        con.commit()
    except Exception as e:
        logger.error(e)
        con.rollback()
    else:
        logger.info('入库成功')

    try:
        search_sql = 'select `溢价率` from `tb_jsl_{}`'.format(date_str)
        cursor.execute(search_sql)

    except Exception as e:
        print(e)

    else:
        content = cursor.fetchall()
        data = []
        for item in content:
            data.append(item[0])

    try:
        search_sql = 'select `溢价率` from `tb_bond_jisilu`'
        cursor.execute(search_sql)

    except Exception as e:
        print(e)

    else:
        content = cursor.fetchall()
        data = []
        for item in content:
            data.append(item[0])

        np_data = np.array(data)
        max_value = np.round(np_data.max(), 2)
        min_value = np.round(np_data.min(), 2)
        mean = np.round(np_data.mean(), 2)
        median = np.round(np.median(np_data), 2)
        count = len(np_data)
        t_value = (current, float(mean), float(max_value), float(min_value), float(median), count)
        print(t_value)
        update_sql = 'insert into tb_bond_avg_yjl (Date,溢价率均值,溢价率最大值,溢价率最小值,溢价率中位数,转债数目) values (%s,%s,%s,%s,%s,%s)'
        # con=get_mysql_conn('d')
        try:
            cursor.execute(update_sql, t_value)
            con.commit()

        except Exception as e:
            print(e)
            con.rollback()
        else:
            print('update')


# 查看历史数据
def find_zz_zg_diff_history():

    con = get_mysql_conn('db_jisilu', 'local')
    cursor = con.cursor()
    current = datetime.date.today()
    days=60
    tb_name ='tb_jsl_{}'
    num_list =[]
    for i in range(days):

        start = (current+datetime.timedelta(days=-1*i)).strftime("%Y-%m-%d")
        name = tb_name.format(start)

        query_cmd = 'select count(*) from `{}` WHERE `正股涨跌幅`>=`可转债涨幅` and `正股涨跌幅`<=0'.format(name)
        try:
            cursor.execute(query_cmd)
        except Exception as e:
            print(e)
            con.rollback()
            continue

        else:
            get_count = cursor.fetchone()
            num = get_count[0]
            num_list.append((start,num))
    print(num_list)
    # print(sorted(num_list,key=lambda x:x[1],reverse=True))
    con.close()

    con2 = get_mysql_conn('db_stock','local')
    cur=con2.cursor()
    insert_sql = 'insert into `tb_zz_more_drop_zg` (date,number) values (%s,%s)'
    try:
        cur.executemany(insert_sql,(num_list))
        con2.commit()
    except Exception as e:
        print(e)
        con2.rollback()
    else:
        print('入库成功')


def avg_yjl_history():
    con=get_mysql_conn('db_jisilu','local')
    con2=get_mysql_conn('db_stock','local')

    cursor=con.cursor()
    cursor2=con2.cursor()

    start = datetime.datetime(2019,2,25)
    update_sql = 'insert into tb_bond_avg_yjl (Date,溢价率均值,溢价率最大值,溢价率最小值,溢价率中位数,转债数目) values (%s,%s,%s,%s,%s,%s)'
    while 1:
        if start>=datetime.datetime.now():
            break
        date_str = start.strftime('%Y-%m-%d')
        try:
            search_sql = 'select `溢价率` from `tb_jsl_{}`'.format(date_str)
            cursor.execute(search_sql)

        except Exception as e:
            print(e)

        else:
            content = cursor.fetchall()
            data=[]
            for item in content:
                data.append(item[0])

            np_data = np.array(data)
            max_value= np.round(np_data.max(),2)
            min_value= np.round(np_data.min(),2)
            mean = np.round(np_data.mean(),2)
            median=np.round(np.median(np_data),2)
            count=len(np_data)
            t_value=(date_str,float(mean),float(max_value),float(min_value),float(median),count)
            print(t_value)

            try:
                cursor2.execute(update_sql,t_value)
                con2.commit()

            except Exception as e:
                print(e)
                con2.rollback()
            else:
                print('update')


        finally:

            start=start+datetime.timedelta(days=1)



def main():
    # find_zz_zg_diff()
    # find_lower_bond()
    # find_zz_zg_diff()
    # find_zz_zg_diff_history()
    avg_yjl_history()

if __name__ == "__main__":
    # source_list=sort_top_raise()
    # save_list_mongo(source_list)
    # convert_name_db()
    main()
