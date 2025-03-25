# File: app/routes.py
from flask import Blueprint, jsonify, request, render_template, current_app, stream_with_context, Response
from app.models import Conversation, Message
from datetime import datetime
from openai import OpenAI
import json

main = Blueprint('main', __name__)


@main.route('/')
def index():
    return render_template('index.html')


@main.route('/api/conversations', methods=['GET'])
def get_conversations():
    conversations = Conversation.get_all()
    result = []
    for conv in conversations:
        result.append({
            'id': conv['id'],
            'title': conv['title'],
            'created_at': conv['created_at']
        })
    return jsonify(result)


@main.route('/api/conversations', methods=['POST'])
def create_conversation():
    title = datetime.now().strftime("%Y%m%d_%H%M%S")
    conversation_id = Conversation.create(title)

    # Add system message
    # system_content = f"当前时间为:{datetime.now().strftime('%Y%m%d_%H%M%S')}作为参考。你的回答在大部分情况下应该使用汉语。在每个输出中，使用以下格式：\n\n**************************************\n\n{{content}}"
    system_content = current_app.config['SYSTEM_PROMPT']
    Message.create(conversation_id, "system", system_content)

    return jsonify({
        'id': conversation_id,
        'title': title
    })


@main.route('/api/conversations/<int:conversation_id>', methods=['DELETE'])
def delete_conversation(conversation_id):
    Conversation.delete(conversation_id)
    return jsonify({'success': True})


@main.route('/api/conversations/<int:conversation_id>/messages', methods=['GET'])
def get_messages(conversation_id):
    messages = Message.get_by_conversation(conversation_id)
    result = []
    for msg in messages:
        result.append({
            'id': msg['id'],
            'role': msg['role'],
            'content': msg['content'],
            'created_at': msg['created_at']
        })
    return jsonify(result)


# @main.route('/api/conversations/<int:conversation_id>/messages', methods=['POST'])
# def create_message(conversation_id):
#     content = request.json.get('content', '')
#
#     # Save user message
#     Message.create(conversation_id, 'user', content)
#
#     # Get all messages for this conversation to maintain context
#     db_messages = Message.get_by_conversation(conversation_id)
#     messages = []
#     for msg in db_messages:
#         messages.append({
#             'role': msg['role'],
#             'content': msg['content']
#         })
#
#     # Generate AI response
#     client = OpenAI(
#         api_key=current_app.config['DEEPSEEK_API_KEY'],
#         base_url=current_app.config['DEEPSEEK_BASE_URL']
#     )
#
#     response = client.chat.completions.create(
#         model=current_app.config['DEEPSEEK_MODEL'],
#         messages=messages,
#         temperature=current_app.config['DEEPSEEK_TEMPERATURE'],
#     )
#
#     ai_content = response.choices[0].message.content
#
#     # Save AI response
#     Message.create(conversation_id, 'assistant', ai_content)
#
#     return jsonify({
#         'content': ai_content
#     })
#
# @main.route('/api/conversations/<int:conversation_id>/stream', methods=['POST'])
# def stream_message(conversation_id):
#     content = request.json.get('content', '')
#
#     # Save user message
#     Message.create(conversation_id, 'user', content)
#
#     # Get all messages for this conversation to maintain context
#     db_messages = Message.get_by_conversation(conversation_id)
#     messages = []
#     for msg in db_messages:
#         messages.append({
#             'role': msg['role'],
#             'content': msg['content']
#         })
#
#     # Generate AI response
#     client = OpenAI(
#         api_key=current_app.config['DEEPSEEK_API_KEY'],
#         base_url=current_app.config['DEEPSEEK_BASE_URL']
#     )
#
#     def generate():
#         full_response = ""
#
#         # 使用流式响应
#         response = client.chat.completions.create(
#             model=current_app.config['DEEPSEEK_MODEL'],
#             messages=messages,
#             temperature=current_app.config['DEEPSEEK_TEMPERATURE'],
#             stream=True  # 启用流式响应
#         )
#
#         for chunk in response:
#             if chunk.choices and chunk.choices[0].delta.content:
#                 content_chunk = chunk.choices[0].delta.content
#                 full_response += content_chunk
#                 yield f"data: {json.dumps({'content': content_chunk})}\n\n"
#
#         # 保存完整响应到数据库
#         Message.create(conversation_id, 'assistant', full_response)
#         yield f"data: {json.dumps({'done': True})}\n\n"
#
#     return Response(stream_with_context(generate()), mimetype='text/event-stream')
#

@main.route('/api/conversations/<int:conversation_id>/messages', methods=['POST'])
def create_message(conversation_id):
    content = request.json.get('content', '')

    # 保存用户消息
    Message.create(conversation_id, 'user', content)

    return jsonify({'success': True})


@main.route('/api/conversations/<int:conversation_id>/stream', methods=['GET'])
def stream_message(conversation_id):
    # 获取此对话的所有消息以维持上下文
    db_messages = Message.get_by_conversation(conversation_id)
    messages = []
    for msg in db_messages:
        messages.append({
            'role': msg['role'],
            'content': msg['content']
        })

    def generate():
        # 设置 SSE 头部
        yield "event: start\ndata: {}\n\n"

        # 创建 OpenAI 客户端
        client = OpenAI(
            api_key=current_app.config['DEEPSEEK_API_KEY'],
            base_url=current_app.config['DEEPSEEK_BASE_URL']
        )

        # 生成流式响应
        full_response = ""
        try:
            response = client.chat.completions.create(
                model=current_app.config['DEEPSEEK_MODEL'],
                messages=messages,
                temperature=current_app.config['DEEPSEEK_TEMPERATURE'],
                stream=True  # 启用流式输出
            )

            for chunk in response:
                if hasattr(chunk.choices[0].delta, 'content') and chunk.choices[0].delta.content:
                    content_chunk = chunk.choices[0].delta.content
                    full_response += content_chunk
                    yield f"data: {json.dumps({'content': content_chunk})}\n\n"

            # 保存完整响应到数据库
            Message.create(conversation_id, 'assistant', full_response)

            # 发送完成事件
            yield f"event: done\ndata: {json.dumps({'content': full_response})}\n\n"

        except Exception as e:
            error_msg = str(e)
            yield f"event: error\ndata: {json.dumps({'error': error_msg})}\n\n"
            print(f"Error in stream: {error_msg}")

    return Response(stream_with_context(generate()),
                    mimetype='text/event-stream',
                    headers={
                        'Cache-Control': 'no-cache',
                        'X-Accel-Buffering': 'no',
                        'Connection': 'keep-alive',
                        'Content-Type': 'text/event-stream'
                    })
