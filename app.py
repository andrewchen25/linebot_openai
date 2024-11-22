from flask import Flask, request, abort
from linebot.v3.messaging import MessagingApi
from linebot.v3.webhook import WebhookHandler
from linebot.v3.webhook.models import TextMessageContent
from linebot.v3.messaging.models import ReplyMessageRequest, TextMessage
from dotenv import load_dotenv
import os
import openai
import traceback

# 加載 .env 文件
load_dotenv()

# 初始化環境變數
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.getenv('CHANNEL_SECRET')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# 檢查環境變數是否正確設置
if not LINE_CHANNEL_ACCESS_TOKEN or not LINE_CHANNEL_SECRET or not OPENAI_API_KEY:
    raise ValueError("環境變數未正確設置，請檢查 LINE_CHANNEL_ACCESS_TOKEN, LINE_CHANNEL_SECRET 或 OPENAI_API_KEY")

# 初始化 LINE Bot 和 OpenAI API
line_bot_api = MessagingApi(channel_access_token=LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)
openai.api_key = OPENAI_API_KEY

# 初始化 Flask 應用
app = Flask(__name__)

# GPT 回應處理函數
def GPT_response(user_input):
    try:
        # 調用 OpenAI 微調模型
        response = openai.ChatCompletion.create(
            model="ft:gpt-4o-mini-2024-07-18:personal:my-qa3:AVxxWGsa",
            messages=[
                {"role": "system", "content": "這是一個提供有關台塑企業文物館準確資訊的聊天機器人。"},
                {"role": "user", "content": user_input}
            ],
            temperature=0.2,
            max_tokens=2048,
            top_p=0.9,
            frequency_penalty=0.0,
            presence_penalty=0.0
        )
        # 提取回應
        return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f"OpenAI API error: {e}")
        return "抱歉，我無法處理您的請求。請稍後再試。"

# Webhook 回調路徑
@app.route("/callback", methods=['POST'])
def callback():
    # 獲取 LINE 簽名
    signature = request.headers.get('X-Line-Signature', '')

    # 獲取請求主體
    body = request.get_data(as_text=True)
    app.logger.info(f"Request body: {body}")

    try:
        # 處理 webhook 事件
        handler.handle(body, signature)
    except Exception as e:
        app.logger.error(f"Webhook handler error: {e}")
        abort(400)

    return 'OK'

# 處理訊息事件
@handler.add(event=TextMessageContent)
def handle_message(event):
    try:
        user_message = event.message.text
        user_reply_token = event.reply_token

        # 使用 Fine-tuned 模型生成回應
        ai_response = GPT_response(user_message)

        # 建立回應訊息
        reply_message = TextMessage(text=ai_response)
        line_bot_api.reply_message(
            ReplyMessageRequest(reply_token=user_reply_token, messages=[reply_message])
        )
    except Exception as e:
        print(f"Error in message handling: {traceback.format_exc()}")
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text="發生錯誤，請稍後再試！")]
            )
        )

# 啟動 Flask 應用
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
