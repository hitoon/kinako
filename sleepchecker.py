# coding:utf-8


import os
import sys
import fitbit
import datetime
from ast import literal_eval
import pandas as pd


CLIENT_ID = os.environ["FITBIT_CLIENT_ID"]
CLIENT_SECRET  = os.environ["FITBIT_CLIENT_SECRET"]
TOKEN_FILE    = "token.txt"


class Checker:
    def __init__(self):
        self.my_state = "awake"
        
        tokens = open(TOKEN_FILE).read()
        token_dict = literal_eval(tokens)
        self.access_token = token_dict['access_token']
        self.refresh_token = token_dict['refresh_token']

        def update_token(token):
            print("update token ...")
            with open(TOKEN_FILE, 'w') as f:
                f.write(str(token))
            self.access_token = token['access_token']
            self.refresh_token = token['refresh_token']
        
        self.client = fitbit.Fitbit(CLIENT_ID, CLIENT_SECRET,
                access_token = self.access_token, refresh_token = self.refresh_token,
                refresh_cb = update_token)

    def test_checker(self):
        today = str(datetime.date.today())
        data_sec = self.client.intraday_time_series('activities/heart',
                today, detail_level='1sec') #'1sec', '1min', or '15min'
        heart_sec = data_sec["activities-heart-intraday"]["dataset"]
        print(heart_sec[-10:])
        return heart_sec

    def get_heart_graph(self):
        today = str(datetime.date.today())
        heart_sec = self.test_checker()
        heart_df = pd.DataFrame.from_dict(heart_sec)
        heart_df.index = pd.to_datetime([today + " " + t for t in heart_df.time])
        ax = heart_df.plot(y="value", figsize=(20,5))
        fig = ax.get_figure()
        fig.savefig('heart_graph.png')

    def check_sleep(self, DATE):
        #DATE = "2018-06-10" # テスト用
        sleepdata = self.client.sleep(date=DATE)
        try:
            dateOfSleep = sleepdata["sleep"][0]["dateOfSleep"]
            sleep_minute = sleepdata["sleep"][0]["minuteData"]
        except IndexError:
            print("睡眠データがありません")
            return None
        
        keys = []
        vals = []
        for i in sleep_minute:
            dt = "{} {}".format(dateOfSleep, i["dateTime"])# 2018-06-07 08:12:30
            keys.append(dt)
            vals.append(i["value"])
        tuple_ = [(k, v) for k, v in zip(keys, vals)]
        print(tuple_[:10])
        return tuple_ 
        # tuple: [(dateTime, sleep), ・・・]
        #dict_ = dict(zip(keys, vals))
        #return dict_ # dict_: {dateTime: value}
        
        # The different values for sleep are:
        #   0: no sleep data
        #   1: asleep
        #   2: awake
        #   3: very awake

    def get_margin(self, date=None):
        # 今から10分前のデータをみる → 寝ていたら睡眠状態を返す
        if date == None:
            date = str(datetime.date.today())# 今日
        
        minute_dict = self.check_sleep(date)
        if minute_dict is None:
            return None
        
        latest = minute_dict[-1]
        tdatetime = datetime.datetime.strptime(latest[0], '%Y-%m-%d %H:%M:%S')
        now_time = datetime.datetime.now() #.strftime("%H:%M:%S")
        time_difference = now_time - tdatetime
        time_difference_minute = time_difference.seconds
        print("最新の睡眠データと現在の時刻の差:", time_difference, "分:", time_difference_minute)
        if time_difference_minute < 30:# 単位：分
            return latest[1]
        else:
            print("直前30分の睡眠データがありません")
            return False


if __name__ == "__main__":
    checker = Checker()
    #checker.get_heart_graph()
    #checker.check_sleep("2018-07-27")
    checker.get_margin("2018-07-27")
