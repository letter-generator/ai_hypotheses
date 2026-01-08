import requests

BASE_URL = "http://127.0.0.1:5000"

# Тест создания чата
response = requests.post(f"{BASE_URL}/api/new_chat")
print("Новый чат:", response.json())

# Тест отправки сообщения
chat_id = response.json()['chat_id']
response = requests.post(f"{BASE_URL}/api/send_message", 
                         json={"chat_id": chat_id, "message": "Тестовое сообщение"})
print("Ответ на сообщение:", response.json())

# Тест получения истории
response = requests.get(f"{BASE_URL}/api/chat_history")
print("История чатов:", response.json())