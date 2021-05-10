FROM rasa/rasa-sdk:2.4.0

WORKDIR /app

COPY actions/requirements-actions.txt ./

USER root

RUN apt-get update -qq && \
  apt-get install -y --no-install-recommends \
  python3 \
  python3-venv \
  python3-pip \
  python3-dev \
  # required by psycopg2 at build and runtime
  libpq-dev \
  # required for health check
  curl \
  && apt-get autoremove -y

RUN apt-get update && apt-get dist-upgrade -y --no-install-recommends

RUN pip install -r requirements-actions.txt

COPY ./actions /app/actions

RUN pip install . --no-cache-dir

# Don't use root user to run code
USER 1001

CMD ["start", "--actions", "actions.actions"]
