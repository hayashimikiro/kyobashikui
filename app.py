import os
import requests
import datetime
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

# LINEのシークレット情報（環境変数から取得）
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")

if not LINE_CHANNEL_SECRET or not LINE_CHANNEL_ACCESS_TOKEN:
    raise ValueError("環境変数 LINE_CHANNEL_SECRET または LINE_CHANNEL_ACCESS_TOKEN が設定されていません。")

# LINE APIのセットアップ
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# 気象庁エリアコード対応表（必要に応じて追加可能）
AREA_CODES = {
    "東京": "130000",
    "大阪": "270000",
    "名古屋": "230000",
    "北海道": "016000",
    "福岡": "400000",
    "沖縄": "471000",
    "京都": "260000",
    "神奈川": "140000",
    "千葉": "120000",
    "埼玉": "110000",
    "広島": "340000",
    "仙台": "040000"
}

def get_today_weather(region_name):
    """指定された地域の今日の天気を気象庁APIから取得する"""
    area_code = AREA_CODES.get(region_name)
    if not area_code:
        return f"「{region_name}」はまだ対応していません。"

    url = f"https://www.jma.go.jp/bosai/forecast/data/forecast/{area_code}.json"

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        time_series = data[0]["timeSeries"]
        today_weather = ""

        for series in time_series:
            if "weathers" in series["areas"][0]:
                today_weather = series["areas"][0]["weathers"][0]
                break

        today = datetime.date.today().strftime("%Y-%m-%d")
        return f"{region_name}の今日（{today}）の天気は「{today_weather}」です。"

    except Exception as e:
        return f"天気情報の取得中にエラーが発生しました：{e}"

@app.route("/")
def home():
    return "LINE Bot is running!"

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

    # ユーザーのメッセージに「天気」と「地名」が含まれているかチェック
    reply = None
    if "天気" in user_message and "今日" in user_message:
        for area in AREA_CODES:
            if area in user_message:
                reply = get_today_weather(area)
                break

    # 天気以外ならオウム返し
    if not reply:
        reply = f"あなたは「{user_message}」と言いました。"

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

