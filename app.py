import os
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

# 環境変数からLINEのシークレット情報を取得
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")

if not LINE_CHANNEL_SECRET or not LINE_CHANNEL_ACCESS_TOKEN:
    raise ValueError("環境変数 LINE_CHANNEL_SECRET または LINE_CHANNEL_ACCESS_TOKEN が設定されていません。")

# LINE APIのセットアップ
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

@app.route("/")
def home():
    return "LINE Bot is running!"

@app.route("/webhook", methods=["POST"])
def webhook():
    # X-Line-Signatureヘッダーの取得
    signature = request.headers.get("X-Line-Signature")

    # リクエストのボディ取得
    body = request.get_data(as_text=True)
    print("Received Signature:", signature)
    print("Received Body:", body)  

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    """ 受け取ったメッセージをそのまま返す（オウム返し機能） """
    user_message = event.message.text  # ユーザーからのメッセージ
    reply_message = f"あなたは「{user_message}」と言いました。"  # 返信内容
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_message))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)