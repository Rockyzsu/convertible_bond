# -*- coding: utf-8 -*-
# @Time : 2020/11/4 0:38
# @File : generate_cb_distribution.py
# @Author : Rocky C@www.30daydo.com

# 可转债价格分布图
import datetime
import os
import time

import fire
import requests
from pyecharts.render import make_snapshot
from snapshot_selenium import snapshot
from configure.settings import DBSelector, config_dict
import pandas as pd
from pyecharts import options as opts
from pyecharts.charts import Bar
import sys
from selenium import webdriver
from pyecharts.commons.utils import JsCode
from common.BaseService import BaseService
from configure.util import read_web_headers_cookies
from datahub.jsl_login import login,headers
from configure import config

if sys.platform == 'win32':
    SELENIUM_PATH = r'C:\OneDrive\Tool\phantomjs-2.1.1-windows\phantomjs-2.1.1-windows\bin\phantomjs.exe'
    driver = None
else:
    SELENIUM_PATH = './phantomjs'
    driver = webdriver.PhantomJS(executable_path=SELENIUM_PATH)


def calc_statistics(pct):
    bigger = pct[pct >= 0].count()
    smaller = pct[pct < 0].count()
    max_id = pct.argmax()
    min_id = pct.argmin()
    avg = round(float(pct.mean()), 2)
    std = round(float(pct.std(ddof=1)), 2)
    return bigger, smaller, avg, std, max_id, min_id


def get_XY(bins, pct, label, color):
    # 分箱获取Y轴的数据

    result = pd.cut(pct, bins, ordered=True, labels=label)
    v = pd.value_counts(result)
    result_dict = {}
    for i in label:
        if i == "-90":
            j = '-20+'
        else:
            j = i
        result_dict[j] = v.loc[i]

    gte_20 = pct[pct >= 20].count()
    result_dict.update({'20+': gte_20})
    y_list = []
    for k, v in result_dict.items():
        if k.startswith('-'):
            color_ = color[0]
        else:
            color_ = color[1]

        y_list.append(opts.BarItem(
            name=str(v),
            value=int(v),
            itemstyle_opts=opts.ItemStyleOpts(color=color_),
        ))

    return result_dict, y_list


