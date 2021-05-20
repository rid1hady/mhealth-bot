FROM rasa/rasa:2.4.0-full

WORKDIR /app

COPY requirements.txt ./

USER root

RUN apt-get update -qq && \
  apt-get install -y --no-install-recommends \
  python3 \
  python3-venv \
  python3-pip \
  python3-dev \
  && apt-get autoremove -y

RUN apt-get update && apt-get dist-upgrade -y --no-install-recommends

RUN pip install -r requirements.txt

COPY ./connectors /app/connectors

COPY ./config.yml ./

RUN rasa train

COPY ./models /app/models

USER 1001

CMD ["run"]
