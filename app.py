from __future__ import unicode_literals

import os
import sys
from argparse import ArgumentParser
from dotenv import load_dotenv

from flask import Flask, request, abort
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError,
    LineBotApiError
)
from linebot.models import (
    MessageEvent, PostbackEvent,
    TextMessage, LocationMessage, 
    TextSendMessage, FlexSendMessage,
    TemplateSendMessage,
    ButtonsTemplate, PostbackAction, URIAction,
    CarouselContainer, BubbleContainer,
    ImageComponent, BoxComponent,
    TextComponent, ButtonComponent,
    SeparatorComponent, FillerComponent
)

from rasaclient import RasaClient
import json

# Load variables from .env files
load_dotenv()

app = Flask(__name__)

# get channel_secret and channel_access_token from your environment variable
channel_secret = os.getenv('LINE_CHANNEL_SECRET', None)
channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', None)
rasa_endpoint = os.getenv('RASA_ENDPOINT', None)
if channel_secret is None:
    print('Specify LINE_CHANNEL_SECRET as environment variable.')
    sys.exit(1)
if channel_access_token is None:
    print('Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.')
    sys.exit(1)

line_bot_api = LineBotApi(channel_access_token)
handler = WebhookHandler(channel_secret)


@app.route("/webhook", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    try:
        handler.handle(body, signature)
    except LineBotApiError as e:
        app.logger.info("Error occurred: " + e.message)
        for d in e.error.details:
            app.logger.info("    " + d.property + " : " + d.message)
    except InvalidSignatureError:
        abort(400)

    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    rasa, sender = get_meta_data(event)
    api_responses = rasa.post_action(event.message.text, sender)
    handle_response(event, api_responses)


@handler.add(MessageEvent, message=LocationMessage)
def handle_location_message(event):
    location_string = "{{\"location\": \"{0}, {1}\"}}".format(event.message.latitude, event.message.longitude)
    rasa, sender = get_meta_data(event)
    api_responses = rasa.post_action(message="/inform" + location_string, sender=sender)
    handle_response(event, api_responses)


@handler.add(PostbackEvent)
def handle_postback(event):
    if event.postback.data[0] == '/':
        rasa, sender = get_meta_data(event)
        api_responses = rasa.post_action(event.postback.data, sender)
        handle_response(event, api_responses)


def get_meta_data(event):
    rasa = RasaClient(rasa_endpoint)
    sender = event.source.user_id
    return rasa, sender


def handle_response(event, api_responses):
    responses = []
    for r in api_responses:
        if 'custom' in r:
            contents = get_carousel_message(r['custom']['locations'])
            responses.append(FlexSendMessage(alt_text="Daftar Lokasi Psikolog Terdekat", contents=contents))
        elif 'buttons' in r:
            button_actions = []
            for b in r['buttons']:
                button_actions.append(
                    PostbackAction(
                            label=b['title'],
                            data=b['payload']
                        )
                    )
            responses.append(TemplateSendMessage(
                alt_text=r['text'],
                template=ButtonsTemplate(
                    text=r['text'],
                    actions=button_actions
                )
            ))
        elif 'text' in r:
            responses.append(TextSendMessage(text=r['text']))
    try:
        if (len(responses) > 0):
            line_bot_api.reply_message(
                event.reply_token,
                responses
            )
    except Exception as e:
        app.logger.info("Error ->" + e)


def get_open_now(open_now):
    if (open_now == None):
        return FillerComponent()
    if (open_now):
        return TextComponent(
                text="Buka",
                size='sm',
                margin='xs',
                color='#1DB446'
            )
    else:
        return TextComponent(
                text="Tutup",
                size='sm',
                margin='xs',
                color='#ff334b'
            )


def get_bubble_content(data):
    bubble = BubbleContainer(
            direction='ltr',
            body=BoxComponent(
                layout='vertical',
                contents=[
                    TextComponent(
                        text="Rekomendasi #{}".format(data.get('rank')),
                        weight='bold',
                        size='sm',
                        color='#1DB446'
                    ),
                    TextComponent(
                        text=data.get('name'),
                        weight='bold',
                        size='lg',
                        margin='md',
                        wrap=True
                    ),
                    TextComponent(
                        text="⭐ {0} ({1} Ulasan)".format(data.get('rating'), data.get('rating_user')),
                        size='sm',
                        margin='xs',
                        color='#aaaaaa'
                    ),
                    TextComponent(
                        text=data.get('formatted_address', 'Indonesia'),
                        margin='xs',
                        wrap=True,
                        color='#aaaaaa',
                        size='sm'
                    ),
                    get_open_now(data.get('open_now'))
                ],
            ),
            footer=BoxComponent(
                layout='vertical',
                contents=[
                    SeparatorComponent(),
                    ButtonComponent(
                        style='link',
                        height='sm',
                        action=URIAction(label='Buka Maps', uri=data.get("url"))
                    )
                ]
            ),
        )
    return bubble


def get_carousel_message(datas):
    contents = []
    for data in datas:
        contents.append(get_bubble_content(data))
    return CarouselContainer(contents=contents)


if __name__ == "__main__":
    arg_parser = ArgumentParser(
        usage='Usage: python ' + __file__ + ' [--port <port>] [--help]'
    )
    arg_parser.add_argument('-p', '--port', type=int, default=8000, help='port')
    arg_parser.add_argument('-d', '--debug', default=False, help='debug')
    options = arg_parser.parse_args()

    app.run(debug=options.debug, port=options.port)
