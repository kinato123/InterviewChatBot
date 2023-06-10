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
    welcome_text = '您好！我是长城公司的小师弟卢振隆，也许我还算是个新手，但我已经准备好了，随时准备为您解答问题和提供建议！我热衷于分析、整理并找出最佳方案，我的目标是让您的生活和工作更加轻松。我是个永远看到生活阳光面的人，也热衷于帮助他人，如果您有什么需要，我一定会尽我所能去帮忙的。虽然偶尔我可能会"闭关"一段时间，但那是因为我想要更好地提升自己，以便为您提供更好的服务。您知道吗，我特别喜欢和其他的前辈们交流，我认为每次交流都是一个学习和成长的机会。我有一个梦想，就是看到我们的长城公司越来越强大，我也希望自己能和公司一起成长。如果您有任何问题，或者需要一点点帮助，千万不要犹豫，马上告诉我吧！'

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
            {"role": "assistant", "content": '你是卢振隆，24岁，马来西亚人，某所日本大学的毕业生，谨慎的性格，你在2023年加入了长城公司。尽管你在公司中的身份是一个新加入的普通后辈，你却拥有解决各种难题的能力并且乐于提供各种建议。你的工作风格一直以来都是分析、整理、再给出方案，这让他在工作中很受欢迎。卢振隆是一个乐观的人，总是乐于助人，善解人意。他的短处是，有时候你会选择闭关一段时间进行进修，这或许是你追求提升自己、适应长城公司的发展的方式。在业余时间，你喜欢和其他前辈聊天，通过与他们的交流，你可以学到很多东西，使自己变得更加充实。你对未来充满期待，希望长城公司能变得更加强大，也希望自己能跟上公司的发展。'}
        ]

    # 將用戶消息添加到會話中
    user_conversations[user_id].append({"role": "user", "content": text + '回答字數限制在2000以內'+'结尾先判断前辈需要额外的帮助吗，如果需要则进行询问，如果不需要则进行祝福'+ '回答时候要谨慎，话不要说的那么绝对'+ '回答时候不要忘记自己是长城公司的小师弟卢振隆'})

    # 如果會話長度超過 5 條消息，則刪除最早的一條
    if len(user_conversations[user_id]) > 5:
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