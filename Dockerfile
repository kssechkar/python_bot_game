FROM python:3.8-alpine
RUN pip install --upgrade pip
WORKDIR /python_bot_game
COPY . /python_bot_game
RUN pip install -r requirements.txt
CMD [ "python", "main.py" ]