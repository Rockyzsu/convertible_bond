# -*-coding=utf-8-*-

# @Time : 2019/4/24 16:55
# @File : task_zz_drop_than_zg.py
from configure.util import notify
from configure.settings import DBSelector, send_from_aliyun
import numpy as np
from common.BaseService import BaseService

# 统计每天转债跌得比正股多的
# 重构 2020-11-13


class DataFinder(object):

    def __init__(self):
        DB = DBSelector()
        self.con = DB.get_mysql_conn('db_stock', 'qq')
        self.cursor = self.con.cursor()

    def zz_data(self):

        zz_than_zg = 'select count(*) from tb_bond_jisilu WHERE `正股涨跌幅`>=`可转债涨幅` and `正股涨跌幅`<=0'
        minus_count_cmd = 'select count(*) from tb_bond_jisilu where `可转债涨幅`<0'
        plug_count_cmd = 'select count(*) from tb_bond_jisilu where `可转债涨幅`>=0'

        self.cursor.execute(zz_than_zg)
        zz_than_zg_count = self.cursor.fetchone()[0]

        self.cursor.execute(minus_count_cmd)
        minus_count = self.cursor.fetchone()[0]

        self.cursor.execute(plug_count_cmd)
        plug_count = self.cursor.fetchone()[0]

        search_sql = 'select `溢价率` from `tb_bond_jisilu`'
        self.cursor.execute(search_sql)

        content = self.cursor.fetchall()
        data = []
        for item in content:
            data.append(item[0])
        np_data = np.array(data)

        return np_data, zz_than_zg_count, plug_count, minus_count

    def update_data(self, t_value):
        update_sql = 'insert into tb_bond_avg_yjl (Date,溢价率均值,溢价率最大值,溢价率最小值,溢价率中位数,转债数目) values (%s,%s,%s,%s,%s,%s)'
        try:
            self.cursor.execute(update_sql, t_value)

        except Exception as e:
            print(e)
            notify('邮件发送失败', f'{self.__class__}:{e}')
            self.con.rollback()
        else:
            self.con.commit()

    def udpate_analysis(self, current, zz_than_zg_count, plug_count, minus_count):
        # 写入数据库
        insert_sql = 'insert into tb_bond_analysis (date,转债跌大于正股数量,可转债涨幅大于0,可转债涨幅小于0) values (%s,%s,%s,%s)'
        try:
            self.cursor.execute(insert_sql, (current, zz_than_zg_count, plug_count, minus_count))
        except Exception as e:
            notify('邮件发送失败', f'{self.__class__}:{e}')
            self.con.rollback()
        else:
            self.con.commit()

    def get_all_zz(self):
        cal_query = 'select `可转债涨幅`,`可转债名称` from tb_bond_jisilu'
        self.cursor.execute(cal_query)
        return self.cursor.fetchall()


class KZZCompareZG(BaseService):

    def __init__(self, logpath='log/zz_diff_zg'):
        super(KZZCompareZG, self).__init__(logpath)
        self.datasource = DataFinder()

    def find_zz_zg_diff(self):

        np_data, zz_than_zg_count, plug_count, minus_count = self.datasource.zz_data()

        t_value = self.calculate(np_data, self.today)
        self.datasource.update_data(t_value=t_value)
        result_dict = self.all_zz_dict()

        content_dict = {
            "zz_than_zg_count": zz_than_zg_count,
            "plug_count": plug_count,
            "minus_count": minus_count,
        }
        content_dict = self.convertor(result_dict, content_dict)
        self.send_mail(content_dict)
        self.datasource.udpate_analysis(self.today, zz_than_zg_count, plug_count, minus_count)

    def all_zz_dict(self):
        result_dict = {}

        for i in self.datasource.get_all_zz():
            result_dict[i[1]] = i[0]

        return result_dict

    def calculate(self, np_data, current):
        max_value = np.round(np_data.max(), 2)
        min_value = np.round(np_data.min(), 2)
        mean = np.round(np_data.mean(), 2)
        median = np.round(np.median(np_data), 2)
        count = len(np_data)
        t_value = (current, float(mean), float(max_value), float(min_value), float(median), count)
        return t_value

    def convertor(self, result_dict, content_dict):
        '''
        统计数据
        :param result_dict:
        :return:
        '''
        sort_result = list(sorted(result_dict.items(), key=lambda x: x[1], reverse=False))
        fall_name = sort_result[0][0]
        raise_name = sort_result[-1][0]
        result_list = list(result_dict.values())
        cal_result_np = np.array(result_list)
        large_than_zero = len(cal_result_np[cal_result_np >= 0])
        total_len = len(cal_result_np)
        raise_ratio = round(large_than_zero / total_len * 100, 2)
        max_v = cal_result_np.max()
        min_v = cal_result_np.min()
        mean = round(cal_result_np.mean(), 2)
        median = round(np.median(cal_result_np), 2)
        ripple_ratio = round(cal_result_np.var(), 2)

        content_dict_new = {
            "raise_ratio": raise_ratio,

            "max_v": max_v,
            "min_v": min_v,
            "mean": mean,
            "median": median,
            "raise_name": raise_name,
            "fall_name": fall_name,
            "ripple_ratio": ripple_ratio,
        }
        content_dict.update(content_dict_new)
        return content_dict

    def send_mail(self, content_dict):
        current = ''
        title = '{}转债跌大于正股数：{}'.format(current, content_dict["zz_than_zg_count"])
        content = f'<p>转债上涨比例：<font color="red">{content_dict["raise_ratio"]}</font></p>' \
                  f'<p>转债跌>正股数: <font color="red">{content_dict["zz_than_zg_count"]}</font></p>' \
                  f'可转债涨幅>=0： <font color="red">{content_dict["plug_count"]}</font></p>' \
                  f'可转债涨幅<0： <font color="red">{content_dict["minus_count"]}</font></p>' \
                  f'涨幅最大值：<font color="red">{content_dict["max_v"]}</font> 属于<font color="red">{content_dict["raise_name"]}</font></p>' \
                  f'涨幅最小值：<font color="red">{content_dict["min_v"]}</font> 属于<font color="red">{content_dict["fall_name"]}</font></p>' \
                  f'涨幅均值：<font color="red">{content_dict["mean"]}</font></p>' \
                  f'涨幅中位数：<font color="red">{content_dict["median"]}</font></p>' \
                  f'涨幅波动的方差：<font color="red">{content_dict["ripple_ratio"]}</font></p>'

        try:
            send_from_aliyun(title, content, types='html')
        except Exception as e:
            notify('邮件发送失败', f'{self.__class__}:{e}')
            self.logger.error(e)


def main():
    kzz = KZZCompareZG()
    kzz.find_zz_zg_diff()


if __name__ == '__main__':
    main()
