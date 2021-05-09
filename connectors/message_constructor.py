from linebot.models import (
    MessageAction, URIAction,
    BubbleContainer, BoxComponent,
    TextComponent, ButtonComponent,
    SeparatorComponent, FillerComponent
)


def construct_location_message(data):
    def get_open_now(open_now):
        if open_now is None:
            return FillerComponent()
        if open_now:
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


def construct_mc_header(data):
    question_number = data.get("question_number", None)
    if question_number is None:
        return [
            TextComponent(
                text="Pilih salah satu",
                size='xs',
                margin='xs',
                color='#27ACB2'
            )
        ]
    else:
        percentage = int(round(float(question_number) / 12 * 100))
        return [
            TextComponent(
                text="Progess : {} %".format(percentage),
                size='xs',
                margin='xs',
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
                        width="{}%".format(percentage),
                        background_color='#0D8186',
                        contents=[
                            FillerComponent()
                        ]
                    )
                ],
            ),
        ]


def construct_multiple_choice(data):
    actions = []
    for button in data.get('buttons'):
        actions.append(ButtonComponent(
            style='primary',
            height='sm',
            margin='md',
            action=MessageAction(
                label=button.get('title'),
                text=button.get('title')
            )
        ))

    bubble = BubbleContainer(
        direction='ltr',
        body=BoxComponent(
            layout='vertical',
            contents=construct_mc_header(data) + [
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

