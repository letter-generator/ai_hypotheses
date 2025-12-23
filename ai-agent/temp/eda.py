import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud, STOPWORDS
from pathlib import Path
import re
from collections import Counter
import warnings
warnings.filterwarnings('ignore')

# Пути
CHUNKS_FILE = Path("C:\\PROJECT\\ai-agent\\data\\clean.jsonl")
EDA_DIR = Path("eda_plots")
EDA_DIR.mkdir(parents=True, exist_ok=True)

print("=== ПРОДВИНУТЫЙ EDA ДЛЯ МЕТАЛЛУРГИЧЕСКОЙ RAG-СИСТЕМЫ ===")
print("=" * 60)

if not CHUNKS_FILE.exists():
    print(f"❌ Ошибка: файл {CHUNKS_FILE} не найден!")
    print("Сначала запусти clean_and_split.py")
    exit()

# 1. Умная загрузка с обработкой ошибок
chunks = []
problem_lines = 0
error_samples = []
line_errors = []

with open(CHUNKS_FILE, "r", encoding="utf-8") as f:
    for i, line in enumerate(f, 1):
        if line.strip():
            try:
                data = json.loads(line)
                # Проверяем обязательные поля
                if 'chunk_text' in data and isinstance(data['chunk_text'], str) and len(data['chunk_text']) > 10:
                    # Нормализуем названия полей
                    if 'chunk_text' in data:
                        data['text'] = data['chunk_text']
                    if 'chunk_tokens' in data:
                        data['tokens'] = data['chunk_tokens']
                    chunks.append(data)
                else:
                    problem_lines += 1
                    if problem_lines <= 3:
                        error_samples.append(f"Строка {i}: отсутствует или слишком короткий chunk_text")
            except (json.JSONDecodeError, KeyError) as e:
                problem_lines += 1
                line_errors.append(f"Строка {i}: {str(e)[:50]}...")

if not chunks:
    print("❌ Нет валидных данных в clean.jsonl — база пустая.")
    exit()

print(f"✅ Загружено чанков: {len(chunks)}")
if problem_lines > 0:
    print(f"⚠️  Пропущено проблемных строк: {problem_lines}")
    if error_samples:
        print("  Примеры проблем:")
        for err in error_samples[:3]:
            print(f"    - {err}")

df = pd.DataFrame(chunks)

# 2. ОСНОВНАЯ СТАТИСТИКА С ФОРМАТИРОВАНИЕМ
print("\n" + "=" * 60)
print("📊 ОСНОВНАЯ СТАТИСТИКА БАЗЫ ЗНАНИЙ")
print("=" * 60)

# Создаем обязательные поля, если их нет
if 'text' not in df.columns and 'chunk_text' in df.columns:
    df['text'] = df['chunk_text']

df['text_length'] = df['text'].str.len()

# Расчет токенов
if 'tokens' in df.columns:
    df['token_count'] = df['tokens']
elif 'chunk_tokens' in df.columns:
    df['token_count'] = df['chunk_tokens']
else:
    # Примерная оценка токенов (4 символа = 1 токен для английского, ~2 для русского)
    df['token_count'] = df['text_length'] // 3

# Вычисляем статистику
try:
    stats = {
        "Всего чанков": len(df),
        "Уникальных статей": df['source'].nunique() if 'source' in df.columns else "N/A",
        "Средняя длина чанка": f"{df['text_length'].mean():.0f} символов",
        "Медианная длина": f"{df['text_length'].median():.0f} символов",
        "Минимальная длина": f"{df['text_length'].min():.0f} символов",
        "Максимальная длина": f"{df['text_length'].max():.0f} символов",
        "Стандартное отклонение": f"{df['text_length'].std():.0f} символов",
        "Среднее токенов": f"{df['token_count'].mean():.0f}",
        "Общий объем текста": f"{df['text_length'].sum() / 1_000_000:.2f} МБ",
        "Процент валидных данных": f"{(len(df)/(len(df)+problem_lines)*100):.1f}%"
    }
    
    for key, value in stats.items():
        print(f"  {key:30} : {value}")
except Exception as e:
    print(f"  ⚠️  Ошибка при расчете статистики: {e}")

