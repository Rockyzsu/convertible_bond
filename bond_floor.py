# 计算债底 大概每个月更新一次
import tushare as ts
from setting import get_engine, get_mysql_conn
import pandas as pd
# api = ts.get_apis()
# code = '123012'
engine = get_engine('db_bond', 'local')


def get_history_data(code):
    df = ts.get_k_data(code=code, start='2017-10-01')
    min_close = df['close'].min()
    min_date = df[df['close'] == min_close]['date'].values[0]
    try:
        df.to_sql(f'cb_{code}', con=engine, if_exists='replace')
    except Exception as e:
        print(e)
        return 0, 0
    else:
        return min_close, min_date


def get_code():
    engine = get_engine('db_stock', 'local')
    df = pd.read_sql('tb_bond_kind_info', con=engine)
    code_list = list(df['可转债代码'].values)
    return code_list


def main():
    con = get_mysql_conn('db_stock', 'local')
    cursor = con.cursor()
    code_list = get_code()
    update_sql = '''
    update tb_bond_kind_info set `最小值` = %s, `最小值-发生时间` = %s where `可转债代码` = %s
    '''
    for i in code_list:
        min_close, min_date = get_history_data(i)
        try:
            cursor.execute(update_sql, (float(min_close), min_date, i))
        except Exception as e:
            print(e)
            con.rollback()
        con.commit()
    con.close()

main()
