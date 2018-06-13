# -*- coding: utf-8 -*-


from __future__ import unicode_literals

import os
import sys
from datetime import datetime, timedelta
from argparse import ArgumentParser

from flask import Flask, request, abort
from linebot import (
    LineBotApi, WebhookParser
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    TemplateSendMessage, ButtonsTemplate, DatetimePickerTemplateAction
)

import threading
import sleepchecker

app = Flask(__name__)


class Alarm:
    def __init__(self):
        self.active = False
        self.snooze_sec = 600 # 基本10分
        self.set_count = 0    # setした回数
        self.ring_count = 0   # アラームがなった回数

    def set(self, sec):
        # threadingでアラームを起動
        alarm_thread = threading.Timer(sec, self.ring)
        alarm_thread.start()
        
        # アラームが鳴る1分前に最新の睡眠情報を取得
        fitbit_thread = threading.Timer(sec - 60, self.check_sleep_fitbit)
        fitbit_thread.start()
        
        if self.set_count == 0:
            #message = 'Alarm: on'
            #line_bot_api.push_message(line_user_id,TextSendMessage(text=message))
            print("Alarm: on")
            self.active = True
            self.set_count += 1
        else:
            print("Alarm: snooze set, After: {}sec, Set_count: {}".format(sec, self.set_count))
            self.set_count += 1

    def reset(self):
        self.active = False
        self.set_count = 0
        self.ring_count = 0

    def ring(self):
        if self.active == True:
            self.ring_count += 1
            message = "起きてー, {}回目".format(self.ring_count)
            line_bot_api.push_message(line_user_id, TextSendMessage(text=message))
            print("Alarm: ring, Ring_count: {}".format(self.ring_count))
    
    def check_sleep_fitbit(self):
        if self.active == True:
            checker = sleepchecker.Checker()
            result = checker.check_sleep()
            #result = True
            if result != False:
                # 睡眠情報がある = 寝ている場合
                self.set(self.snooze_sec)
            else:
                # 起きていた場合
                message = "起きてる！"
                line_bot_api.push_message(line_user_id, TextSendMessage(text=message))
                make_alarm_off()


alm = Alarm()

# get channel_secret and channel_access_token from your environment variable
channel_secret = os.getenv('LINE_CHANNEL_SECRET', None)
channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', None)
line_user_id = os.getenv('LINE_USER_ID', None)
if channel_secret is None:
    print('Specify LINE_CHANNEL_SECRET as environment variable.')
    sys.exit(1)
if channel_access_token is None:
    print('Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.')
    sys.exit(1)

# push通知送信のためのuser_id
if line_user_id is None:
    print('Specify LINE_USER_ID as environment variable.')
    sys.exit(1)

line_bot_api = LineBotApi(channel_access_token)
parser = WebhookParser(channel_secret)


@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    #print("Request body: " + body)

    # parse webhook body
    try:
        events = parser.parse(body, signature)
    except InvalidSignatureError:
        abort(400)

    # if event is MessageEvent and message is TextMessage, then echo text
    for event in events:
        if event.type == "postback":
            # lineテンプレートで選択された時刻にアラームをセット
            if event.postback.data == "datetime_picker":
                dt = event.postback.params["datetime"]# なぜか最後だけdict
                now = datetime.now()
                alarm_time = datetime.strptime(dt, '%Y-%m-%dT%H:%M')
                dif = alarm_time - now
                alm.set(dif.seconds)
                message = 'Alarm: on, at ' + dt
                line_bot_api.push_message(line_user_id,TextSendMessage(text=message))

        if not isinstance(event, MessageEvent):
            continue
        if not isinstance(event.message, TextMessage):
            continue
        
        message = event.message.text
        
        if message == "set":
            # アラームセットのためのlineテンプレートの送信
            make_set_alarm_event(event.reply_token)
        elif message == "off":
            make_alarm_off()
        elif message == "status":
            check_alarm_status()
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=message)
            )
    return "ok"

def make_set_alarm_event(token):
    # アラームセットのためのlineテンプレートの送信
    # TODO: 古いテンプレートは使えないようにする
    now = datetime.now()
    two_min_later = now + timedelta(minutes=2)
    date_picker = TemplateSendMessage(
            alt_text='datetime picker',
            template=ButtonsTemplate(
                title='アラームを設定しますか？',
                text='日付と時刻を選択してください',
                actions=[
                    DatetimePickerTemplateAction(
                        label='設定',
                        data='datetime_picker',
                        mode='datetime',
                        initial=two_min_later.strftime("%Y-%m-%dT%H:%M"),
                        min=two_min_later.strftime("%Y-%m-%dT%H:%M"),
                        max='2099-12-31T23:59'
                        )
                    ]
                )
            )
    line_bot_api.reply_message(token, date_picker)

def make_alarm_off():
    if alm.active is True:
        alm.reset()
        message = 'Alarm: off'
        line_bot_api.push_message(line_user_id,TextSendMessage(text=message))
        print("Alarm: off")
    else:
        message = 'Alarm is not active'
        line_bot_api.push_message(line_user_id,TextSendMessage(text=message))
        print(message)

def check_alarm_status():
    message = "アラーム: {}\n睡眠判定までの時間: {}秒\n現在の睡眠判定回数: {}\
            \nアラームを鳴らした回数: {}".format(alm.active, alm.snooze_sec, alm.set_count, alm.ring_count)
    line_bot_api.push_message(line_user_id,TextSendMessage(text=message))


if __name__ == "__main__":
    arg_parser = ArgumentParser(
        usage='Usage: python ' + __file__ + ' [--port <port>] [--help]'
    )
    arg_parser.add_argument('-p', '--port', type=int, default=5000, help='port')
    arg_parser.add_argument('-d', '--debug', default=True, help='debug')
    options = arg_parser.parse_args()

    app.run(debug=options.debug, port=options.port)
