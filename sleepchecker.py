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
        data_sec = self.client.intraday_time_series('activities/heart', DATE, detail_level='1sec') #'1sec', '1min', or '15min'
        heart_sec = data_sec["activities-heart-intraday"]["dataset"]
        print(heart_sec[-100:])

if __name__ == "__main__":
    checker = Checker()
    checker.test_checker()
