import getpass
import platform
import sys
import g4f
import os
from colorama import Fore, Back, Style
import psutil
from pathlib import Path
import shutil
import subprocess
import traceback

import subprocess

def run_command(command):
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Ошибка при выполнении команды: {e.stderr}"
    
def check_program_in_path(program_name):
    """
    Проверяет, доступна ли программа в PATH
    """
    return shutil.which(program_name) is not None

def get_program_path(program_name):
    """
    Возвращает полный путь к программе
    """
    return shutil.which(program_name)

def check_git_installation():
    """
    Проверяет установлен ли Git и его версию
    """
    if not check_program_in_path('git'):
        return False, None, None
    
    try:
        result = subprocess.run(
            ['git', '--version'],
            capture_output=True,
            text=True,
            shell=True
        )
        if result.returncode == 0:
            version = result.stdout.strip()
            path = get_program_path('git')
            return True, version, path
    except Exception:
        pass
    
    return False, None, None

def check_gh_installation():
    """
    Проверяет установлен ли GitHub CLI и его версию
    """
    if not check_program_in_path('gh'):
        return False, None, None
    
    try:
        result = subprocess.run(
            ['gh', '--version'],
            capture_output=True,
            text=True,
            shell=True
        )
        if result.returncode == 0:
            # Берем только первую строку с версией
            version = result.stdout.strip().split('\n')[0]
            path = get_program_path('gh')
            return True, version, path
    except Exception:
        pass
    
    return False, None, None

def check_docker():
    """
    Проверяет установлен ли Docker
    """
    if not check_program_in_path('docker'):
        return False, None, None
    
    try:
        result = subprocess.run(
            ['docker', '--version'],
            capture_output=True,
            text=True,
            shell=True
        )
        if result.returncode == 0:
            version = result.stdout.strip()
            path = get_program_path('docker')
            return True, version, path
    except Exception:
        pass
    
    return False, None, None

def check_python():
    """
    Проверяет установлен ли Python
    """
    if not check_program_in_path('python'):
        return False, None, None
    
    try:
        result = subprocess.run(
            ['python', '--version'],
            capture_output=True,
            text=True,
            shell=True
        )
        if result.returncode == 0:
            version = result.stdout.strip()
            path = get_program_path('python')
            return True, version, path
    except Exception:
        pass
    
    return False, None, None

def get_current_directory_contents():
    """
    Возвращает список файлов и папок в текущей директории
    """
    current_dir = Path.cwd()
    try:
        items = list(current_dir.iterdir())
        # Разделяем файлы и папки для лучшей читаемости
        dirs = []
        files = []
        
        for item in items:
            if item.is_dir():
                dirs.append(f"[DIR]  {item.name}")
            else:
                files.append(f"[FILE] {item.name}")
        
        # Объединяем и сортируем
        all_items = sorted(dirs) + sorted(files)
        
        if all_items:
            return "Файлы и папки в текущей директории:\n" + "\n".join(all_items)
        else:
            return "Текущая директория пуста"
    except Exception as e:
        return f"Не удалось прочитать содержимое директории: {str(e)}"

def read_file_content(file_path):
    """
    Читает содержимое файла и возвращает его
    """
    try:
        path = Path(file_path)
        
        # Если путь относительный, делаем его абсолютным относительно текущей директории
        if not path.is_absolute():
            path = Path.cwd() / path
        
        # Проверяем существование файла
        if not path.exists():
            return f"Файл не найден: {file_path}"
        
        # Проверяем, что это файл, а не директория
        if not path.is_file():
            return f"Это директория, а не файл: {file_path}"
        
        # Проверяем размер файла (не читаем слишком большие файлы)
        file_size = path.stat().st_size
        if file_size > 1024 * 1024 * 5:  # 5MB лимит для анализа
            return f"Файл слишком большой для анализа ({file_size} байт). Максимальный размер: 5MB"
        
        # Читаем содержимое файла
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Проверяем, не бинарный ли файл
        try:
            content.encode('utf-8').decode('utf-8')
        except UnicodeDecodeError:
            return f"Файл содержит бинарные данные и не может быть прочитан как текст"
        
        return content
        
    except Exception as e:
        return f"Ошибка при чтении файла {file_path}: {str(e)}"

def analyze_file(quest, file_content):
    """
    Проверяет Python файл на синтаксические ошибки
    """
    try:
        q = f'{file_content}\n\n\n{quest}'
        hystory = [{'role': 'user', 'content': q}]
        a = answer(q, hystory=hystory)
        return a
    except Exception as e:
        return f"Ошибка при анализе кода: {str(e)}"


def answer(query: str, hystory: list) -> str:
    response = g4f.ChatCompletion.create(
        model=g4f.models.command_a,
        messages=hystory,
    )
    return response

