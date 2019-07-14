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
def _crawl(text):
    # 여기에 함수를 구현해봅시다.
    if '반팔' in text or '티셔츠' in text:
        url = "https://store.musinsa.com/app/items/lists/001001"
        sourcecode = urllib.request.urlopen(url).read()
        soup = BeautifulSoup(sourcecode, "html.parser")
        
        image_url = []
        brand = []
        name = []
        origin_price = []
        price = []
        total_data =[]
        
        ranking = soup.find("div", class_="ranking_division ranking_cell")
        for data in ranking.find_all("div", class_="bestranking_inner li_inner"):
            for a in data.find_all("img"):
                if len(image_url) < 5:
                    image_url.append("https:" + a['src'].strip())

        for data in ranking.find_all("p", class_="item_title"):
            if len(brand) < 5:
                brand.append(data.get_text().strip())

        for data in ranking.find_all("p", class_="list_info"):
            if len(name) < 5:
                if data.get_text().find('...'):
                    name.append(data['title'].strip())
                else:
                    name.append(data.get_text().strip())
                        
        for data in ranking.find_all("p", class_="price"):
            if len(price) < 5:
                origin_price.append(data.get_text().split()[0])
                price.append(data.get_text().split()[1])
                    
                    
        total_data = [str(n+1) + '\n' + image_url[n] + '\n브랜드명 : ' + brand[n] + '\n상품 이름 : ' + name[n] + '\n원래 가격 : ' + origin_price[n] + '\n할인된 가격 : ' + price[n] for n in range(0, len(price))]
        
        message = u'\n\n'.join(total_data)
        #message = u'\n'.join(image_url)

        return message
        
    else:
        return "'키워드'를 입력해주세요!!!"


# 챗봇이 멘션을 받았을 경우
@slack_events_adaptor.on("app_mention")
def app_mentioned(event_data):
    channel = event_data["event"]["channel"]
    text = event_data["event"]["text"]

    message = _crawl(text)
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
