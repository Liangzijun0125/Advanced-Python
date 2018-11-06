#!/usr/bin/env python
# -*- coding: utf-8 -*-
# __author__ = 'Rohit Gupta'

"""
Cryptocurrency price History from coinmarketcap.com
"""

from __future__ import print_function               #把下一个新版本的特性导入到当前版本

__all__ = ["CmcScraper"]

'''它是一个string元素组成的list变量，定义了当你使用 from <module> import * 
导入某个模块的时候能导出的符号（这里代表变量，函数，类等）。
'''

import os
import csv
from datetime import datetime
from .utils import download_coin_data, extract_data, InvalidParameters


class CmcScraper(object):
    """
    Scrape cryptocurrency historical market price data from coinmarketcap.com

    """

    def __init__(
        self,                                                      #self代表的是类的实例
        coin_code,
        start_date=None,
        end_date=None,
        all_time=False,
        order_ascending=False,
    ):
        """
        :param coin_code: coin code of cryptocurrency e.g. btc
        :param start_date: date since when to scrape data (in the format of dd-mm-yyyy)
        :param end_date: date to which scrape the data (in the format of dd-mm-yyyy)
        :param all_time: 'True' if need data of all time for respective cryptocurrency
        :param order_ascending: data ordered by 'Date' in ascending order (i.e. oldest first).

        """

        self.coin_code = coin_code
        self.start_date = start_date
        self.end_date = end_date
        self.all_time = bool(all_time)
        self.order_ascending = order_ascending
        self.headers = []
        self.rows = []

        # enable all_time download if start_time or end_time is not given
        if not (self.start_date and self.end_date):
            self.all_time = True                                        #不指定时间段时就直接抓取全部历史数据

        if not (self.all_time or (self.start_date and self.end_date)):
            raise InvalidParameters(
                "'start_date' or 'end_date' cannot be empty if 'all_time' flag is False"
            )

    def __repr__(self):
        return "<CmcScraper coin_code:{}, start_date:{}, end_date:{}, all_time:{}>".format(
            self.coin_code, self.start_date, self.end_date, self.all_time
        )

    def _download_data(self, **kwargs):             #当函数的参数不确定时，可以使用*args 和**kwargs，*args 没有key值，**kwargs有key值。**kw是关键字参数，用于字典
        """
        This method downloads the data.
        :param forced: (optional) if ``True``, data will be re-downloaded.
        :return:
        """

        forced = kwargs.get("forced")       #Python 字典(Dictionary) get() 函数返回指定键的值，如果值不在字典中返回默认值。

        if self.headers and self.rows and not forced:
            return

        if self.all_time:
            self.start_date, self.end_date = None, None

        table = download_coin_data(self.coin_code, self.start_date, self.end_date)

        # self.headers, self.rows, self.start_date, self.end_date = extract_data(table)
        self.end_date, self.start_date, self.headers, self.rows = extract_data(table)

        if self.order_ascending:
            self.rows.sort(key=lambda x: datetime.strptime(x[0], "%d-%m-%Y"))    #Python time strptime() 函数根据指定的格式把一个时间字符串解析为时间元组。

    def get_data(self, verbose=False, **kwargs):

        """
        This method fetches downloaded the data.
        :param verbose: (optional) Flag to enable verbose.
        :param kwargs: Optional arguments that data downloader takes.
        :return:
        """

        self._download_data(**kwargs)

        if verbose:                                     #re模块的re.VERBOSE可以把正则表达式写成多行，并且自动忽略空格。
            print(*self.headers, sep=", ")

            for row in self.rows:
                print(*row, sep=", ")
        else:
            return self.headers, self.rows

    def get_dataframe(self, date_as_index=False, **kwargs):     
        #pandas是python环境下最有名的数据统计包，而DataFrame是一种数据组织方式（类比Excel，它也是一种数据组织和呈现的方式，简单说就是表格）
        #如果不print DataFrame，就看不到这些数据，
        """
        This gives scraped data as DataFrame.
        :param date_as_index: make 'Date' as index and remove 'Date' column.   #时间成为了索引，索引(index)就是每一行数据的id,可以标识每一行的唯一值
        :param kwargs: Optional arguments that data downloader takes.
        :return: DataFrame of the downloaded data.
        """

        try:
            import pandas as pd
        except ImportError:
            pd = None

        if pd is None:
            raise NotImplementedError(
                "DataFrame Format requires 'pandas' to be installed."
                "Try : pip install pandas"
            )

        self._download_data(**kwargs)

        dataframe = pd.DataFrame(data=self.rows, columns=self.headers)

        # convert 'Date' column to datetime type
        dataframe["Date"] = pd.to_datetime(
            dataframe["Date"], format="%d-%m-%Y", dayfirst=True
        )

        if date_as_index:
            # set 'Date' column as index and drop the the 'Date' column.
            dataframe.set_index("Date", inplace=True)

        return dataframe

    def export_csv(self, csv_name=None, csv_path=None, **kwargs):
        """
        This exports scraped data into a csv.
        :param csv_name: (optional) name of csv file.
        :param csv_path: (optional) path to where export csv file.
        :param kwargs: Optional arguments that data downloader takes.
        :return:
        """

        self._download_data(**kwargs)

        if csv_path is None:
            # Export in current directory if path not specified
            csv_path = os.getcwd()

        if csv_name is None:
            # Make name fo file in format of {coin_code}_{start_date}_{end_date}.csv
            csv_name = "{0}_{1}_{2}.csv".format(
                self.coin_code, self.start_date, self.end_date
            )

        if not csv_name.endswith(".csv"):
            csv_name += ".csv"

        _csv = "{0}/{1}".format(csv_path, csv_name)

        try:
            with open(_csv, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.writer(
                    csvfile, delimiter=",", quoting=csv.QUOTE_NONNUMERIC
                )    
                '''
                分隔符为,;
                If quoting is set to csv.QUOTE_NONNUMERIC, then csvfile 
                will quote all fields containing text data and convert all numeric fields to the float data type.
                '''
                writer.writerow(self.headers)
                for data in self.rows:
                    writer.writerow(data)
        except IOError as err:
            errno, strerror = err.args
            print("I/O error({0}): {1}".format(errno, strerror))
