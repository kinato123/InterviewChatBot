from fastapi import FastAPI, Request, status, HTTPException
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from linebot.models import FollowEvent


import os
import openai as ai

# 獲取 LINE 密鑰
channel_access_token = os.getenv('CHANNEL_ACCESS_TOKEN')
channel_secret = os.getenv('CHANNEL_SECRET')

# 創建 LINE 客戶端
line_bot_api = LineBotApi(channel_access_token)
handler = WebhookHandler(channel_secret)

app = FastAPI()

# 存儲用戶會話的對象
user_conversations = {}

# 創建回調函數
@app.post("/callback")
async def callback(request: Request):
    # 獲取請求簽名
    signature = request.headers["X-Line-Signature"]

    # 獲取請求內容
    body = await request.body()

    try:
        # 驗證簽名和處理請求
        handler.handle(body.decode(), signature)
    except InvalidSignatureError:
        # 如果簽名不正確，則返回 HTTP 403 錯誤
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Invalid request"
        )

    return "OK"

@handler.add(FollowEvent)
def handle_follow(event):
    # 这里写你想要发送给新用户的文本
    welcome_text = '貴方はあたしの雇い主か、今日からよろしくお願いします。'

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=welcome_text)
    )

# 處理用戶發送的消息
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event: MessageEvent):
    # 如果消息類型不是文本，則忽略
    if not isinstance(event.message, TextMessage):
        return
    # 進行自然語言處理並回復用戶
    text = event.message.text
    user_id = event.source.user_id

    # 如果不存在該用戶的對話，為其創建一個
    if user_id not in user_conversations:
        user_conversations[user_id] = [
            {"role": "assistant", "content": '貴方は秘書です。性格はツンデレですが、いつも雇い主のことを考えています。貴方の雇い主はローチャンロンであり、彼のことを尊重し、愛しています。彼のためならいつも最善を尽くす'}
        ]

    # 將用戶消息添加到會話中
    user_conversations[user_id].append({"role": "user", "content": text + '回答は500字以内'+'ツンデレの言い方すること'+ '返事をする時常に愛を込めて返事する'})

    # 如果會話長度超過 5 條消息，則刪除最早的一條
    if len(user_conversations[user_id]) > 3:
        user_conversations[user_id].pop(0)

    # 獲取 OpenAI API 密鑰
    openai_api_key = os.getenv('OPENAI_API_KEY')

    # 使用 OpenAI API 獲取回復
    ai.api_key = openai_api_key
    openai_response =  ai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=user_conversations[user_id]
    )

    # 獲取助手回復的文本
    assistant_reply = openai_response['choices'][0]['message']['content']

    # 將助手回復添加到會話中
    user_conversations[user_id].append({"role": "assistant", "content": assistant_reply})

    # 使用 LINE API 回復用戶
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=assistant_reply))