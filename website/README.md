## Запуск проекта

### 1. Запуск Backend-сервера
```bash
cd backend
python app.py
```
Сервер запустится на порту: **http://localhost:5000**

### 2. Запуск Frontend-сервера
```bash
cd frontend
python -m http.server 5500
```
Frontend будет доступен по адресу: **http://localhost:5500**

### 3. Открыть в браузере
Перейдите по адресу: [http://localhost:5500](http://localhost:5500)

## Порядок запуска
1. **Сначала запустите backend** (порт 5000)
2. **Затем запустите frontend** (порт 5500)
3. **Откройте браузер** и перейдите на http://localhost:5500