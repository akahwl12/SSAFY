'''
실행전에 cmd 창에서 pip install selenium 을 해주세요.

selenium 설치 후 
https://sites.google.com/a/chromium.org/chromedriver/downloads -> ChromeDriver 2.46 다운

cromdriver.exe의 경로를 37번째 줄에 추가해주세요.

line 37 : chromedriver_dir = r'첨부파일 경로\chromedriver.exe'
'''
 
 
 #-*- coding: utf-8 -*-
import json
import re
import requests
import urllib.request
import urllib.parse
import time

from bs4 import BeautifulSoup
from selenium import webdriver

from flask import Flask, request
from flask import make_response
from slack import WebClient
from slack.web.classes import extract_json
from slack.web.classes.blocks import *
from slack.web.classes.elements import *
from slack.web.classes.interactions import MessageInteractiveEvent
from slackeventsapi import SlackEventAdapter


SLACK_TOKEN = "xoxb-689196739892-691517716167-A916ayUXvR9hGYGxAdEZWKoc"
SLACK_SIGNING_SECRET = "117afd14d8cacec35cb8a61239e70304"

chromedriver_dir = r'C:\Users\student\Downloads\chromedriver_win32\chromedriver.exe'


app = Flask(__name__)
# /listening 으로 슬랙 이벤트를 받습니다.
slack_events_adaptor = SlackEventAdapter(SLACK_SIGNING_SECRET, "/listening", app)
slack_web_client = WebClient(token=SLACK_TOKEN)


# 키워드로 중고거래 사이트를 크롤링하여 가격대가 비슷한 상품을 찾은 다음,
# 메시지 블록을 만들어주는 함수입니다

def hasPlaceMainCt(soup):
    main_pack = soup.find("div", class_="main_pack")

    try:
        if main_pack.find("div")["id"] == "place_main_ct":
            return True
        else:
            return False
    except:
        return False

def first_message(keyword):
    seperate_line = SectionBlock(
        text="===========================================================",
    )
    head_section = SectionBlock(
        text="*\"" + keyword + "\" " +  "로 검색한 결과입니다.*",
    )
    button_actions = ActionsBlock(
        block_id=keyword,
        elements=[
            ButtonElement(
                text="맛집 탐방",
                action_id="0", value=str(keyword)
            ),
            ButtonElement(
                text="호텔 찾기", style="danger",
                action_id="1", value=str(keyword)
            ),
            ButtonElement(
                text="지역 정보",
                action_id="2", value=str(keyword)
            ),
        ]
    )
    return [seperate_line, head_section, button_actions]

def make_sale_message_blocks(keyword):
    query_text = ""
    for key in keyword.strip().split():
        query_text += urllib.parse.quote_plus(str(key))+'+%20'
    query_text += urllib.parse.quote_plus("맛집")
    search_url = "https://www.diningcode.com/list.php?query=" + query_text
    print('Searching : ' + search_url)
    source_code = urllib.request.urlopen(search_url).read()
    soup = BeautifulSoup(source_code, "html.parser")

    items = []
    listbox = soup.find("div",class_= "lc-list high-rank")
    # print("check2 : " )
    # print(listbox)
    onmouse = [listbox.find("li", {"onmouseenter":"setIcon("+str(n)+");"})for n in range(1,7)]
    # print("check3 : ")
    # print(onmouse)
    for item_div in onmouse:
        title = item_div.find("span", class_="btxt").get_text().strip()
        text = item_div.find("span", class_="stxt").get_text().strip()
        tagAndAdd = item_div.find_all("span", class_="ctxt")
        tags = tagAndAdd[0].get_text().strip()
        image = item_div.find("span", class_="img")["style"].replace("('", ' ').replace("')", ' ')
        image = image.split()[2]
        address = tagAndAdd[1].get_text().strip()
        items.append({
            "title": title,
            "text": text,
            "tags": tags,
            "image": image,
            "address": address,
        })
    print("items!!!!")
    print(items)


    # items.sort(key=lambda item: abs(price - int(item["price"].replace(",", ""))))

    # 메시지를 꾸밉니다
    # 처음 섹션에는 제목과 첫 번째 상품의 사진을 넣습니다

    returnLis = []

    head_section = SectionBlock(
        text="*" + "="*24 + "  맛집 리스트  " + "="*25 + "*"
    )
    returnLis.append(head_section)

    # 두 번째 섹션에는 처음 10개의 상품을 제목 링크/내용으로 넣습니다
    item_fields = []
    restaurant_num = 5
    for item in items[:restaurant_num]:
        # 첫 줄은 제목 링크, 두 번째 줄은 게시일과 가격을 표시합니다.
        query_text = ""
        for key in keyword.strip().split()[1:]:
            query_text += urllib.parse.quote_plus(str(key)) + '+'
        query_text += urllib.parse.quote_plus(item["title"].split()[1])
        search_url = "https://search.naver.com/search.naver?query=" + query_text
        text = "*<"+search_url+"|" +item["title"] + ">*"
        text += "\n*<메뉴> /* " +str(item["text"])
        text += "\n*<태그> /* " + str(item["tags"])
        text += "\n*<주소> /* " + str(item["address"])
        item_fields.append(text)

    for i in range(restaurant_num):
        a = SectionBlock(
            text = item_fields[i],
            accessory = ImageElement(
                image_url=items[i]["image"],
                alt_text = keyword
            )
        )
        returnLis.append(a)

    button_actions = ActionsBlock(
        block_id=keyword,
        elements=[
            ButtonElement(
                text="한식",
                action_id="한식", value=str(keyword)
            ),
            ButtonElement(
                text="양식", 
                action_id="양식", value=str(keyword)
            ),
            ButtonElement(
                text="중식",
                action_id="중식", value=str(keyword)
            ),
            ButtonElement(
                text="술집",
                action_id="술집", value=str(keyword)
            ),
        ]
    )
    returnLis.append(button_actions)
    return returnLis

