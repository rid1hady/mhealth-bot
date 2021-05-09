import logging

from sanic import Blueprint, response
from sanic.request import Request
from sanic.response import HTTPResponse
from sanic.exceptions import abort

from rasa.core.channels.channel import UserMessage, CollectingOutputChannel, InputChannel
from rasa.shared.constants import INTENT_MESSAGE_PREFIX

from typing import Text, Dict, Any, Optional, Callable, Awaitable
from linebot import LineBotApi, WebhookParser
from linebot.exceptions import InvalidSignatureError, LineBotApiError

from linebot.models import (
    MessageEvent, PostbackEvent,
    TextMessage, LocationMessage,
    TextSendMessage, FlexSendMessage,
    CarouselContainer
)

from connectors.message_constructor import construct_location_message, construct_multiple_choice

logger = logging.getLogger(__name__)


class LineClient:
    @classmethod
    def name(cls) -> Text:
        return "line"

    def __init__(
            self,
            access_token: Text,
            secret: Text,
            on_new_message: Callable[[UserMessage], Awaitable[Any]]
    ) -> None:
        self.on_new_message = on_new_message
        self.client = LineBotApi(access_token)
        self.parser = WebhookParser(secret)
        self.output_collector = LineOutput(self.client)

    async def handle(self, event):
        if isinstance(event, MessageEvent):
            if isinstance(event.message, TextMessage):
                await self.handle_message(event)
            elif isinstance(event.message, LocationMessage):
                await self.handle_location_message(event)
        elif isinstance(event, PostbackEvent):
            await self.handle_postback(event)

    async def handle_message(self, event):
        special_cases = {
            "Assesmen Umum": "/take_test",
            "Psikolog Terdekat": "/contact_psychiatrist",
            "Tips Mental Health": "/self_care_practices"
        }
        text = event.message.text
        if text in special_cases:
            text = special_cases[text]
        await self.send_to_rasa(
            text=text,
            out_channel=self.output_collector,
            sender_id=event.source.user_id
        )

    async def handle_location_message(self, event):
        lat = event.message.latitude
        long = event.message.longitude
        location_string = "{{\"location\": \"{0}, {1}\"}}".format(lat, long)
        message = "/inform" + location_string
        await self.send_to_rasa(
            text=message,
            out_channel=self.output_collector,
            sender_id=event.source.user_id
        )

    async def handle_postback(self, event):
        if event.postback.data[0] == INTENT_MESSAGE_PREFIX:
            await self.send_to_rasa(
                text=event.postback.data,
                out_channel=self.output_collector,
                sender_id=event.source.user_id
            )

    async def send_to_rasa(
            self,
            text: Text,
            out_channel: Optional["CollectingOutputChannel"],
            sender_id: Text,
            metadata: Optional[Dict] = None
    ) -> None:
        usr_message = UserMessage(
            text,
            out_channel,
            sender_id,
            input_channel=self.name(),
            metadata=metadata
        )
        await self.on_new_message(usr_message)


class LineOutput(CollectingOutputChannel):
    @classmethod
    def name(cls) -> Text:
        return "line"

    def __init__(self, line_bot_api: LineBotApi) -> None:
        super().__init__()
        self.line_bot_api = line_bot_api

    def send(self, reply_token: Text) -> None:
        responses = []
        for message in self.messages:
            if message.get('custom'):
                responses.append(self.get_custom_response(message.get('custom')))
            elif message.get('buttons'):
                responses.append(self.get_button_response(message))
            elif message.get('text'):
                responses.append(self.get_text_response(message.get('text')))
        
        responses = list(filter(None, responses))
        if len(responses) > 0:
            self.line_bot_api.reply_message(
                reply_token,
                responses
            )

    def get_text_response(
            self, text: Text
    ) -> TextSendMessage:
        return TextSendMessage(text)

    def get_button_response(
            self,
            message: Dict[Text, Any]
    ) -> FlexSendMessage:
        content = construct_multiple_choice(message)
        return FlexSendMessage(alt_text=message.get('text'), contents=content)

    def get_custom_response(
            self, message: Dict[Text, Any]
    ) -> FlexSendMessage:
        responses = None
        if 'locations' in message:
            locations = message.get('locations')
            bubbles = []
            for loc in locations:
                bubbles.append(construct_location_message(loc))
            carousel = CarouselContainer(contents=bubbles)
            responses = FlexSendMessage(
                alt_text="Daftar Lokasi Psikolog Terdekat",
                contents=carousel
            )

        elif 'payload' in message:
            payload = message.get('payload')
            bubble = construct_multiple_choice(payload)
            responses = FlexSendMessage(alt_text=payload.get('text'), contents=bubble)

        return responses


class LineInput(InputChannel):
    @classmethod
    def name(cls) -> Text:
        return "line"

    @classmethod
    def from_credentials(cls, credentials: Optional[Dict[Text, Any]]) -> InputChannel:
        if not credentials:
            cls.raise_missing_credentials_exception()

        return cls(
            credentials.get("access_token"),
            credentials.get("secret"),
        )

    def __init__(self, line_access_token: Text, line_secret: Text) -> None:
        self.line_access_token = line_access_token
        self.line_secret = line_secret

    def blueprint(
            self, on_new_message: Callable[[UserMessage], Awaitable[None]]
    ) -> Blueprint:

        line_webhook = Blueprint("line_webhook", __name__)

        @line_webhook.route("/", methods=["GET"])
        async def health(request: Request) -> HTTPResponse:
            logger.info("Request " + request.json)
            return response.json({"status": "ok"})

        @line_webhook.route("/webhook", methods=["POST"])
        async def callback(request: Request) -> HTTPResponse:
            signature = request.headers.get('X-Line-Signature')
            
            line = LineClient(
                self.line_access_token,
                self.line_secret,
                on_new_message
            )

            body = request.body.decode('utf-8')
            logger.info("Request Body: " + body)

            try:
                events = line.parser.parse(body, signature)
                reply_token = events[0].reply_token
                for event in events:
                    await line.handle(event)
                
                line.output_collector.send(reply_token)
            except LineBotApiError as e:
                logger.exception(
                    "Exception occurred " + e.message
                )
                for d in e.error.details:
                    logger.info("    " + d.property + " : " + d.message)
            except InvalidSignatureError as e:
                logger.exception(e.message)
                abort(400)

            return response.json({"status": "ok"})

        return line_webhook
