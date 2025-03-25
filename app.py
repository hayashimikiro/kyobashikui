import os
import re
import requests
import datetime
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

# LINEのシークレット情報
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")

if not LINE_CHANNEL_SECRET or not LINE_CHANNEL_ACCESS_TOKEN:
    raise ValueError("LINEの環境変数が設定されていません。")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# 気象庁のエリアコード（47都道府県対応）
AREA_CODES = {
    "北海道": "016000", "青森": "020000", "岩手": "030000", "宮城": "040000", "秋田": "050000",
    "山形": "060000", "福島": "070000", "茨城": "080000", "栃木": "090000", "群馬": "100000",
    "埼玉": "110000", "千葉": "120000", "東京": "130000", "神奈川": "140000", "新潟": "150000",
    "富山": "160000", "石川": "170000", "福井": "180000", "山梨": "190000", "長野": "200000",
    "岐阜": "210000", "静岡": "220000", "愛知": "230000", "三重": "240000", "滋賀": "250000",
    "京都": "260000", "大阪": "270000", "兵庫": "280000", "奈良": "290000", "和歌山": "300000",
    "鳥取": "310000", "島根": "320000", "岡山": "330000", "広島": "340000", "山口": "350000",
    "徳島": "360000", "香川": "370000", "愛媛": "380000", "高知": "390000", "福岡": "400000",
    "佐賀": "410000", "長崎": "420000", "熊本": "430000", "大分": "440000", "宮崎": "450000",
    "鹿児島": "460100", "沖縄": "471000"
}

def get_weather(region_name, day="today"):
    """指定地域と日付の天気を取得"""
    code = AREA_CODES.get(region_name)
    if not code:
        return f"「{region_name}」は対応していません。"

    url = f"https://www.jma.go.jp/bosai/forecast/data/forecast/{code}.json"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        # 対象日 index を決定
        if day == "today":
            index = 0
        elif day == "tomorrow":
            index = 1
        elif day == "yesterday":
            return f"申し訳ありません、「昨日の天気」は取得できません（気象庁の仕様上）。"
        else:
            return "日付の指定が不明です。"

        series = data[0]["timeSeries"]
        for s in series:
            if "weathers" in s["areas"][0]:
                weather = s["areas"][0]["weathers"][index]
                date = (datetime.date.today() + datetime.timedelta(days=index)).strftime("%Y-%m-%d")
                return f"{region_name}の{day_jp(day)}（{date}）の天気は「{weather}」です。"
        return "天気情報が見つかりませんでした。"

    except Exception as e:
        return f"天気情報の取得中にエラーが発生しました：{e}"

def day_jp(keyword):
    return {
        "today": "今日",
        "tomorrow": "明日",
        "yesterday": "昨日"
    }.get(keyword, "不明")

def extract_info(user_text):
    """メッセージから地域と日付のキーワードを抽出"""
    region = None
    day = "today"

    # 都道府県名を抽出
    for area in AREA_CODES:
        if area in user_text:
            region = area
            break

    # 日付ワード抽出
    if "明日" in user_text:
        day = "tomorrow"
    elif "昨日" in user_text:
        day = "yesterday"
    # 「天気は？」→ 今日とみなす

    return region, day

@app.route("/")
def home():
    return "LINE天気Botが動作中です"

@app.route("/webhook", methods=["POST"])
def webhook():
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text

    # 地名と日付を解析
    region, day = extract_info(user_message)

    if "天気" in user_message and region:
        reply = get_weather(region, day)
    elif "天気" in user_message:
        reply = "どこの地域の天気か教えてください。例：「東京の天気は？」"
    else:
        reply = f"あなたは「{user_message}」と言いました。"

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