def make_hotel_message_blocks(text):
    query = urllib.parse.quote('%20'.join(text.split()))
    driver.get("http://search-tour.interpark.com/PC/Result?search=" + query + "&code1=H&code2=") # 인터파크 호텔 URL로 이동하기

    source_code = driver.page_source
    soup = BeautifulSoup(source_code, 'html.parser')
    time.sleep(1)

    items = []

    overlap = 0

    if "건" not in soup.find("h4", class_="mainTxt").get_text():
        return -1

    for data in soup.find_all("li", class_="boxItem"):
        if len(items) == 5:
            break
        title = data.find("p", class_="proSub").get_text().strip()
        link = data.find("h5", class_="proTit")['onclick'].strip()
        link = link.replace("searchModule.OnClickDetail('","")
        link = link.replace("','')","")
        for i in items:
            if link in i['link']:
                overlap = 1
        if overlap:
            overlap = 0
            continue
        address = data.find("p", class_="proInfo").get_text().strip()
        image = data.find("img", class_="img")['src'].strip()

        item_price = str(data.find("strong", class_="proPrice"))
        pos1 = item_price.find('>')
        pos2 = item_price.find('<i class="unit')
        item_price = item_price[pos1+1 : pos2].strip() + " 원"

        items.append({
            "image": image,
            "title": title,
            "link": link,
            "address": address,
            "price": item_price,
        })


    sections = []
    images = []

    for i in range(len(items)):
        images.insert(i, ImageElement(image_url=items[i]["image"], alt_text="호텔 사진"))

        sections.append(SectionBlock(
            accessory=images[i],
            text = "*<" + items[i]["link"] + "|" + items[i]["title"] + ">*\n\n가격 " + items[i]['price'] + '\n\n[주소 : ' + items[i]['address'] + ']'
        ))

    sections.insert(0, SectionBlock(
        text = "*" + "="*25 + "  호텔 목록  " + "="*25 + "*"
    ))

    sections += first_message(text)
    
    return sections


def _crawl_find_map(user_input):
    return_list = []

    # 여기에 함수를 구현해봅시다.
    # base_url = "https://search.naver.com/search.naver?sm=top_hty&fbm=1&ie=utf8&query="
    base_url = "https://search.naver.com/search.naver?sm=top_hty&ie=utf8&query="
    print("input check1 :", user_input)

    user_input = user_input.strip()
    print(user_input)
    inn = user_input
    print("input check2 :", user_input)

    user_input = user_input.replace(" ", "+")

    print("input check3 :", user_input)

    print("input check4 :", user_input)
    user_input = urllib.parse.quote(user_input)
    url = base_url + user_input

    print("url 체크:", url)
    # url에 한글이 들어가 있으니 인코딩을 해준다.

    source_code = urllib.request.urlopen(url).read()
    soup = BeautifulSoup(source_code, "html.parser")

    return_list.append("<" + url + "|네이버 검색>")

    images = []
    
    # 확장성을 위해 lcs_greenmap 부터 시작함
    try:
     # 결과 폼이 place_main_ct를 갖는지 확인하는 함수
        if hasPlaceMainCt(soup):
            # 장소정보 가져오기
            print('hasPlaceMainCt가 있습니다.')
            place_main_ct = soup.find("div", id="place_main_ct")
            result_url = place_main_ct.find("a", class_="api_more_theme")["href"]
            return_list.append("<" + result_url + "|장소정보>")
            # return_list.append("장소정보 : " +  result_url)

            # 네이버지도 가져오기
            result_loc = place_main_ct.find("a", class_="btn")["href"]  
            return_list.append("<" + result_loc + "|네이버 길찾기>")
            # return_list.append("네이버 길찾기 : " + result_loc)

            driver.get(result_url)

            print("url 성공 : ",result_url)
            image = driver.find_element_by_xpath('//*[@id="container"]/div[1]/div/div/div[3]/div/div[1]/div/a/img')
            image = image.get_attribute('src')
            print("image url=",image)
            images.append(ImageElement(image_url=image, alt_text="플레이스 사진"))

        else:
            # 장소정보 가져오기
            print('hasPlaceMainCt가 없습니다. 테스트3:08')
            container = soup.find("div", id="container")
            print('[4/1]container 가져옴!')
            local_map = container.find("div", class_="local_map")
            print('[4/2]local_map도 가져옴!')

            info_area = local_map.find("dl", class_="info_area")
            print("[4/3]info_area 다 와간다!")
            result_url = info_area.find("a")["href"]

            # return_list.append("장소정보 : " +  result_url)
            return_list.append("<" + result_url + "|장소정보>")
            print("[4/4]장소정보 저장 완료 : " + result_url)

            # 네이버지도 가져오기
            inline = info_area.find("dd", class_="txt_inline")
            print("inline 접속")

            result_loc = inline.find_all("a")[1]["href"]
            print("result_loc 구함")

            # return_list.append("네이버 길찾기 : " + result_loc)
            return_list.append("<" + result_loc + "|네이버 길찾기>")

            
    except:
        print("에러 떳어욤")
        return -1

    print("장소정보는 : ", result_url)

    sections = []

    sections.insert(0, SectionBlock(
        text = "*" + "="*25 + "  지역 정보  " + "="*25 + "*"
    ))

    if len(images) > 0:
        sections.append(SectionBlock(
            text = u'\n'.join(return_list),
            accessory = images[0]
        ))
    else:
        sections.append(SectionBlock(
            text = u'\n'.join(return_list)
        ))

    sections += first_message(inn)

    return sections


