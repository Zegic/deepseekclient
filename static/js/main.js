document.addEventListener('DOMContentLoaded', function() {
    let currentConversationId = null;
    const chatContainer = document.getElementById('chat-container');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');
    const newChatButton = document.getElementById('new-chat');
    const conversationList = document.getElementById('conversation-list');
    const welcomeMessage = document.getElementById('welcome-message');

    // 当前的 EventSource 对象
    let currentEventSource = null;

    // 加载对话列表
    loadConversations();

    // 事件监听器
    newChatButton.addEventListener('click', createNewConversation);
    sendButton.addEventListener('click', sendMessage);
//    userInput.addEventListener('keydown', function(e) {
//        if (e.key === 'Enter' && !e.shiftKey) {
//            e.preventDefault();
//            sendMessage();
//        }
//    });

    // 自动调整文本区域大小
    userInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
    });

    // 函数
    function loadConversations() {
        fetch('/api/conversations')
            .then(response => response.json())
            .then(conversations => {
                conversationList.innerHTML = '';
                conversations.forEach(conversation => {
                    const item = document.createElement('div');
                    item.className = 'conversation-item';
                    if (currentConversationId === conversation.id) {
                        item.classList.add('active');
                    }
                    item.dataset.id = conversation.id;
                    item.innerHTML = `
                        ${conversation.title}
                        <button class="delete-conversation" data-id="${conversation.id}">×</button>
                    `;

                    // 使用事件委托处理点击
                    item.onclick = function(e) {
                        if (e.target.classList.contains('delete-conversation')) {
                            deleteConversation(e.target.dataset.id);
                            e.stopPropagation();
                        } else {
                            loadConversation(conversation.id);
                        }
                    };

                    conversationList.appendChild(item);
                });
            })
            .catch(error => {
                console.error('Error loading conversations:', error);
            });
    }

    function createNewConversation() {
        fetch('/api/conversations', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(conversation => {
            currentConversationId = conversation.id;
            loadConversation(conversation.id);
            loadConversations();
        })
        .catch(error => {
            console.error('Error creating conversation:', error);
        });
    }

    function deleteConversation(id) {
        fetch(`/api/conversations/${id}`, {
            method: 'DELETE'
        })
        .then(() => {
            if (currentConversationId === parseInt(id)) {
                currentConversationId = null;
                chatContainer.innerHTML = '';
                welcomeMessage.style.display = 'block';
            }
            loadConversations();
        })
        .catch(error => {
            console.error('Error deleting conversation:', error);
        });
    }

    function loadConversation(id) {
        currentConversationId = parseInt(id);
        welcomeMessage.style.display = 'none';
        chatContainer.innerHTML = '<div class="loading-message">Loading messages...</div>';

        // 更新活动对话
        document.querySelectorAll('.conversation-item').forEach(item => {
            item.classList.remove('active');
            if (parseInt(item.dataset.id) === currentConversationId) {
                item.classList.add('active');
            }
        });

        fetch(`/api/conversations/${id}/messages`)
            .then(response => response.json())
            .then(messages => {
                chatContainer.innerHTML = '';
                messages.forEach(message => {
                    if (message.role !== 'system') {
                        addMessageToUI(message.role, message.content);
                    }
                });
                chatContainer.scrollTop = chatContainer.scrollHeight;
            })
            .catch(error => {
                console.error('Error loading messages:', error);
                chatContainer.innerHTML = '<div class="error-message">Error loading messages</div>';
            });
    }

    function sendMessage() {
        const content = userInput.value.trim();
        if (!content) return;

        // 如果没有活动对话，创建一个
        if (!currentConversationId) {
            createNewConversation();
            setTimeout(() => {
                sendStreamMessage(content);
            }, 500); // 给创建对话一些时间
        } else {
            sendStreamMessage(content);
        }

        userInput.value = '';
        userInput.style.height = 'auto';
    }
function sendStreamMessage(content) {
    // 添加用户消息到 UI
    addMessageToUI('user', content);

    // 创建 AI 消息容器
    const aiMessageDiv = document.createElement('div');
    aiMessageDiv.className = 'message ai-message';
    aiMessageDiv.innerHTML = '<div class="typing-indicator">AI 正在思考...</div>';
    chatContainer.appendChild(aiMessageDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;

    // 关闭任何现有的 EventSource
    if (currentEventSource) {
        currentEventSource.close();
    }

    // 首先发送用户消息到服务器
    fetch(`/api/conversations/${currentConversationId}/messages`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ content })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Failed to send message');
        }

        // 然后创建 EventSource 来接收流式响应
        currentEventSource = new EventSource(`/api/conversations/${currentConversationId}/stream`);

        // 处理开始事件
        currentEventSource.addEventListener('start', function(e) {
            // 移除打字指示器
            const typingIndicator = aiMessageDiv.querySelector('.typing-indicator');
            if (typingIndicator) {
                aiMessageDiv.removeChild(typingIndicator);
            }
            aiMessageDiv.innerHTML = '';
        });

        // 处理消息事件
        currentEventSource.onmessage = function(e) {
            try {
                const data = JSON.parse(e.data);
                if (data.content) {
                    aiMessageDiv.innerHTML += data.content.replace(/\n/g, '<br>');
                    chatContainer.scrollTop = chatContainer.scrollHeight;
                }
            } catch (error) {
                console.error('Error parsing SSE message:', error);
            }
        };

        // 处理完成事件
        currentEventSource.addEventListener('done', function(e) {
            currentEventSource.close();
            currentEventSource = null;

            // 更新对话列表
            loadConversations();
        });

        // 处理错误事件
        currentEventSource.addEventListener('error', function(e) {
            console.error('SSE error event:', e);
            try {
                if (e.data) {
                    const data = JSON.parse(e.data);
                    aiMessageDiv.innerHTML = `<div class="error-message">Error: ${data.error}</div>`;
                } else {
                    aiMessageDiv.innerHTML = '<div class="error-message">Connection error</div>';
                }
            } catch (error) {
                aiMessageDiv.innerHTML = '<div class="error-message">Connection error</div>';
                console.error('Error handling SSE error:', error);
            }

            if (currentEventSource) {
                currentEventSource.close();
                currentEventSource = null;
            }
        });
    })
    .catch(error => {
        console.error('Error sending message:', error);
        aiMessageDiv.innerHTML = `<div class="error-message">Error: ${error.message}</div>`;
    });
}


    function addMessageToUI(role, content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role === 'user' ? 'user-message' : 'ai-message'}`;

        // 格式化内容
        const formattedContent = content.replace(/\n/g, '<br>');
        messageDiv.innerHTML = formattedContent;

        chatContainer.appendChild(messageDiv);
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }
});
