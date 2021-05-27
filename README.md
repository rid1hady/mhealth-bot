# Psymax

<img align="right" src="psymax.png" alt="Psymax Logo" width="150px"/>

`Psymax`, took its name after Baymax from Big Hero 6, is a mental health bot written in Indonesian Language, aim specifically to assess student's mental health condition. `Psymax` was build with Rasa Framework and specially designed to work on Line.

## Table of Contents

- [Psymax](#psymax)
  - [Table of Contents](#table-of-contents)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
    - [Docker](#docker)
    - [Non Docker](#non-docker)
  - [Troubleshoot](#troubleshoot)
    - [Error Read Env Value on YML](#error-read-env-value-on-yml)

## Prerequisites

Because pysmax was specially designed for Line, you need to create a Line Channel first for your bot. You can follow this [guideline](https://developers.line.biz/en/docs/messaging-api/getting-started/#using-console) to create a channel on Line.

## Installation

1. Clone this repository
2. Copy `.env.example` to `.env` and write your config

### Docker

if you are using docker, I already provide `docker-compose.yml` that you can run by executing the following command.

```bash
docker-compose up -d
```

### Non Docker

For non-docker user.

1. Create a python virtual env with python version 3.8
2. Install all the requirement file by executing

    ```bash
    pip install -r requirements.txt
    pip install -r actions/requirements-actions.txt
    ```

3. Validating rasa installation by execute

    ```bash
    rasa --version
    ```

    will print something like this

    ```shell
    Rasa Version     : 2.4.0
    Rasa SDK Version : 2.4.0
    Rasa X Version   : None
    Python Version   : 3.8.8
    Operating System : Windows-10-10.0.19041-SP0
    Python Path      : c:\users\ridwa\.conda\envs\rasa\python.exe
    ```

4. Run actions
  
    ```bash
    rasa run actions
    ```

5. Train model and run server

    ```bash
    rasa train && rasa run
    ```

## Troubleshoot

### Error Read Env Value on YML

You need to load your .env value to system first before running the rasa apps since `.yml` file only read from existing env value on your system.

However, you can run the following simple script depending on your system.

- Windows User

    ```bash
    for /F %A in (.env) do SET %A
    ```