# 3. АНАЛИЗ ПО ГОДАМ (с обработкой "Не определено")
print("\n📅 АНАЛИЗ ПО ГОДАМ ПУБЛИКАЦИЙ")
print("-" * 40)

if 'year' in df.columns:
    try:
        # Очищаем данные года
        df['year_clean'] = pd.to_numeric(
            df['year'].astype(str).str.extract(r'(\d{4})')[0], 
            errors='coerce'
        )
        valid_years = df['year_clean'].dropna()
        
        if len(valid_years) > 0:
            print(f"  Статей с указанным годом: {len(valid_years)} ({len(valid_years)/len(df)*100:.1f}%)")
            print(f"  Диапазон лет: {int(valid_years.min())} - {int(valid_years.max())}")
            print(f"  Медианный год: {int(valid_years.median())}")
            
            # График распределения по годам
            plt.figure(figsize=(14, 7))
            
            # Гистограмма
            plt.subplot(1, 2, 1)
            sns.histplot(valid_years, bins=min(30, len(valid_years.unique())),
                        kde=True, color='#8A2BE2', alpha=0.7)
            plt.title('Распределение статей по годам', fontsize=14, fontweight='bold')
            plt.xlabel('Год публикации')
            plt.ylabel('Количество статей')
            plt.grid(True, alpha=0.3)
            
            # Box plot для проверки выбросов
            plt.subplot(1, 2, 2)
            sns.boxplot(y=valid_years, color='#9370DB')
            plt.title('Box plot: распределение годов', fontsize=14, fontweight='bold')
            plt.ylabel('Год')
            plt.grid(True, alpha=0.3)
            
            plt.tight_layout()
            plt.savefig(EDA_DIR / "year_analysis.png", dpi=150, bbox_inches='tight')
            plt.close()
            print(f"  ✅ Сохранён: eda_plots/year_analysis.png")
        else:
            print("  ⚠️  Нет валидных годов в данных")
    except Exception as e:
        print(f"  ⚠️  Ошибка при анализе годов: {e}")
else:
    print("  ⚠️  Поле 'year' отсутствует")

# 4. РАСПРЕДЕЛЕНИЕ ДЛИНЫ ЧАНКОВ
print("\n📏 АНАЛИЗ ДЛИНЫ ТЕКСТОВЫХ ЧАНКОВ")
print("-" * 40)

