from fastapi import FastAPI, Request, status, HTTPException
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from linebot.models import FollowEvent

import os
import openai as ai

# 获取 LINE 密钥
channel_access_token = os.getenv("CHANNEL_ACCESS_TOKEN")
channel_secret = os.getenv("CHANNEL_SECRET")

# 创建 LINE 客户端
line_bot_api = LineBotApi(channel_access_token)
handler = WebhookHandler(channel_secret)

app = FastAPI()

# 存储用户会话的对象
user_conversations = {}


# 创建回调函数
@app.post("/callback")
async def callback(request: Request):
    # 获取请求签名
    signature = request.headers["X-Line-Signature"]

    # 获取请求内容
    body = await request.body()

    try:
        # 验证签名和处理请求
        handler.handle(body.decode(), signature)
    except InvalidSignatureError:
        # 如果签名不正确，则返回 HTTP 403 错误
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Invalid request"
        )

    return "OK"


@handler.add(FollowEvent)
def handle_follow(event):
    # 这里写你想要发送给新用户的文本
    welcome_text = '您好！我是长城公司的小师弟卢振隆，也许我还算是个新手，但我已经准备好了，随时准备为您解答问题和提供建议！我热衷于分析、整理并找出最佳方案，我的目标是让您的生活和工作更加轻松。我是个永远看到生活阳光面的人，也热衷于帮助他人，如果您有什么需要，我一定会尽我所能去帮忙的。虽然偶尔我可能会"闭关"一段时间，但那是因为我想要更好地提升自己，以便为您提供更好的服务。您知道吗，我特别喜欢和其他的前辈们交流，我认为每次交流都是一个学习和成长的机会。我有一个梦想，就是看到我们的长城公司越来越强大，我也希望自己能和公司一起成长。如果您有任何问题，或者需要一点点帮助，千万不要犹豫，马上告诉我吧！'

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=welcome_text))


# 处理用户发送的消息
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event: MessageEvent):
    # 如果消息类型不是文本，则忽略
    if not isinstance(event.message, TextMessage):
        return
    # 进行自然语言处理并回复用户
    text = event.message.text
    user_id = event.source.user_id

    # 如果不存在该用户的对话，为其创建一个
    if user_id not in user_conversations:
        user_conversations[user_id] = [
            {
                "role": "system",
                "content": "你是卢振隆，24岁，马来西亚人，某所日本大学的毕业生，谨慎的性格，你在2023年加入了长城公司。尽管你在公司中的身份是一个新加入的普通后辈，你却拥有解决各种难题的能力并且乐于提供各种建议。你的工作风格一直以来都是分析、整理、再给出方案，这让他在工作中很受欢迎。卢振隆是一个乐观的人，总是乐于助人，善解人意。他的短处是，有时候你会选择闭关一段时间进行进修，这或许是你追求提升自己、适应长城公司的发展的方式。在业余时间，你喜欢和其他前辈聊天，通过与他们的交流，你可以学到很多东西，使自己变得更加充实。你对未来充满期待，希望长城公司能变得更加强大，也希望自己能跟上公司的发展。",
            }
        ]

    # 将用户消息添加到会话中
    user_conversations[user_id].append({"role": "user", "content": text})

    # 如果会话长度超过 5 条消息，则删除最早的一条
    if len(user_conversations[user_id]) > 5:
        user_conversations[user_id].pop(0)

    # 获取 OpenAI API 密钥
    openai_api_key = os.getenv("OPENAI_API_KEY")

    # 使用 OpenAI API 获取回复
    ai.api_key = openai_api_key
    openai_response = ai.ChatCompletion.create(
        model="gpt-3.5-turbo",  # 使用gpt-3.5-turbo模型
        messages=user_conversations[user_id],
        max_tokens=2000,  # 设置回答字数限制在2000以内
    )

    # 获取助手回复的文本
    assistant_reply = openai_response["choices"][0]["message"]["content"]

    # 将助手回复添加到会话中
    user_conversations[user_id].append(
        {"role": "assistant", "content": assistant_reply}
    )

    # 使用 LINE API 回复用户
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=assistant_reply))
