from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import *
import os
import openai
import traceback
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
line_bot_api = LineBotApi(os.getenv('CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('CHANNEL_SECRET'))
openai.api_key = os.getenv('OPENAI_API_KEY')

def GPT_response(text):
    response = openai.ChatCompletion.create(
        model="ft:gpt-4o-mini-2024-07-18:personal:my-qa3:AVxxWGsa",
        messages=[
            {"role": "system", "content": "這是一個提供有關台塑企業文物館準確資訊的聊天機器人。"},
            {"role": "user", "content": text}
        ],
        temperature=0.2,
        max_tokens=2048,
        top_p=0.9,
        frequency_penalty=0.0,
        presence_penalty=0.0
    )
    answer = response['choices'][0]['message']['content']
    return answer

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    msg = event.message.text
    try:
        GPT_answer = GPT_response(msg)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(GPT_answer))
    except Exception as e:
        print(traceback.format_exc())
        line_bot_api.reply_message(event.reply_token, TextSendMessage('系統錯誤，請稍後再試'))

@handler.add(PostbackEvent)
def handle_postback(event):
    print(event.postback.data)

@handler.add(MemberJoinedEvent)
def welcome_new_member(event):
    try:
        uid = event.joined.members[0].user_id
        gid = event.source.group_id
        profile = line_bot_api.get_group_member_profile(gid, uid)
        name = profile.display_name
        message = TextSendMessage(text=f'{name}歡迎加入')
        line_bot_api.reply_message(event.reply_token, message)
    except LineBotApiError as e:
        print(f"Error getting profile: {str(e)}")

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