try:
    plt.figure(figsize=(15, 10))
    
    # Гистограмма
    plt.subplot(2, 2, 1)
    sns.histplot(df['text_length'], bins=50, kde=True, color='#4B0082')
    plt.title('Распределение длины чанков', fontsize=14, fontweight='bold')
    plt.xlabel('Длина (символы)')
    plt.ylabel('Частота')
    plt.axvline(df['text_length'].mean(), color='red', linestyle='--', 
                label=f'Среднее: {df["text_length"].mean():.0f}')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Box plot
    plt.subplot(2, 2, 2)
    sns.boxplot(y=df['text_length'], color='#9932CC')
    plt.title('Box plot длины чанков', fontsize=14, fontweight='bold')
    plt.ylabel('Длина (символы)')
    plt.grid(True, alpha=0.3)
    
    # QQ-plot для проверки нормальности
    plt.subplot(2, 2, 3)
    from scipy import stats as sp_stats
    sp_stats.probplot(df['text_length'], dist="norm", plot=plt)
    plt.title('QQ-plot: проверка нормальности', fontsize=14, fontweight='bold')
    plt.grid(True, alpha=0.3)
    
    # Cumulative distribution
    plt.subplot(2, 2, 4)
    sorted_lengths = np.sort(df['text_length'])
    if len(sorted_lengths) > 1:
        yvals = np.arange(len(sorted_lengths)) / float(len(sorted_lengths) - 1)
        plt.plot(sorted_lengths, yvals, color='#8A2BE2', linewidth=2)
        plt.title('Cumulative Distribution', fontsize=14, fontweight='bold')
        plt.xlabel('Длина (символы)')
        plt.ylabel('Процент данных')
        plt.grid(True, alpha=0.3)
    else:
        plt.text(0.5, 0.5, 'Недостаточно данных', ha='center', va='center')
        plt.title('Cumulative Distribution', fontsize=14, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(EDA_DIR / "chunk_length_analysis.png", dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"  Минимальная длина: {df['text_length'].min():.0f} символов")
    print(f"  Максимальная длина: {df['text_length'].max():.0f} символов")
    print(f"  Стандартное отклонение: {df['text_length'].std():.0f}")
    print(f"  ✅ Сохранён: eda_plots/chunk_length_analysis.png")
except Exception as e:
    print(f"  ⚠️  Ошибка при анализе длины чанков: {e}")

# 5. УМНОЕ ОБЛАКО СЛОВ (специально для металлургии)
print("\n🔤 АНАЛИЗ КЛЮЧЕВЫХ ТЕРМИНОВ")
print("-" * 40)

try:
    # Специфичные стоп-слова для металлургии
    metallurgy_stopwords = set(STOPWORDS)
    russian_stopwords = {'и', 'в', 'с', 'на', 'по', 'что', 'это', 'для', 'от', 'из', 'как', 'то', 'же', 'но', 'а'}
    metallurgy_stopwords.update(russian_stopwords)
    
    # Извлекаем технические термины
    all_text = ' '.join(df['text'].astype(str).str.lower())
    
    # Убираем цифры и короткие слова
    words = re.findall(r'\b[a-zа-я]{4,}\b', all_text)
    word_freq = Counter(words)
    
    # Удаляем стоп-сwords
    filtered_freq = {word: count for word, count in word_freq.items()
                     if word not in metallurgy_stopwords and count > 5}
    
    if filtered_freq and len(filtered_freq) > 10:
        # Облако слов
        wordcloud = WordCloud(
            width=1600, height=800,
            background_color='black',
            colormap='viridis',
            max_words=200,
            stopwords=metallurgy_stopwords
        ).generate_from_frequencies(filtered_freq)
        
        plt.figure(figsize=(20, 10))
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis('off')
        plt.title('Ключевые термины в металлургических статьях',
                  fontsize=24, fontweight='bold', pad=20)
        plt.tight_layout()
        plt.savefig(EDA_DIR / "technical_wordcloud.png", dpi=150, bbox_inches='tight')
        plt.close()
        
        # Топ-20 терминов
        top_terms = pd.Series(filtered_freq).nlargest(20)
        
        plt.figure(figsize=(12, 8))
        top_terms.sort_values().plot(kind='barh', color='#8A2BE2')
        plt.title('Топ-20 технических терминов', fontsize=16, fontweight='bold')
        plt.xlabel('Частота')
        plt.grid(True, alpha=0.3, axis='x')
        plt.tight_layout()
        plt.savefig(EDA_DIR / "top_terms.png", dpi=150, bbox_inches='tight')
        plt.close()
        
        print(f"  Уникальных терминов: {len(filtered_freq)}")
        print(f"  Топ-5 терминов: {', '.join(list(top_terms.index[:5]))}")
        print(f"  ✅ Сохранены: eda_plots/technical_wordcloud.png, eda_plots/top_terms.png")
    else:
        print("  ⚠️  Не удалось извлечь технические термины или их слишком мало")
except Exception as e:
    print(f"  ⚠️  Ошибка при анализе терминов: {e}")

# 6. АНАЛИЗ ИСТОЧНИКОВ
print("\n📚 АНАЛИЗ ИСТОЧНИКОВ ДАННЫХ")
print("-" * 40)

if 'source' in df.columns:
    try:
        source_stats = df['source'].value_counts()
        
        plt.figure(figsize=(14, 10))
        
        # Топ-15 источников
        plt.subplot(2, 1, 1)
        top_sources = source_stats.head(15)
        max_val = top_sources.max() if not top_sources.empty else 0
        bars = plt.barh(range(len(top_sources)), top_sources.values,
                       color=plt.cm.viridis(np.linspace(0.3, 0.9, len(top_sources))))
        plt.yticks(range(len(top_sources)), top_sources.index)
        plt.gca().invert_yaxis()
        plt.title('Топ-15 источников по количеству чанков', fontsize=14, fontweight='bold')
        plt.xlabel('Количество чанков')
        plt.grid(True, alpha=0.3, axis='x')
        
        # Добавляем значения на бары
        for i, (bar, value) in enumerate(zip(bars, top_sources.values)):
            plt.text(value + max_val * 0.01, bar.get_y() + bar.get_height()/2,
                    str(value), va='center', fontsize=9)
        
        # Распределение типов источников (Arxiv vs OpenAlex)
        plt.subplot(2, 1, 2)
        source_types = df['source'].apply(lambda x: 'arxiv' if 'arxiv' in str(x).lower() else
                                                      'openalex' if 'openalex' in str(x).lower() else 'other')
        type_counts = source_types.value_counts()
        
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1']
        wedges, texts, autotexts = plt.pie(type_counts.values, labels=type_counts.index,
                                           autopct='%1.1f%%', colors=colors, startangle=90)
        plt.title('Распределение по типам источников', fontsize=14, fontweight='bold')
        
        plt.tight_layout()
        plt.savefig(EDA_DIR / "source_analysis.png", dpi=150, bbox_inches='tight')
        plt.close()
        
        print(f"  Всего уникальных источников: {len(source_stats)}")
        print(f"  Доминирующий источник: {source_stats.index[0] if not source_stats.empty else 'N/A'} ({source_stats.iloc[0] if not source_stats.empty else 0} чанков)")
        print(f"  ✅ Сохранён: eda_plots/source_analysis.png")
    except Exception as e:
        print(f"  ⚠️  Ошибка при анализе источников: {e}")
else:
    print("  ⚠️  Поле 'source' отсутствует")

# 7. ДОПОЛНИТЕЛЬНЫЙ АНАЛИЗ: РАСПРЕДЕЛЕНИЕ ПО СТРАНАМ
print("\n🌍 АНАЛИЗ ПО СТРАНАМ")
print("-" * 40)

if 'country' in df.columns:
    try:
        country_stats = df['country'].value_counts()
        
        if not country_stats.empty:
            plt.figure(figsize=(12, 8))
            
            # Топ-10 стран
            top_countries = country_stats.head(10)
            top_countries.plot(kind='bar', color='#6A5ACD')
            plt.title('Топ-10 стран по количеству статей', fontsize=14, fontweight='bold')
            plt.xlabel('Страна')
            plt.ylabel('Количество статей')
            plt.xticks(rotation=45)
            plt.grid(True, alpha=0.3, axis='y')
            plt.tight_layout()
            plt.savefig(EDA_DIR / "country_distribution.png", dpi=150, bbox_inches='tight')
            plt.close()
            
            print(f"  Уникальных стран: {len(country_stats)}")
            print(f"  Топ-3 страны: {', '.join(list(country_stats.index[:3]))}")
            print(f"  ✅ Сохранён: eda_plots/country_distribution.png")
        else:
            print("  ⚠️  Нет данных по странам")
    except Exception as e:
        print(f"  ⚠️  Ошибка при анализе стран: {e}")
else:
    print("  ⚠️  Поле 'country' отсутствует")

# 8. АНАЛИЗ ДУБЛИКАТОВ
print("\n🔍 АНАЛИЗ ДУБЛИКАТОВ И ПОВТОРОВ")
print("-" * 40)

try:
    # Проверяем дубликаты по тексту
    text_duplicates = df['text'].duplicated().sum()
    duplicate_percentage = (text_duplicates / len(df)) * 100
    
    print(f"  Полные дубликаты текста: {text_duplicates} ({duplicate_percentage:.1f}%)")
    
    if text_duplicates > 0:
        # Визуализация дубликатов
        plt.figure(figsize=(10, 6))
        labels = ['Уникальные', 'Дубликаты']
        sizes = [len(df) - text_duplicates, text_duplicates]
        colors = ['#4CAF50', '#F44336']
        plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
        plt.title('Распределение уникальных и дублирующихся чанков', fontsize=14, fontweight='bold')
        plt.tight_layout()
        plt.savefig(EDA_DIR / "duplicates_analysis.png", dpi=150, bbox_inches='tight')
        plt.close()
        print(f"  ✅ Сохранён: eda_plots/duplicates_analysis.png")
    
    # Проверяем схожие чанки (по первым 100 символам)
    df['text_start'] = df['text'].str.slice(0, 100)
    start_duplicates = df['text_start'].duplicated().sum()
    print(f"  Чанки с похожим началом: {start_duplicates}")
    
except Exception as e:
    print(f"  ⚠️  Ошибка при анализе дубликатов: {e}")

# 9. КОРРЕЛЯЦИОННЫЙ АНАЛИЗ
print("\n📈 КОРРЕЛЯЦИОННЫЙ АНАЛИЗ")
print("-" * 40)

try:
    # Выбираем только числовые колонки
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    # Убираем неинформативные колонки (например, состоящие из одного значения)
    informative_numeric_cols = []
    for col in numeric_cols:
        if df[col].nunique() > 1 and not df[col].isna().all():
            informative_numeric_cols.append(col)
    
    if len(informative_numeric_cols) > 1:
        corr_matrix = df[informative_numeric_cols].corr()
        
        plt.figure(figsize=(10, 8))
        sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', center=0,
                    square=True, linewidths=1, cbar_kws={"shrink": 0.8},
                    fmt='.2f')
        plt.title('Матрица корреляций числовых признаков', fontsize=14, fontweight='bold')
        plt.tight_layout()
        plt.savefig(EDA_DIR / "correlation_matrix.png", dpi=150, bbox_inches='tight')
        plt.close()
        print(f"  ✅ Сохранён: eda_plots/correlation_matrix.png")
        
        # Выводим сильные корреляции
        strong_correlations = []
        for i in range(len(corr_matrix.columns)):
            for j in range(i+1, len(corr_matrix.columns)):
                corr_value = corr_matrix.iloc[i, j]
                if abs(corr_value) > 0.7:  # Сильная корреляция
                    strong_correlations.append(
                        f"{corr_matrix.columns[i]} - {corr_matrix.columns[j]}: {corr_value:.2f}"
                    )
        
        if strong_correlations:
            print("  Сильные корреляции:")
            for corr in strong_correlations:
                print(f"    • {corr}")
    else:
        print("  ⚠️  Недостаточно числовых данных для корреляционного анализа")
