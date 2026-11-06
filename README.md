# Визуализатор зависимостей Ubuntu — вариант 12

Практическая работа 2. Этап 1: Конфигурация CLI.
Python 3.12+, только стандартная библиотека для получения зависимостей.

## Подготовка и запуск

Сборка не требуется. В PowerShell из корня проекта:

```powershell
python -m venv .venv
.\run.bat --package bash --version 5.2.21-2ubuntu4
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Прямой запуск: `python src/apt_graph/main.py --package bash --version 5.2.21-2ubuntu4`.
В PyCharm: интерпретатор .venv, модуль src.apt_graph.main, рабочая папка — корень проекта.
Linux: `python3 -m src.apt_graph.main --package bash --version 5.2.21-2ubuntu4`.

## Настройки

| Опция | Значение |
| --- | --- |
| --package | Обязательное имя пакета; в тестовом режиме A-Z |
| --version | Обязательная точная версия пакета, не latest |
| --repository | HTTP(S) URL индекса Packages[.gz/.xz] или путь тестового JSON |
| --test-mode | Читать тестовый репозиторий (с этапа 3) |
| --ascii | Печатать ASCII-дерево (этап 5) |
| --max-depth | Глубина 0..200, по умолчанию 5 |

Индекс по умолчанию: Ubuntu noble, main, binary-amd64 (см. default_repository в config.py).
URL должен указывать именно на индекс пакетов, а не на главную страницу зеркала.
Один индекс задаёт область анализа. Пакеты из отсутствующих компонентов не выдумываются.
Флаги --test-mode и --ascii не принимают значения true/false.
Ошибки параметров: код 2; ошибки данных/сети/визуализации: код 1; успех: код 0.

Ошибочные вызовы (проверять отдельно):

```powershell
.\run.bat --package ../bad --version 1
.\run.bat --package bash --version latest
.\run.bat --package bash --version 1 --repository ftp://host
.\run.bat --package A --version 1 --test-mode --repository missing.json
.\run.bat --package bash --version 1 --ascii false
.\run.bat --package bash --version 1 --max-depth -1
```

## Поведение этапа

Выводятся шесть настроек ключ=значение. Сетевых запросов нет.

## Описание функций

### config.py

- `depth_value`: Accept a bounded BFS level count, with the root at level zero.
- `validate_url`: Require an HTTP(S) index URL without credentials or fragments.
- `validate_settings`: Check names, exact version and repository location for both modes.
- `parse_args`: Return validated CLI options or terminate with argparse error code 2.

### main.py

- `main`: Validate settings and display the six key-value pairs.

## Проверки

tests содержит функциональные тесты и проверку структуры/ограничений исходников.
Перед коммитом также проверяются flake8 (включая naming) и radon.
Источники формата: Debian Policy, разделы 5 (control fields) и 7 (relationships).
https://www.debian.org/doc/debian-policy/ch-controlfields.html
https://www.debian.org/doc/debian-policy/ch-relationships.html
