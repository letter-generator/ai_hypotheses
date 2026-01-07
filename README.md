<h1 align="center"> HypGen </h1>
<h3 align="center"> ИИ-агент для генерации гипотез c функцией Q&A в области металлургии  </h3>  

</br>

<h2 id="table-of-contents"> :book: Навигация</h2>

<details open="open">
  <summary>Навигация</summary>
  <ol>
    <li><a href="#about"> ➤ О проекте</a></li>
    <li><a href="#folder-structure"> ➤ Структура проекта</a></li>
    <li><a href="#technology stack"> ➤ Стек технологий</a></li>
    <li><a href="#contributors"> ➤ Участники</a></li>
  </ol>
</details>

![-----------------------------------------------------](https://raw.githubusercontent.com/andreasbm/readme/master/assets/lines/rainbow.png)

<h2 id="about"> :small_orange_diamond: О проекте</h2>

<p align="justify">
<strong>HypGen</strong> — это интеллектуальный агент для генерации научных гипотез и ответов на вопросы в области металлургии и материаловедения. Система использует современные подходы искусственного интеллекта для анализа научных статей и предложения исследовательских идей.
</p>

<p align="justify">
<strong>Проблема:</strong> Исследователи в области металлургии тратят до 60% рабочего времени на поиск и анализ научной литературы, что значительно замедляет процесс генерации новых идей и гипотез.
</p>

<p align="justify">
<strong>Решение:</strong> Наш агент автоматизирует этот процесс, используя:
</p>
<ul>
  <li>Базу знаний из 500+ научных статей по металлургии</li>
  <li>RAG-архитектуру (Retrieval-Augmented Generation)</li>
  <li>Мощную языковую модель GigaChat-Pro</li>
  <li>Механизм валидации и оспаривания гипотез (Gigachat-Max)</li>
</ul>

<p align="justify">
Система позволяет исследователям сосредоточиться на творческой и экспериментальной работе, сокращая время на подготовительные этапы с нескольких недель до минут.
</p>


![-----------------------------------------------------](https://raw.githubusercontent.com/andreasbm/readme/master/assets/lines/rainbow.png)


<h2 id="folder-structure"> :small_orange_diamond: Структура проекта</h2>

   
    ai-agent/
    ├── data/
    │   ├── clean.jsonl.py     # Очищенные и разбитые на чанки данные    
    │   └── raw.jsonl          # Сырые данные (научные статьи)           
    |
    ├── faiss_index/
    │   ├── index.faiss        # FAISS индекс
    │   ├── index.pkl          # Метаданные индекса
    │   └── index_info.json    # Информация о модели     
    |
    ├── scripts/
    │   ├── build_faiss.py     # Создание векторного индекса   
    │   ├── clean_and_split.py # Очистка и разбивка на чанки
    │   └── parse.py           # Парсинг статей из источников
    |
    ├── settings/
    │   ├── config.py          # Настройки проекта
    │   ├── prompts.py         # Промпты для LLM    
    │   └── requirements.txt   # Зависимости проекта                          
    |                  
    ├── app.py                 # Основное приложение для запуска (в тестовом интерфейсе Streamlit)   
    └── rag.py                 # RAG-пайплайн




![-----------------------------------------------------](https://raw.githubusercontent.com/andreasbm/readme/master/assets/lines/rainbow.png)


<h2 id="requirements_instruction"> :small_orange_diamond: Cтек технологий</h2>

[![made-with-python](https://img.shields.io/badge/Made%20with-Python-1f425f.svg)](https://www.python.org/) <br>

В проекте используются следующие ключевые технологии и библиотеки с открытым исходным кодом:

- **Python 3.11** — язык программирования, на котором написан агент
- **LangChain** — фреймворк для LLM-приложений
- **FAISS** — векторный поиск от Facebook AI
- **Hugging face - multilingual-e5-large-instruct**  — модель эмбеддингов
- **Gigachat Pro + Gigacht Max** - LLM для генерации и оспаривания гипотез соответственно


![-----------------------------------------------------](https://raw.githubusercontent.com/andreasbm/readme/master/assets/lines/rainbow.png)


<h2 id="contributors"> :small_orange_diamond: Участники</h2>

<p>
  :diamond_shape_with_a_dot_inside: <b>Молчанова Полина Алексеевна</b> <br>
  &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Email: <a>07lllllll07lllllll@gmail.com</a> <br>
  &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; GitHub: <a href="https://github.com/aaaaaaa0">@aaaaaaa0</a> <br>
  
  :diamond_shape_with_a_dot_inside: <b>Пластеева Ксения Евгеньевна</b> <br>
  &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Email: <a>kseniaplasteeva45561@gmail.com</a> <br>
  &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; GitHub: <a href="https://github.com/KseniaPlasteeva">@KseniaPlasteeva</a> <br>

  :diamond_shape_with_a_dot_inside: <b>Ступаченко Екатерина Евгеньевна</b> <br>
  &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Email: <a>katya.62442@gmail.com</a> <br>
  &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; GitHub: <a href="https://github.com/tnixf">@tnixf</a> <br>

  :diamond_shape_with_a_dot_inside: <b>Тетенькина Екатерина Владимировна</b> <br>
  &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Email: <a>fikusekaterina8@gmail.com</a> <br>
  &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; GitHub: <a href="https://github.com/f-f-i">@f-f-i</a> <br>

  :diamond_shape_with_a_dot_inside: <b>Филипович Илья Андреевич</b> <br>
  &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Email: <a>llilay293@gmail.com</a> <br>
  &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; GitHub: <a href="https://github.com/IlyaF7">@IlyaF7</a> <br>

  :diamond_shape_with_a_dot_inside: <b>Суханова Софья Андреевна</b> <br>
  &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Email: <a>genkagorinnn@gmail.com</a> <br>
  &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; GitHub: <a href="https://github.com/sofyasukh">@sofyasukh</a> <br>

  :diamond_shape_with_a_dot_inside: <b>Мосина Вероника Григорьевна</b> <br>
  &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Email: <a>mosinaveronika13@gmail.com</a> <br>
  &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; GitHub: <a href="https://github.com/relladonna">@relladonna</a> <br>

  :diamond_shape_with_a_dot_inside: <b>Ляпин Семён Николаевич</b> <br>
  &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Email: <a>semenlyapin1@gmail.com</a> <br>
  &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; GitHub: <a href="https://github.com/Semyon129">@Semyon129</a> <br>
</p>

<i>
  Учебный проект, реализованный в рамках дисциплины «Проектный практикум».<br>
  Команда «Генератор букв».<br>
  Январь 2026 г.
</i>
