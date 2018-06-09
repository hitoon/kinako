# -*- coding: utf-8 -*-


from __future__ import unicode_literals

import os
import sys
from datetime import datetime
from argparse import ArgumentParser
import threading

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

app = Flask(__name__)

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
    print("Request body: " + body)

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
                set_alarm(dt, event.reply_token)
            return "OK"

        if not isinstance(event, MessageEvent):
            continue
        if not isinstance(event.message, TextMessage):
            continue
        
        message = event.message.text
        
        if message == "set":
            # アラームセットのためのlineテンプレートの送信
            make_set_alarm_event(event.reply_token)

        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=message)
            )

    return 'OK'

def make_set_alarm_event(token):
    # アラームセットのためのlineテンプレートの送信
    now = datetime.now().strftime("%Y-%m-%dT%H:%M")
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
                        initial=now,
                        min='2000-01-01T00:00',
                        max='2099-12-31T23:59'
                        )
                    ]
                )
            )
    line_bot_api.reply_message(
            token,
            date_picker
            )
    
    return 1

def set_alarm(dt, token):# t 2018-06-09T18:29
    now = datetime.now()
    alarm_time = datetime.strptime(dt, '%Y-%m-%dT%H:%M')
    dif = alarm_time - now
    print("アラームセットまで(秒)", dif.seconds)
    
    # threadingでアラームを起動
    t=threading.Timer(dif.seconds, alarm)
    t.start()

    # TODO: fitbit判定threadの起動, アラーム設定時刻5分後に寝ているかどうか取得し、
    # 寝ていたらもう一度アラームを鳴らす

    message = " ".join(dt.split("T")) + " にアラームをセットしました！"
    line_bot_api.reply_message(
            token,
            TextSendMessage(text=message)
            )
    return 1

def alarm():
    line_bot_api.push_message(line_user_id, TextSendMessage(text='起きてー'))
    print("アラームを呼びました")
    print("現在のスレッド数", threading.active_count())
    return 1


if __name__ == "__main__":
    arg_parser = ArgumentParser(
        usage='Usage: python ' + __file__ + ' [--port <port>] [--help]'
    )
    arg_parser.add_argument('-p', '--port', type=int, default=5000, help='port')
    arg_parser.add_argument('-d', '--debug', default=True, help='debug')
    options = arg_parser.parse_args()

    app.run(debug=options.debug, port=options.port)