prev_client_msg_id = {}

# 챗봇이 멘션을 받으면 중고거래 사이트를 검색합니다
@slack_events_adaptor.on("app_mention")
def app_mentioned(event_data):
    
    

    print('app_mentioned event data:', event_data)
    channel = event_data["event"]["channel"]
    text = event_data["event"]["text"]
    client_msg_id = event_data["event"]["client_msg_id"]

    keyword = ""
    for key in text.strip().split()[1:]:
        keyword += (str(key))+' '

    print('client message id:', client_msg_id)
    if client_msg_id not in prev_client_msg_id:
        prev_client_msg_id[client_msg_id] = 1
    else:
        print('=' * 50, 'PLEASE NO RETRY', '=' * 50)
        resp = make_response('no-retry', 200)
        resp.headers["X-Slack-No-Retry"] = 1
        return resp

    # 입력한 텍스트에서 검색 키워드와 가격대를 뽑아냅니다.
    # 중고거래 사이트를 크롤링하여 가격대가 비슷한 상품을 찾아옵니다.
    message_blocks = first_message(keyword)

    # 메시지를 채널에 올립니다
    slack_web_client.chat_postMessage(
        channel=channel,
        blocks=extract_json(message_blocks)
    )


# 사용자가 버튼을 클릭한 결과는 /click 으로 받습니다
# 이 기능을 사용하려면 앱 설정 페이지의 "Interactive Components"에서
# /click 이 포함된 링크를 입력해야 합니다.
@app.route("/click", methods=["GET", "POST"])
def on_button_click():
    # 버튼 클릭은 SlackEventsApi에서 처리해주지 않으므로 직접 처리합니다
    payload = request.values["payload"]
    click_event = MessageInteractiveEvent(json.loads(payload))

    func_Name = click_event.action_id
    user_input = click_event.value

    print('block id type:', type(func_Name))
    # 다른 가격대로 다시 크롤링합니다.
    if func_Name == '0':
        message_blocks = make_sale_message_blocks(user_input)
        slack_web_client.chat_postMessage(
            channel=click_event.channel.id,
            blocks=extract_json(message_blocks)
        )
    elif func_Name == '1':
        message_blocks =  make_hotel_message_blocks(user_input)
        if message_blocks == -1:
            slack_web_client.chat_postMessage(
                channel=click_event.channel.id,
                text = u"*검색결과가 없습니다.. 다시 입력해주세요*"
            )
        else:
            slack_web_client.chat_postMessage(
                channel=click_event.channel.id,
                blocks=extract_json(message_blocks)
            )
    elif func_Name == '2':
        message =  _crawl_find_map(user_input)
        if message == -1:
            slack_web_client.chat_postMessage(
                channel=click_event.channel.id,
                text = u"띄워쓰기를 다시 하거나 좀 더 상세한 주소를 입력해 주세요."
            )
        else:
            slack_web_client.chat_postMessage(
                channel=click_event.channel.id,
                blocks=extract_json(message)
            )
    elif func_Name in ["한식","중식","양식","술집"]:
        message_blocks = make_sale_message_blocks(str(user_input)+" "+ str(func_Name))
        slack_web_client.chat_postMessage(
            channel=click_event.channel.id,
            blocks=extract_json(message_blocks)
        )

    # 메시지를 채널에 올립니다


    # Slack에게 클릭 이벤트를 확인했다고 알려줍니다
    return "OK", 200


# / 로 접속하면 서버가 준비되었다고 알려줍니다.
@app.route("/", methods=["GET"])
def index():
    return "<h1>Server is ready.</h1>"


if __name__ == '__main__':
    options = webdriver.ChromeOptions()
    options.add_argument('headless')
    options.add_argument('window-size=1920x1080')
    options.add_argument("disable-gpu")

    driver = webdriver.Chrome(chromedriver_dir, chrome_options=options)
    driver.implicitly_wait(3)

    app.run('0.0.0.0', port=5000)