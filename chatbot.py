from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
from openai import OpenAI
import threading

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

# 设置你的OpenAI API密钥

client = OpenAI(
    api_key = "sk-cwWC5XQUTr6yXD66qeyHERoczacTxCe1J3TgcmMCYa8waFGx",
    base_url = "https://api.fe8.cn/v1"
)

# openai.api_key = ''
# openai.base_url = "https://api.fe8.cn/v1"

# 用于存储对话上下文的字典，键为用户的 IP 地址
contexts = {}

# 创建一个锁对象
lock = threading.Lock()

@app.route('/')
def index():
    return render_template('index.html')

def process_message(message, session_id):
    # 获取当前会话的上下文
    context = contexts.get(session_id, [])
    prompt = '\n'.join([f"Human: {m}\nAI: {r}" for m, r in context]) + f"\nHuman: {message}\nAI:"

    # 使用锁确保 GPT 接口的线性调用
    with lock:
	    chat_completion = client.chat.completions.create(
	        messages=[
	            {
	                "role": "user",
	                "content": prompt,
	            }
	        ],
	        model="gpt-3.5-turbo", #此处更换其它模型,请参考模型列表 eg: google/gemma-7b-it
            stream=True,
	    )

    # 逐步产生响应并通过Socket.IO发送给客户端
    response = ""
    for chunk in chat_completion:
        response_part = chunk.choices[0].delta.content or ""
        emit('response', {'response': response_part})
        response += response_part

        print(chunk.choices[0].delta.content or "", end="")

    print(session_id+"::question:"+prompt)
    print(session_id+ "::answer:"+response)

    return response

@socketio.on('message')
def handle_message(data):
    session_id = request.sid
    message = data['message']

    # 获取当前会话的上下文
    context = contexts.get(session_id, [])

    # 处理消息并生成响应
    response = process_message(message, session_id)

    # 更新上下文，保持最多6轮对话
    context.append((message, response))
    contexts[session_id] = context[-3:]

    # 向客户端发送响应
#    emit('response', {'response': response})

if __name__ == '__main__':
    socketio.run(app, debug=True)