bstart = '├'

def draw_tui_window(ques, ans):
    global bstart
    print(f'{Fore.GREEN}├─ GPT:{Style.RESET_ALL}')
    for i in ans.split('\n'):
        print(f'{Fore.GREEN}│ {Fore.LIGHTGREEN_EX}{i}{Style.RESET_ALL}')
    print(f'{Fore.LIGHTBLACK_EX}├─{"─"*50}{Style.RESET_ALL}')
    
    ans_lines = ans.split('\n')
    name_file = False
    file = 0
    
    for i in ans_lines:
        if i.startswith('cmd'):
            bstart = '╭'
            com = i[4:]
            if com.startswith('cd'):
                try:
                    os.chdir(com[3:].strip())
                except Exception as e:
                    print(f'{Fore.RED}Ошибка при смене директории: {e}{Style.RESET_ALL}')
            else:
                try:
                    run_command(com)
                except Exception as e:
                    print(f'{Fore.RED}Ошибка при выполнении команды: {e}{Style.RESET_ALL}')
        elif i.startswith('file'):
            bstart = '╭'
            file = 1
            name_file = i[5:].strip()
        elif i.startswith('^^^') and file == 1:
            bstart = '╭'
            file = 2
        elif i == '^^^' and file == 2:
            bstart = '╭'
            file = 0
        elif file == 2:
            bstart = '╭'
            if name_file:
                try:
                    # Проверяем, существует ли директория для файла
                    file_path = Path(name_file)
                    if file_path.parent:
                        file_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Записываем в файл
                    with open(name_file, 'a', encoding='utf-8') as f:
                        f.write(i + '\n')
                except Exception as e:
                    print(f'{Fore.RED}Ошибка при записи в файл {name_file}: {e}{Style.RESET_ALL}')
        elif i.startswith('readfile'):
            bstart = '╭'
            file_to_read = i[9:].strip()
            print(f'{Fore.YELLOW}├─ Запрос на чтение файла: {file_to_read}{Style.RESET_ALL}')
            content = read_file_content(file_to_read)
            print(f'{Fore.YELLOW}│ Содержимое файла {file_to_read}:{Style.RESET_ALL}')
            print(f'{Fore.YELLOW}│{Style.RESET_ALL}')
            for line in content.split('\n'):
                print(f'{Fore.YELLOW}│ {line}{Style.RESET_ALL}')
            print(f'{Fore.YELLOW}│{Style.RESET_ALL}')
            print(f'{Fore.YELLOW}├─{"─"*50}{Style.RESET_ALL}')
        elif i.startswith('analyze'):
            bstart = '╭'
            file_to_analyze = i[8:].strip()
            print(f'{Fore.LIGHTBLUE_EX}├─ Анализ файла: {file_to_analyze}{Style.RESET_ALL}')
            
            # Читаем файл
            content = read_file_content(file_to_analyze)
            
            if content.startswith("Файл не найден") or content.startswith("Ошибка"):
                print(f'{Fore.RED}│ {content}{Style.RESET_ALL}')
            else:
                print(f'{Fore.LIGHTBLUE_EX}│ Содержимое файла:{Style.RESET_ALL}')
                print(f'{Fore.LIGHTBLUE_EX}├─{"─"*50}{Style.RESET_ALL}')
                print(f'{Fore.CYAN}│{Style.RESET_ALL}')
                for line_num, line in enumerate(content.split('\n'), 1):
                    print(f'{Fore.CYAN}│{line_num:4d}: {line}{Style.RESET_ALL}')
                print(f'{Fore.LIGHTBLUE_EX}│ Анализ Python файла:{Style.RESET_ALL}')
                print(Fore.LIGHTGREEN_EX + analyze_file(ques, content))
                
                print(f'{Fore.CYAN}│{Style.RESET_ALL}')
            
            print(f'{Fore.LIGHTBLUE_EX}├─{"─"*50}{Style.RESET_ALL}')

# Проверка компонентов
ans = {}
components = ''
dir_contents_info = get_current_directory_contents()

if not check_git_installation()[0]:
    print(f'{Fore.RED}Для работы с Git необходимо его установить.\n{Fore.CYAN}https://git-scm.com/install/windows{Style.RESET_ALL}')
else:
    print(f'{Fore.GREEN}Git установлен.\n{Fore.CYAN}Версия: {check_git_installation()[1]}\n{Fore.LIGHTBLACK_EX}─{"─"*50}{Style.RESET_ALL}')
    components += f'Git установлен. Версия: {check_git_installation()[1]}'

if not check_gh_installation()[0]:
    print(f'{Fore.RED}Для работы с GitHub CLI необходимо его установить.\n{Fore.CYAN}https://cli.github.com/{Style.RESET_ALL}')