except Exception as e:
    print(f"  ⚠️  Ошибка при корреляционном анализе: {e}")

# 10. СОХРАНЕНИЕ СВОДНОГО ОТЧЕТА
print("\n📄 ФИНАЛЬНЫЙ ОТЧЕТ")
print("=" * 60)

try:
    report_path = EDA_DIR / "eda_summary.txt"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("=" * 60 + "\n")
        f.write("ОТЧЕТ EDA ДЛЯ МЕТАЛЛУРГИЧЕСКОЙ RAG-СИСТЕМЫ\n")
        f.write("=" * 60 + "\n\n")
        
        f.write("1. ОСНОВНАЯ СТАТИСТИКА\n")
        f.write("-" * 40 + "\n")
        for key, value in stats.items():
            f.write(f"{key:35} : {value}\n")
        
        f.write("\n2. КАЧЕСТВО ДАННЫХ\n")
        f.write("-" * 40 + "\n")
        f.write(f"Пропущено проблемных строк: {problem_lines}\n")
        f.write(f"Процент валидных данных: {(len(df)/(len(df)+problem_lines)*100):.1f}%\n")
        f.write(f"Полные дубликаты текста: {text_duplicates} ({duplicate_percentage:.1f}%)\n")
        
        if 'year_clean' in df.columns:
            valid_years = df['year_clean'].dropna()
            if len(valid_years) > 0:
                f.write(f"\n3. ВРЕМЕННОЙ АНАЛИЗ\n")
                f.write("-" * 40 + "\n")
                f.write(f"Статей с указанным годом: {len(valid_years)}\n")
                f.write(f"Диапазон лет: {int(valid_years.min())} - {int(valid_years.max())}\n")
                f.write(f"Медианный год: {int(valid_years.median())}\n")
                f.write(f"Средний год: {valid_years.mean():.1f}\n")
        
        if filtered_freq and len(filtered_freq) > 10:
            f.write(f"\n4. ТЕРМИНОЛОГИЧЕСКИЙ АНАЛИЗ\n")
            f.write("-" * 40 + "\n")
            f.write(f"Уникальных технических терминов: {len(filtered_freq)}\n")
            f.write(f"Топ-10 терминов:\n")
            for i, (term, freq) in enumerate(list(filtered_freq.most_common(10)), 1):
                f.write(f"  {i:2}. {term:25} : {freq:5}\n")
        
        if 'source' in df.columns:
            f.write(f"\n5. АНАЛИЗ ИСТОЧНИКОВ\n")
            f.write("-" * 40 + "\n")
            f.write(f"Всего уникальных источников: {df['source'].nunique()}\n")
            f.write(f"Топ-5 источников:\n")
            for i, (source, count) in enumerate(df['source'].value_counts().head(5).items(), 1):
                f.write(f"  {i}. {source:50} : {count}\n")
        
        f.write(f"\n6. РЕКОМЕНДАЦИИ\n")
        f.write("-" * 40 + "\n")
        
        recommendations = []
        if len(df) < 100:
            recommendations.append("База слишком мала (<100 чанков). Добавьте больше статей.")
        if text_duplicates / len(df) > 0.1:
            recommendations.append("Высокий процент дубликатов (>10%). Проверьте preprocessing.")
        if 'text_length' in df.columns and df['text_length'].std() > df['text_length'].mean() * 0.5:
            recommendations.append("Высокая дисперсия длины чанков. Стандартизируйте размер чанков.")
        if 'year_clean' in df.columns and len(df['year_clean'].dropna()) / len(df) < 0.5:
            recommendations.append("Менее 50% статей имеют год публикации. Улучшите парсинг метаданных.")
        
        if recommendations:
            for i, rec in enumerate(recommendations, 1):
                f.write(f"  {i}. {rec}\n")
        else:
            f.write("  База знаний в хорошем состоянии для RAG-системы!\n")
        
        f.write(f"\n7. ВЫВОДЫ ДЛЯ RAG-СИСТЕМЫ\n")
        f.write("-" * 40 + "\n")
        f.write(f"• Средняя длина чанков подходит для семантического поиска\n")
        f.write(f"• Качество данных достаточное для генерации гипотез\n")
        f.write(f"• Наличие метаданных (год, страна) улучшает контекст\n")
        
    print(f"✅ ВСЕ ГРАФИКИ СОХРАНЕНЫ В: {EDA_DIR}")
    print(f"✅ СВОДНЫЙ ОТЧЕТ: {report_path}")
    
