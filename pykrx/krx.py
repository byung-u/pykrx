from pykrx.krx_stock import MKD01023, MKD20011
from pykrx.krx_stock import MKD30040, MKD30009, StockFinder
from pykrx.krx_bond import MKD40038, MKD40013
from pykrx.krx_short import SRT02010100, SRT02020100
from pykrx.krx_short import SRT02020300, SRT02020400
from pykrx.krx_short import SRT02030100, SRT02030400
import datetime
import pandas as pd
import re
import calendar


class Krx:
    def __init__(self):
        self.stock_finder = StockFinder.scraping()
        self.re_ticker = re.compile("^[0-9]{6}$")
        self.re_isin = re.compile("^KR[0-9]{10}$")

    def get_tickers(self, date=None):
        if date is None:
            return list(self.stock_finder['티커'].values)
        else:
            # HACK :
            df = MKD30009().scraping(date)
            return list(df.index)

    def get_isin_by_ticker(self, ticker):
        try:
            cond = self.stock_finder['티커'] == ticker
            return self.stock_finder['ISIN'][cond].values[0]
        except IndexError:
            return None

    def _get_isin(self, ticker):
        if ticker is None:
            return None
        elif self.re_ticker.match(ticker):
            isin = self.get_isin_by_ticker(ticker)
        elif self.re_isin.match(ticker):
            isin = ticker
        else:
            print("잘못된 Ticker를 입력했습니다. ")
            print(" - 올바른 예: 000660")
            raise RuntimeError
        return isin

    def get_business_days(self, year, month):
        '''영업일의 리스트를 구하는 함수
        :param year: 조회년도
        :param month: 조회월
        :return: business day list
        '''

        first_day, last_day = calendar.monthrange(year, month)
        first_day_in_string = "{}{:02d}{:02d}".format(year, month, first_day)
        last_day_in_string = "{}{:02d}{:02d}".format(year, month, last_day)

        df = self.get_market_ohlcv(first_day_in_string, last_day_in_string, "066570")
        return df.index.tolist()

    @staticmethod
    def get_treasury_yields_in_kerb_market(date):
        df = MKD40013().scraping(date)
        if df is None:
            return None
        return df

    @staticmethod
    def get_treasury_yields_in_bond_index(fromdate, todate):
        df = MKD40038().scraping(fromdate, todate)#.reset_index(drop=True)
        if df is None:
            return None

        if fromdate not in df.index.tolist():
            print("WARN: fromdate seems to be a holiday")
            print("- {} is used instead of {}".format(df.index[-1], fromdate))
        if todate not in df.index.tolist():
            print("WARN: todate seems to be a holiday")
            print("- {} is used instead of {}".format(df.index[0], todate))

        # 구현!
        return df

    @staticmethod
    def get_market_index(date):
        df = MKD20011().scraping(date)
        if df is None:
            return None
        return df


    @staticmethod
    def get_market_status_by_date(date):
        '''일자별 BPS/PER/PBR/배당수익률
        :param date : 조회 일자   (YYYYMMDD)
                       20000101 이후의 데이터 제공
        :return     : DataFrame
        '''
        return MKD30009().scraping(date)

    def get_market_ohlcv(self, fromdate, todate, ticker):
        '''일자별 OHLCV
        :param fromdate: 조회 시작 일자   (YYYYMMDD)
        :param todate  : 조회 마지막 일자 (YYYYMMDD)
        :param ticker  : 종목 번호
        :return        : OHLCV DataFrame
        '''
        isin = self._get_isin(ticker)
        return MKD30040().scraping(fromdate, todate, isin).sort_index()

    def get_shorting_status_by_date(self, fromdate, todate, ticker):
        '''일자별 공매도 종합 현황
        :param fromdate: 조회 시작 일자   (YYYYMMDD)
        :param todate  : 조회 마지막 일자 (YYYYMMDD)
        :param ticker  : 종목 번호
        :return        : 종합 현황 DataFrame
        '''
        isin = self._get_isin(ticker)
        return SRT02010100().scraping(isin, fromdate, todate)

    def get_shorting_volume_by_ticker(self, fromdate, todate, ticker=None, market="코스피"):
        '''종목별 공매도 거래 현황 조회
        :param fromdate: 조회 시작 일자   (YYYYMMDD)
        :param todate  : 조회 마지막 일자 (YYYYMMDD)
        :param ticker  : 종목 번호 - None일 경우 전체 조회
        :param market  : 코스피/코스닥
        :return        : 거래 현황 DataFrame
        '''
        isin = self._get_isin(ticker)
        return SRT02020100().scraping(fromdate, todate, market, isin)

    def get_shorting_volume_by_investor(self, fromdate, todate, market="코스피", inquery="거래량"):
        '''투자자별 공매도 거래 현황
        :param fromdate: 조회 시작 일자   (YYYYMMDD)
        :param todate  : 조회 마지막 일자 (YYYYMMDD)
        :param market  : 코스피/코스닥
        :param inquery : 거래량조회 / 거래대금조회
        :return        : 거래 현황 DataFrame
        '''
        return SRT02020300().scraping(fromdate, todate, inquery, market)

    def get_shorting_volume_top50(self, date, market="코스피"):
        '''공매도 거래 비중 TOP 50
        :param date    : 조회 일자   (YYYYMMDD)
        :param market  : 코스피/코스닥
        :return        : 거래 비중 DataFrame
        '''
        # date   : 조회 일자 (YYYYMMDD)
        # market : 코스피 / 코스닥
        return SRT02020400().scraping(date, market)

    def get_shorting_balance_by_ticker(self, fromdate, todate, ticker=None, market="코스피"):
        '''종목별 공매도 잔고 현황
        :param fromdate: 조회 시작 일자   (YYYYMMDD)
        :param todate  : 조회 마지막 일자 (YYYYMMDD)
        :param ticker  : 종목 번호 - None일 경우 전체 조회
        :param market  : 코스피/코스닥
        :return        : 잔고 현황 DataFrame
        '''
        isin = self._get_isin(ticker)
        return SRT02030100().scraping(fromdate, todate, market, isin)

    def get_shorting_balance_top50(self, date, market="코스피"):
        '''종목별 공매도 잔고 TOP 50
        :param date    : 조회 일자   (YYYYMMDD)
        :param market  : 코스피/코스닥
        :return        : 잔고 현황 DataFrame
        '''
        return SRT02030400().scraping(date, market)


if __name__ == "__main__":
    pd.set_option('display.width', None)
    krx = Krx()
    print(krx.get_business_days(2019, 1))
