# -*- coding: utf-8 -*-


from __future__ import unicode_literals

import os
import sys
from datetime import datetime
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

app = Flask(__name__)

# get channel_secret and channel_access_token from your environment variable
channel_secret = os.getenv('LINE_CHANNEL_SECRET', None)
channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', None)
if channel_secret is None:
    print('Specify LINE_CHANNEL_SECRET as environment variable.')
    sys.exit(1)
if channel_access_token is None:
    print('Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.')
    sys.exit(1)

line_bot_api = LineBotApi(channel_access_token)
parser = WebhookParser(channel_secret)

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # parse webhook body
    try:
        events = parser.parse(body, signature)
    except InvalidSignatureError:
        abort(400)

    # if event is MessageEvent and message is TextMessage, then echo text
    for event in events:
        if event.type == "postback":
            # todo アラームをセット
            return "OK"

        if not isinstance(event, MessageEvent):
            continue
        if not isinstance(event.message, TextMessage):
            continue
        
        message = event.message.text
        
        if message == "set":
            make_set_alarm_event(event.reply_token)

        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=message)
            )

    return 'OK'

def make_set_alarm_event(token):
    now = datetime.now().strftime("%Y-%m-%dT%H:%M")
    date_picker = TemplateSendMessage(
            alt_text='datetime picker',
            template=ButtonsTemplate(
                text='アラームを設定',
                title='アラーム',
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


if __name__ == "__main__":
    arg_parser = ArgumentParser(
        usage='Usage: python ' + __file__ + ' [--port <port>] [--help]'
    )
    arg_parser.add_argument('-p', '--port', type=int, default=8000, help='port')
    arg_parser.add_argument('-d', '--debug', default=False, help='debug')
    options = arg_parser.parse_args()

    app.run(debug=options.debug, port=options.port)