except Exception as e:
    print(f"⚠️  Ошибка при сохранении отчета: {e}")

print("\n" + "=" * 60)
print("📌 РЕКОМЕНДАЦИИ ДЛЯ УЛУЧШЕНИЯ БАЗЫ ЗНАНИЙ:")
print("=" * 60)

# Автоматические рекомендации
recommendations = []
if len(df) < 100:
    recommendations.append("⚠️  База слишком мала (<100 чанков). Добавьте больше статей.")
if text_duplicates / len(df) > 0.1:
    recommendations.append("⚠️  Высокий процент дубликатов (>10%). Проверьте preprocessing.")
if 'text_length' in df.columns and df['text_length'].std() > df['text_length'].mean() * 0.5:
    recommendations.append("⚠️  Высокая дисперсия длины чанков. Стандартизируйте размер чанков.")
if 'year_clean' in df.columns and len(df['year_clean'].dropna()) / len(df) < 0.5:
    recommendations.append("⚠️  Менее 50% статей имеют год публикации. Улучшите парсинг метаданных.")
if 'country' in df.columns and df['country'].nunique() < 3:
    recommendations.append("⚠️  Мало стран представлено. Разнообразьте источники.")

for i, rec in enumerate(recommendations, 1):
    print(f"  {i}. {rec}")

if not recommendations:
    print("  ✅ База знаний в хорошем состоянии для RAG-системы!")

print("\n" + "=" * 60)
print("🎯 КЛЮЧЕВЫЕ МЕТРИКИ ДЛЯ ОТЧЕТА:")
print("=" * 60)
print(f"  • Размер базы: {len(df)} чанков")
print(f"  • Качество: {stats.get('Процент валидных данных', 'N/A')}")
print(f"  • Термины: {len(filtered_freq) if 'filtered_freq' in locals() else 'N/A'} уникальных")
print(f"  • Временной охват: {int(valid_years.min()) if 'valid_years' in locals() and len(valid_years) > 0 else 'N/A'}-{int(valid_years.max()) if 'valid_years' in locals() and len(valid_years) > 0 else 'N/A'}")
print("=" * 60)