else:
    print(f'{Fore.GREEN}GitHub CLI установлен.\n{Fore.CYAN}Версия: {check_gh_installation()[1]}\n{Fore.LIGHTBLACK_EX}─{"─"*50}{Style.RESET_ALL}')
    components += f'\nGitHub CLI установлен. Версия: {check_gh_installation()[1]}'

if not check_docker()[0]:
    print(f'{Fore.RED}Для работы с Docker необходимо его установить.\n{Fore.CYAN}https://www.docker.com/products/docker-desktop{Style.RESET_ALL}')
else:
    print(f'{Fore.GREEN}Docker установлен.\n{Fore.CYAN}Версия: {check_docker()[1]}\n{Fore.LIGHTBLACK_EX}─{"─"*50}{Style.RESET_ALL}')
    components += f'\nDocker установлен. Версия: {check_docker()[1]}'

if not check_python()[0]:
    print(f'{Fore.RED}Для работы с Python необходимо его установить.\n{Fore.CYAN}https://www.python.org/downloads/windows/{Style.RESET_ALL}')
else:
    print(f'{Fore.GREEN}Python установлен.\n{Fore.CYAN}Версия: {check_python()[1]}\n{Fore.LIGHTBLACK_EX}─{"─"*50}{Style.RESET_ALL}')
    components += f'\nPython установлен. Версия: {check_python()[1]}'

current_dir = Path.cwd()

# Получаем содержимое текущей директории для промпта
dir_contents = "\n".join([f'  - {item}' for item in sorted([p.name for p in current_dir.iterdir()])]) if list(current_dir.iterdir()) else "  (пусто)"

prompt = f'''
Ты — ассистент пользователя с доступом к файловой системе.

У тебя есть несколько режимов работы:

1. **ОБЫЧНЫЙ РЕЖИМ (для разговора)**:  
   Когда пользователь просто общается с тобой (приветствия, вопросы, разговор) — отвечай обычным текстом, без использования специальных форматов.

2. **АНАЛИТИЧЕСКИЙ РЕЖИМ (для анализа кода)**:  
   Когда пользователь просит проанализировать файл (например, "Проанализируй файл calculator.py и найди в нем ошибки") — используй команду:
   analyze путь_к_файлу
   
   После этой команды система:
   1. Прочитает содержимое файла
   2. Проверит синтаксис (для Python файлов)
   3. Запустит файл (для Python файлов)
   4. Покажет результат выполнения
   5. Покажет полное содержимое файла с номерами строк

   Затем ты можешь проанализировать результаты и:
   - Указать на конкретные ошибки с номерами строк
   - Предложить исправления
   - Использовать обычный текст для объяснений

3. **КОМАНДНЫЙ РЕЖИМ (для работы с файловой системой)**:  
   Когда пользователь просит выполнить операции с файлами или директориями (создать, изменить, скопировать, удалить и т.д.) — используй **ТОЛЬКО** специальные форматы:

   **Для команд терминала (начинай строку строго с `cmd `):**
   cmd команда_для_выполнения

   **Для создания файлов с содержимым:**
   file имя_файла
   ^^^
   содержимое файла
   ^^^
   
   **Для чтения файлов (когда тебе просто нужно посмотреть содержимое):**
   readfile путь_к_файлу

**ВАЖНО: После команды `analyze` ты МОЖЕШЬ использовать обычный текст для анализа!**
Пример правильного ответа на "Проанализируй calculator.py":
analyze calculator.py
(система покажет содержимое и результаты проверки)
Я проанализировал файл calculator.py. Вот что я обнаружил:
1. На строке 5: отсутствует двоеточие после условия if
2. На строке 10: переменная result не определена
3. Файл содержит синтаксическую ошибку: invalid syntax

Предлагаю исправить следующим образом:
file calculator.py
^^^
исправленный код
^^^

**АБСОЛЮТНО ЗАПРЕЩЕНО:**
- Использовать ```python, ```bash, ``` или любые другие обёртки кода
- Давать объяснения или инструкции в текстовом виде при работе с файлами в командном режиме
- Смешивать обычный текст и команды в одном ответе (кроме аналитического режима)
- Использовать markdown форматирование в командном режиме
- Использовать плейсхолдеры типа [имя_репо] или [путь_к_репо] - используй реальные команды

**КОНКРЕТНЫЕ ИНСТРУКЦИИ ДЛЯ АНАЛИЗА ФАЙЛОВ:**

1. **Анализ Python файлов:**
   analyze имя_файла.py
   (система проверит синтаксис и запустит файл)

2. **После получения результатов анализа:**
   - Проанализируй вывод системы
   - Укажи конкретные строки с ошибками
   - Объясни проблему обычным текстом
   - Предложи исправления через команду `file`

3. **Пример полного анализа:**
   analyze myfile.py
   (получаем результаты)
   Обнаружены следующие проблемы:
   1. Строка 3: ImportError - модуль не найден
   2. Строка 8: NameError - переменная не определена
   
   Исправленная версия:
   file myfile.py
   ^^^
   исправленный код
   ^^^

**ПРАВИЛА ОТВЕТА:**
1. Если запрос НЕ требует работы с файловой системой → отвечай обычным текстом
2. Если запрос требует анализа файлов → используй `analyze`, затем анализируй обычным текстом
3. Если запрос требует работы с файлами/директориями (не анализа) → используй ТОЛЬКО `cmd`, `file` или `readfile` форматы
4. После команды `analyze` можешь свободно использовать обычный текст для анализа результатов
5. Всегда используй реальные, исполняемые команды (без плейсхолдеров)

**ПРИМЕРЫ ПРАВИЛЬНЫХ ОТВЕТОВ:**

1. **Анализ файла:**
   analyze calculator.py
   На строке 5 обнаружена синтаксическая ошибка: отсутствует двоеточие. 
   Предлагаю исправить:
   file calculator.py
   ^^^
   исправленный код
   ^^^

2. **Простой просмотр:**
   readfile config.txt

3. **Команды:**
   cmd git status

---

**ИНФОРМАЦИЯ О СИСТЕМЕ:**  
- ОС: {platform.system()} {platform.release()}  
- Текущая директория: {current_dir}

**СОДЕРЖИМОЕ ТЕКУЩЕЙ ДИРЕКТОРИИ:**
{dir_contents}

**ДОСТУПНЫЕ ИНСТРУМЕНТЫ:**
- Командная строка (через cmd)
- Создание/редактирование файлов (через file)
- Чтение файлов (через readfile)
- Анализ файлов (через analyze) - проверка синтаксиса и запуск
- Git: {check_git_installation()[1] if check_git_installation()[0] else "Не установлен"}
- GitHub CLI: {check_gh_installation()[1] if check_gh_installation()[0] else "Не установлен"}
- Docker: {check_docker()[1] if check_docker()[0] else "Не установлен"}
- Python: {check_python()[1] if check_python()[0] else "Не установлен"}

---
Используй правильный формат в зависимости от запроса. После `analyze` можешь свободно анализировать обычным текстом.
Отвечай только на русском языке. Используй только реальные команды без плейсхолдеров.
'''

