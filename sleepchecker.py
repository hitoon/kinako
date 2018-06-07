# coding:utf-8


import os
import fitbit
import datetime
from ast import literal_eval


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
        DATE = "2018-06-01"
        data_sec = self.client.intraday_time_series('activities/heart',
                DATE, detail_level='1sec') #'1sec', '1min', or '15min'

        heart_sec = data_sec["activities-heart-intraday"]["dataset"]
        print(heart_sec[-100:])

    def _get_minute_dict(self, DATE):
        sleepdata = self.client.sleep(date=DATE)
        dateOfSleep = sleepdata["sleep"][0]["dateOfSleep"]
        sleep_minute = sleepdata["sleep"][0]["minuteData"]
        keys = []
        vals = []
        for i in sleep_minute:
            dt = "{} {}".format(dateOfSleep, i["dateTime"])# 2018-06-07 08:12:30
            keys.append(dt)
            vals.append(i["value"])
        tuple_ = [(k, v) for k, v in zip(keys, vals)]
        return tuple_ # tuple: [(dateTime, sleep), ・・・]
        #dict_ = dict(zip(keys, vals))
        #return dict_ # dict_: {dateTime: value}
        
        # The different values for sleep are:
        #   0: no sleep data
        #   1: asleep
        #   2: awake
        #   3: very awake

    def check_sleep(self):
        # todo: 同期してない　→　同期してください
        # 今から30分前のデータをみる → 寝ていたら睡眠状態を返す
        today = str(datetime.date.today())
        minute_dict = self._get_minute_dict(today)
        latest = minute_dict[-1]
        tdatetime = datetime.datetime.strptime(latest[0], '%Y-%m-%d %H:%M:%S')
        now_time = datetime.datetime.now() #.strftime("%H:%M:%S")
        time_difference = now_time - tdatetime
        time_difference_minute = time_difference.seconds // 60
        print("最新の睡眠データと現在の時刻の差:", time_difference, "分:", time_difference_minute)
        if time_difference_minute < 10:
            return latest[1]
        else:
            print("直前10分の睡眠データがありません")
            return False

if __name__ == "__main__":
    checker = Checker()
    checker.check_sleep()
