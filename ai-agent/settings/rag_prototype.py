import os
from pathlib import Path
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.prompts import PromptTemplate
from langchain_community.chat_models import GigaChat 
from config import GIGACHAT_TOKEN, generator_prompt, critic_prompt, qa_prompt

FAISS_DIR = Path("C:\\PROJECT\\ai-agent\\faiss_index")

print("Загрузка индекса FAISS...")
embeddings = HuggingFaceEmbeddings(model_name="intfloat/multilingual-e5-large")
vectorstore = FAISS.load_local(FAISS_DIR, embeddings, allow_dangerous_deserialization=True)
print("Индекс загружен.")

CREDENTIALS = GIGACHAT_TOKEN


def get_generator_llm():
    return GigaChat(
        credentials=CREDENTIALS,
        temperature=0.8,  
        verify_ssl_certs=False
    )


def get_critic_llm():
    return GigaChat(
        credentials=CREDENTIALS,
        model="GigaChat-Max",   
        temperature=0.2,        
        verify_ssl_certs=False
    )


QA_PROMPT = PromptTemplate.from_template(qa_prompt)
GENERATOR_PROMPT = PromptTemplate.from_template(generator_prompt)
CRITIC_PROMPT = PromptTemplate.from_template(critic_prompt)


def ask(question: str):
    docs = vectorstore.similarity_search(question, k=5)
    context = "\n\n".join([f"Источник: {d.metadata.get('title','?')}\n{d.page_content}" for d in docs])
    llm = GigaChat(
        credentials=CREDENTIALS,
        model="GigaChat-Pro",
        temperature=0.1,
        verify_ssl_certs=False
    )
    return (QA_PROMPT | llm).invoke({"context": context, "question": question}).content


def generate_hypotheses(problem: str):
    # 1. Поиск контекста
    docs = vectorstore.similarity_search(problem, k=10)
    context = "\n\n".join([
        f"[{i+1}] Источник: {d.metadata.get('title','?')}\n{d.page_content}"
        for i, d in enumerate(docs)
    ])

    # 2. Генерация 5 сырых гипотез - GigaChat-Pro
    generator_llm = get_generator_llm()
    raw_hypotheses = (GENERATOR_PROMPT | generator_llm).invoke({
        "problem": problem,
        "context": context
    }).content

    # 3. Критика и отбор 3 лучших - GigaChat-Max
    critic_llm = get_critic_llm()
    final_hypotheses = (CRITIC_PROMPT | critic_llm).invoke({
        "raw_hypotheses": raw_hypotheses,
        "context": context
    }).content

    print("\n" + "="*60)
    print("ИСПОЛЬЗОВАННЫЕ ИСТОЧНИКИ:")
    for i, d in enumerate(docs, 1):
        print(f"[{i}] {d.metadata.get('title')} | {d.metadata.get('year', 'N/A')}")
        print(f"    Фрагмент: {d.page_content[:200]}...")
    print("="*60)
    return final_hypotheses, raw_hypotheses, docs


def analyze_hypotheses(raw, final, docs):
    
    print("Анализ работы критика:")

    # 1. Подсчет гипотез 
    raw_count = raw.lower().count('1.')
    final_count = final.lower().count('1.')
    print(f"1. Кол-во гипотез: {raw_count} -> {final_count} (ожидалось: 5 -> 3)")

    # 2. Поиск цифр и параметров
    import re
    raw_numbers = re.findall(r'\d+\.?\d*\s*[%°Cmм/минсек]', raw)
    final_numbers = re.findall(r'\d+\.?\d*\s*[%°Cmм/минсек]', final)
    print(f"2. Конкретных параметров (типа '15%', '1200°C'):")
    print(f"   В сырых: {len(raw_numbers)} шт. (примеры: {raw_numbers[:3]})")
    print(f"   В финальных: {len(final_numbers)} шт. (примеры: {final_numbers[:3]})")

    # 3. Проверка "пустых" слов. признак расплывчатости
    vague_words = ["возможно", "может быть", "вероятно", "следует рассмотреть", "обычно"]
    raw_vague = sum(raw.lower().count(word) for word in vague_words)
    final_vague = sum(final.lower().count(word) for word in vague_words)
    print(f"3. Расплывчатых утверждений: {raw_vague} -> {final_vague} (меньше - лучше)")

    # 4. Есть ли явное упоминание источников?
    if "[" in final and "]" in final:
        source_refs = re.findall(r'\[(\d+)\]', final)
        if source_refs:
            print(f"4. В финальных гипотезах ЕСТЬ ссылки на источники: {list(set(source_refs))}")
        else:
            print("4. Есть скобки, но нет номеров источников.")
    else:
        print("4. В финальных гипотезах НЕТ явных ссылок на источники.")
    
    # 5. Проверка соответствия источников
    print("5. Сводка по источникам:")
    for i, doc in enumerate(docs, 1):
        has_ref = f"[{i}]" in raw or f"[{i}]" in final
        status = "✓" if has_ref else "○"
        print(f"   {status} [{i}] {doc.metadata.get('title', '?')}")



if __name__ == "__main__":

    print("ТЕСТ 1")
    answer = ask("Как титан влияет на неметаллические включения в стали?")
    print(answer)
    
    print("ТЕСТ 2")
    problem = "Как снизить неметаллические включения в непрерывнолитой заготовке при выплавке стали?"
    final, raw, docs_used = generate_hypotheses(problem)
    
    print("\n3 гипотезы после оспаривания:")
    print(final)
    
    print("5 гипотез до оспаривания:")
    print(raw)
    
    analyze_hypotheses(raw, final, docs_used)