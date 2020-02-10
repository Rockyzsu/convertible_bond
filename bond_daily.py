# -*-coding=utf-8-*-

# @Time : 2019/7/1 16:50
# @File : bond_daily.py
# 收集可转债的市场全景图
from settings import get_engine,sendmail,llogger,get_mysql_conn
import pandas as pd
import datetime
from config import token
import tushare as ts
today = datetime.datetime.now().strftime('%Y-%m-%d')
today_fmt = datetime.datetime.now().strftime('%Y%m%d')
# today='2020-02-06'
# today_fmt='20200206'
cons=ts.get_apis()
logger=llogger('log/bond_daily.log')
# ts.set_token(token)

# pro = ts.pro_api()
conn=get_mysql_conn('db_bond_daily','local')

def creat_table(day):
    tb_name = 'bond_{}'.format(day)
    create_cmd = 'create table if not exists `{tb_name}` (`date` varchar(20),`code` varchar(10) primary key,`name` varchar(16),`open` float ,' \
                 '`close` float,`high` float,`low` float,`vol` float,`amount` float) '.format(tb_name=tb_name)
    cursor = conn.cursor()
    try:
        cursor.execute(create_cmd)
        conn.commit()
    except Exception as e:
        logger.error(e)
        return False
    else:
        return True

def read_data_source(today):
    engine = get_engine('db_jisilu','local')
    try:
        df = pd.read_sql('tb_jsl_{}'.format(today),con=engine)
    except Exception as e:
        logger.error(e)

        sendmail('代码{}出错\n读取表tb_jsl_{}失败'.format('bond_daily',today),'{}'.format(today))
        return None
    else:
        return df

def np_to_py_float(d):
    try:
        d=float(d)
    except Exception as e:
        return 0
    else:
        return d

def loop_data():

    df = read_data_source(today)
    # df = read_data_source('2020-02-07')

    if not creat_table(today):
        return

    cursor = conn.cursor()

    for idx,row in df.iterrows():
        code = row['可转债代码']
        name=row['可转债名称']

        ret_df = daily(code)

        if ret_df is not None:
            try:
                ret_df = ret_df.loc[today] # loc索引 为series
            except Exception as e:
                logger.error(e)
                logger.info(code)
                continue

            if isinstance(ret_df,pd.Series):
                open = np_to_py_float(ret_df['open'])
                close = np_to_py_float(ret_df['close'])
                high = np_to_py_float(ret_df['high'])
                low = np_to_py_float(ret_df['low'])
                vol = np_to_py_float(ret_df['vol'])
                amount = np_to_py_float(ret_df['amount'])
            else:
                if len(ret_df)==1:
                    open=np_to_py_float(list(ret_df['open'].values)[0])
                    close=np_to_py_float(list(ret_df['close'].values)[0])
                    high=np_to_py_float(list(ret_df['high'].values)[0])
                    low=np_to_py_float(list(ret_df['low'].values)[0])
                    vol=np_to_py_float(list(ret_df['vol'].values)[0])
                    amount=np_to_py_float(list(ret_df['amount'].values)[0])
                else:
                    open,close,high,low,vol,amount=None,None,None,None,None,None

            insert_cmd = '''insert into `bond_{}` (`date`,`code`,`name`,`open`,`close` ,`high`,`low`,`vol`,`amount`) values (%s,%s,%s,%s,%s,%s,%s,%s,%s)
            '''.format(today)
            try:
                cursor.execute(insert_cmd,(today,code,name,open,close,high,low,vol,amount))
                conn.commit()
            except Exception as e:
                conn.rollback()
                logger.error(e)


def daily(code):
    global cons
    retry =5
    t = 0
    df=None
    while t<retry:
        try:
            df = ts.bar(code, conn=cons, freq='D', start_date=today, end_date='')
        except Exception as e:
            logger.error(e)
            cons = ts.get_apis()

            t += 1
        else:
            if df is not None and not df.empty:
                break
            else:
                # print(df)
                logger.error('重试')
                cons = ts.get_apis()
                t+=1

    return df


if __name__=='__main__':
    if ts.is_holiday(today):
        logger.info('假期')
        ts.close_apis(cons)
        exit()

    logger.info('{}-->获取每天的开高低收数据'.format(today))
    loop_data()
    ts.close_apis(cons)
