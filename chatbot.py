from flask import request
from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import openai
import re

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

# 用于存储对话上下文的字典，键为session_id
contexts = {}

@app.route('/')
def index():
    return render_template('index.html')

def process_message(message, session_id):
    # 这里可以加入自己的对话处理逻辑
    response = f"你说: {message}"
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
    contexts[session_id] = context[-6:]

    # 向客户端发送响应
    emit('response', {'response': response})

if __name__ == '__main__':
    socketio.run(app, debug=True)
