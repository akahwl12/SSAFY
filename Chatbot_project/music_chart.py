# -*- coding: utf-8 -*-
import re
import urllib.request

from bs4 import BeautifulSoup

from flask import Flask
from slack import WebClient
from slackeventsapi import SlackEventAdapter


SLACK_TOKEN = "xoxb-689196739892-691517716167-A916ayUXvR9hGYGxAdEZWKoc"
SLACK_SIGNING_SECRET = "117afd14d8cacec35cb8a61239e70304"


app = Flask(__name__)
# /listening 으로 슬랙 이벤트를 받습니다.
slack_events_adaptor = SlackEventAdapter(SLACK_SIGNING_SECRET, "/listening", app)
slack_web_client = WebClient(token=SLACK_TOKEN)


# 크롤링 함수 구현하기
def _crawl_music_chart(text):
    if not "music" in text:
        return "`@<봇이름> music` 과 같이 멘션해주세요.!!!!"

    # 여기에 함수를 구현해봅시다.
    url = "https://music.bugs.co.kr/chart"
    sourcecode = urllib.request.urlopen(url).read()
    soup = BeautifulSoup(sourcecode, "html.parser")

    title = []
    artist = []
    
    total_data = []
    
    for data in soup.find_all("p", class_="title"):
        if not data.get_text() in title:
            if len(title) < 10:
                title.append(data.get_text().strip())
    
    for data in soup.find_all("p", class_="artist"):
        if not data.get_text() in artist:
            condition = data.get_text().find('\n\n\r\n')
            if len(artist) < 10:
                if(condition):
                    artist.append(data.get_text()[:condition].strip())
                else:
                    artist.append(data.get_text().strip())
    
    total_data = [str(n+1) + "위 : " + title[n] + "  -  " + artist[n] for n in range(0, len(title))]
            
    message = u'\n'.join(total_data)

    return message


# 챗봇이 멘션을 받았을 경우
@slack_events_adaptor.on("app_mention")
def app_mentioned(event_data):
    channel = event_data["event"]["channel"]
    text = event_data["event"]["text"]

    message = _crawl_music_chart(text)
    slack_web_client.chat_postMessage(
        channel=channel,
        text=message
    )


# / 로 접속하면 서버가 준비되었다고 알려줍니다.
@app.route("/", methods=["GET"])
def index():
    return "<h1>Server is ready.</h1>"


if __name__ == '__main__':
    app.run('0.0.0.0', port=5000)