hystory = [{"role": "system", "content": prompt}]
hystory.append({"role": "user", "content": 'Напиши Ок, если ты понял правила'})

print(Fore.CYAN, end='')
c = 0
while True:
    try:
        ans = answer('Напиши Ок, если ты понял правила', hystory)
        print(ans)
        hystory.append({"role": "assistant", "content": ans})
        break
    except KeyboardInterrupt:
        print(Style.RESET_ALL)
        sys.exit(1)
    except Exception as e:
        print(f'{Fore.RED}Ошибка: {e}{Style.RESET_ALL}')
        if c == 5:
            print(f'{Fore.RED}Превышено количество попыток{Style.RESET_ALL}')
            sys.exit(0)
        c += 1
print(Style.RESET_ALL)

print(f'{Fore.CYAN}╭─ Info: {Fore.LIGHTBLACK_EX}Загрузка завершена.{Style.RESET_ALL}')

while True:
    try:
        # Обновляем содержимое директории перед каждым запросом
        current_dir = Path.cwd()
        dir_contents = "\n".join([f"  - {item}" for item in sorted([p.name for p in current_dir.iterdir()])]) if list(current_dir.iterdir()) else "  (пусто)"
        
        query = input(f'''{Fore.CYAN}│
│
├─ {Fore.LIGHTCYAN_EX}Path: {Style.RESET_ALL}{Fore.LIGHTGREEN_EX}{current_dir}{Style.RESET_ALL}
{Fore.CYAN}{bstart}─ You:
│ {Fore.LIGHTCYAN_EX}''')
        print(Fore.CYAN + '│' + Style.RESET_ALL)
        
        if query.lower() == 'exit':
            break
            
        # Добавляем информацию о текущей директории к запросу
        enhanced_query = f"Содержимое текущей директории:\n{dir_contents}\n\nЗапрос пользователя: {query}"
        
        hystory.append({"role": "user", "content": enhanced_query})
        ans = answer(enhanced_query, hystory)
        hystory.append({"role": "assistant", "content": ans})
        draw_tui_window(ques=query, ans=ans)
        bstart = '├'
        
    except KeyboardInterrupt:
        print(f'\n{Fore.YELLOW}Выход...{Style.RESET_ALL}')
        sys.exit(1)
    except Exception as e:
        print(f'{Fore.RED}Ошибка: {e}{Style.RESET_ALL}')