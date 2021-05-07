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
    ButtonsTemplate, MessageAction, PostbackAction, URIAction,
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
    special_cases = {
        "Assesmen Umum": "/take_test",
        "Psikolog Terdekat": "/contact_psychiatrist",
        "Tips Mental Health": "/self_care_practices"
    }
    rasa, sender = get_meta_data(event)
    text = event.message.text
    if text in special_cases:
        text = special_cases[text]
    api_responses = rasa.post_action(text, sender)
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
            custom_data = r['custom']
            if 'locations' in custom_data:
                datas = custom_data['locations']
                bubbles = []
                for data in datas:
                    bubbles.append(get_locations_content(data))
                contents = CarouselContainer(contents=bubbles)
                responses.append(
                    FlexSendMessage(
                        alt_text="Daftar Lokasi Psikolog Terdekat",
                        contents=contents
                    )
                )
            elif 'payload' in custom_data:
                payload = custom_data['payload']
                bubble = get_multiple_choice_content(payload)
                responses.append(FlexSendMessage(alt_text=payload['text'], contents=bubble))
        elif 'buttons' in r:
            bubble = get_multiple_choice_content(r)
            responses.append(FlexSendMessage(alt_text=r['text'], contents=bubble))
        elif 'text' in r:
            responses.append(TextSendMessage(text=r['text']))
    try:
        if (len(responses) > 0):
            line_bot_api.reply_message(
                event.reply_token,
                responses
            )
    except Exception as e:
        print(e)
        app.logger.info("Error ->" + e.message)
        for d in e.error.details:
            app.logger.info("    " + d.property + " : " + d.message)


def get_header_text(data):
    question_number = data.get("question_number", None)
    if question_number == None:
        return [
            TextComponent(
                text="Pilih salah satu",
                size='xs',
                margin='xs',
                color='#1DB446'
            )
        ]
    else:
        percentage = float(question_number / 12) * 100
        return [
            TextComponent(
                text="Progess : {} %".format(int(round(percentage))),
                size='xs',
                margin='lg',
                color='#27ACB2'
            ),
            BoxComponent(
                layout='vertical',
                margin='sm',
                height='6px',
                background_color='#9FD8E3',
                corner_radius='2px',
                contents=[
                    BoxComponent(
                        layout='vertical',
                        height='6px',
                        corner_radius='2px',
                        width="{}%".format(int(round(percentage))),
                        background_color='#0D8186',
                        contents=[
                            FillerComponent()
                        ]
                    )
                ],
            ),
        ]

        

def get_multiple_choice_content(data):
    actions = []
    for b in data['buttons']:
        actions.append(ButtonComponent(
            style='primary',
            height='sm',
            margin='md',
            action=MessageAction(label=b['title'], text=b['title'])
        ))

    bubble = BubbleContainer(
        direction='ltr',
        body=BoxComponent(
                layout='vertical',
                contents=get_header_text(data) + [
                    TextComponent(
                        text=data.get('text'),
                        size='md',
                        margin='lg',
                        wrap=True,
                    )
                ]
        ),
        footer=BoxComponent(
            layout='vertical',
            contents=actions
        )
    )

    return bubble


def get_locations_content(data):
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


if __name__ == "__main__":
    arg_parser = ArgumentParser(
        usage='Usage: python ' + __file__ + ' [--port <port>] [--help]'
    )
    arg_parser.add_argument('-p', '--port', type=int, default=8000, help='port')
    arg_parser.add_argument('-d', '--debug', default=False, help='debug')
    options = arg_parser.parse_args()

    app.run(debug=options.debug, port=options.port)