class CBDistribution(BaseService):

    def __init__(self, noon=False):
        super(CBDistribution, self).__init__()
        root_path = config_dict('data_path')
        self.noon=noon
        if self.noon:
            self.IMGAGE_PATH = os.path.join(root_path, f"{self.today}_cb_noon.png")
            self.HMTL_PATH = os.path.join(root_path, f"{self.today}_cb_noon.html")

        else:
            self.IMGAGE_PATH = os.path.join(root_path, f"{self.today}_cb.png")
            self.HMTL_PATH = os.path.join(root_path, f"{self.today}_cb.html")

        self.check_path('data')

    def get_bond_data(self):
        DB = DBSelector()
        engine = DB.get_engine('db_stock', 'qq')

        df = pd.read_sql('tb_bond_jisilu', con=engine)
        return df

    def get_XY_data(self, df):
        bins = list(range(-20, 21))
        bins.insert(0, -90)
        bins.append(90)
        label = [str(b) for b in bins[:-1]]

        pct = df['可转债涨幅']
        pct_zg = df['正股涨跌幅']

        bigger, smaller, avg, std, max_id, min_id = calc_statistics(pct)

        max_name = df.loc[max_id]['可转债名称']
        max_pct = df.loc[max_id]['可转债涨幅']
        min_name = df.loc[min_id]['可转债名称']
        min_pct = df.loc[min_id]['可转债涨幅']

        color1 = ("#228B22", "#FF0000")
        color2 = ("#009ACD", "#F4A460")

        result_dict, zz_list = get_XY(bins, pct, label, color1)
        _, zg_list = get_XY(bins, pct_zg, label, color2)

        data = {
            'max_name': max_name,
            'max_pct': max_pct,
            'min_name': min_name,
            'min_pct': min_pct,
            'zz_list': zz_list,
            'zg_list': zg_list,
            'result_dict': result_dict,
            'bigger': bigger,
            'smaller': smaller,
            'avg': avg,
            'std': std,

        }

        return data

    def download(self, url, data, retry=5):
        session = login(config.jsl_user,config.jsl_password)
        # headers,cookies = read_web_headers_cookies('jsl',headers=True,cookies=True)
        for i in range(retry):
            try:
                r = session.post(url, headers=headers, data=data)
                if not r.text or r.status_code != 200:
                    continue
                else:
                    return r
            except Exception as e:
                self.logger.info(e)
                self.notify(title=f'{self.__class__}下载失败')
                continue

        return None

    def data_parse(self, bond_list, adjust_no_use):

        cell_list = []
        for item in bond_list:
            cell_list.append(pd.Series(item.get('cell')))
        df = pd.DataFrame(cell_list)

        if adjust_no_use:

            # 类型转换 部分含有%
            df['price'] = df['price'].astype('float64')
            df['convert_price'] = df['convert_price'].astype('float64')
            df['premium_rt'] = df['premium_rt'].astype('float64')
            df['force_redeem_price'] = df['force_redeem_price'].astype('float64')


            rename_columns = {'bond_id': '可转债代码', 'bond_nm': '可转债名称',
                              'price': '可转债价格', 'stock_nm': '正股名称',
                              'stock_id': '正股代码',
                              'sprice': '正股现价',
                              'sincrease_rt': '正股涨跌幅',
                              'convert_price': '最新转股价', 'premium_rt': '溢价率',
                              'increase_rt': '可转债涨幅',
                              'convert_value': '转股价值',
                              'dblow': '双低',
                              'put_convert_price': '回售触发价', 'convert_dt': '转股起始日',
                              'short_maturity_dt': '到期时间', 'volume': '成交额(万元)',
                              'force_redeem_price': '强赎价格', 'year_left': '剩余时间',
                              # 'next_put_dt': '回售起始日',
                              'rating_cd': '评级',
                              # 'issue_dt': '发行时间',
                              # 'redeem_tc': '强制赎回条款',
                              # 'adjust_tc': '下修条件',
                              'adjust_condition': '下修条件',
                              'turnover_rt': '换手率',
                              'convert_price_tips': '下修提示',
                              # 'put_tc': '回售',
                              'adj_cnt': '提出下调次数',
                              'svolume': '正股成交量',
                              #   'ration':'已转股比例'
                              'convert_amt_ratio': '转债剩余占总市值比',
                              'curr_iss_amt': '剩余规模', 'orig_iss_amt': '发行规模',
                              # 'ration_rt': '股东配售率',
                              'option_tip': '期权价值',
                              'bond_nm_tip': '强赎提示',
                              'redeem_dt': '强赎日期',
                              'list_dt': '上市日期',
                              'ytm_rt': '到期收益率',
                              'redeem_icon': '强赎标志',
                              'margin_flg': '是否两融标的',
                              'adj_scnt': '下修成功次数',
                              'convert_cd_tip': '转股日期提示',
                              'ref_yield_info': '参考YTM',

                              # 'guarantor': '担保',
                              }



            df = df.rename(columns=rename_columns)
            df = df[list(rename_columns.values())]
            df['更新日期'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')

        df = df.set_index('可转债代码', drop=True)
        return df

    def get_bond_realtime(self):
        post_data = {
            'btype': 'C',
            'listed': 'Y',
            'rp': '50',
            'is_search': 'N',
        }
        timestamp = int(time.time() * 1000)
        self.url = 'https://www.jisilu.cn/data/cbnew/cb_list_new/?___jsl=LST___t={}'.format(timestamp)
        js = self.download(self.url, data=post_data)
        if not js:
            return None

        ret = js.json()
        bond_list = ret.get('rows', {})
        df = self.data_parse(bond_list, True)
        return df

    def generate_html(self):
        if self.noon:
            df = self.get_bond_realtime()
            df=df.reset_index()
        else:
            df = self.get_bond_data()
        data = self.get_XY_data(df)

        bigger = data['bigger']
        smaller = data['smaller']
        avg = data['avg']
        std = data['std']
        max_name = data['max_name']
        max_pct = data['max_pct']
        min_name = data['min_name']
        min_pct = data['min_pct']

        bar = (
            Bar()
                .add_xaxis(list(data['result_dict'].keys()))
                .add_yaxis(f"{self.today}-可转债涨幅分布", data['zz_list'], category_gap=3)
                .add_yaxis(f"{self.today}-正股涨幅分布", data['zg_list'], category_gap=3)
                .set_series_opts(
                label_opts=opts.LabelOpts(is_show=True),
                axispointer_opts=opts.AxisPointerOpts(is_show=True))
                .set_global_opts(
                title_opts=opts.TitleOpts(title="可转债涨幅分布"),
                xaxis_opts=opts.AxisOpts(
                    name="涨跌幅",
                    is_show=True,
                    name_rotate=30,
                ),
                graphic_opts=[
                    opts.GraphicGroup(
                        graphic_item=opts.GraphicItem(
                            left="70%",
                            top="20%",
                        ),
                        children=[

                            opts.GraphicText(
                                graphic_item=opts.GraphicItem(
                                    left="center",
                                    top="middle",
                                    z=100,
                                ),
                                graphic_textstyle_opts=opts.GraphicTextStyleOpts(
                                    text=JsCode(
                                        f"['涨幅>=0：{bigger}',"
                                        f"'涨幅<0：{smaller}',"
                                        f"'平均涨幅：{avg}%',"
                                        f"'波动方差：{std}',"
                                        f"'',"
                                        f"'最大：{max_name}  {max_pct}%',"
                                        f"'最小：{min_name}  {min_pct}%',"
                                        "''].join('\\n')"
                                    ),
                                    font="14px Microsoft YaHei",
                                    graphic_basicstyle_opts=opts.GraphicBasicStyleOpts(
                                        fill="#333"
                                    )
                                )
                            )
                        ]
                    )
                ],
            )

        )

        bar.render(self.HMTL_PATH)
        # 自定义一个driver
        make_snapshot(snapshot, bar.render(), self.IMGAGE_PATH, driver=driver)


def main(noon=False):
    app = CBDistribution(noon)
    app.generate_html()


if __name__ == '__main__':
    fire.Fire(main)
