# Визуализатор зависимостей Ubuntu — вариант 12

Практическая работа 2. Этап 4: Обратные зависимости.
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

По полному индексу строятся обратные рёбра, затем выполняется тот же
рекурсивный BFS от указанной версии. Выводятся пакеты, зависящие от неё,
с учётом глубины. Это обратные зависимости в выбранном индексе,
а не только в прямом графе корня.

Для тестового JSON версия каждой вершины равна 1. Пример: {"A": ["B"], "B": []}.
Все вершины должны быть объявлены. Дубликаты рёбер удаляются.

```powershell
.\run.bat --package A --version 1 --test-mode --repository examples/chain.json --max-depth 2
.\run.bat --package A --version 1 --test-mode --repository examples/diamond.json
.\run.bat --package A --version 1 --test-mode --repository examples/cycle.json
.\run.bat --package A --version 1 --test-mode --repository examples/empty.json
```

Реальный граф включает Depends и Pre-Depends; Recommends/Suggests не включены.
Ограничения Debian-версий сравниваются собственным кодом.
Показываются все удовлетворяющие альтернативы и виртуальные поставщики из индекса.
Это граф объявленных зависимостей, а не план установки APT с выбором одной альтернативы.
Для обычного имени выбирается наибольшая удовлетворяющая версия.
При отсутствии подходящей зависимости выводится ошибка с её именем.

Показать обратную цепочку C <- B <- A:

```powershell
.\run.bat --package C --version 1 --test-mode --repository examples/chain.json
```

Обратный поиск проверяет ограничения относительно точной выбранной версии корня,
в том числе когда в индексе есть другая, более новая версия.

## Описание функций

### config.py

- `depth_value`: Accept a bounded BFS level count, with the root at level zero.
- `validate_url`: Require an HTTP(S) index URL without credentials or fragments.
- `validate_settings`: Check names, exact version and repository location for both modes.
- `parse_args`: Return validated CLI options or terminate with argparse error code 2.

### control.py

- `parse_stanzas`: Unfold continuation lines and reject malformed or duplicate fields.
- `parse_packages`: Index binary package records by name and exact version.
- `declarations`: Return mandatory Pre-Depends and Depends as intact OR groups.

### fixtures.py

- `validate_graph`: Require declared uppercase vertices and lists of valid references.
- `__init__`: Read JSON and validate every edge before traversal.
- `root`: Reject absent names and versions even with zero traversal depth.
- `children`: Return deduplicated edges in stable declaration order.

### graph.py

- `build_graph`: Perform recursive BFS; each vertex is expanded at its shortest depth.
- `graph_lines`: Show each vertex including isolated roots and boundary leaves.
- `visit_level`: Expand a whole BFS frontier, then recurse to the next level.

### main.py

- `load_repository`: Select a validated local fixture or a downloaded Ubuntu index.
- `main`: Print reverse BFS edges across the entire selected repository.

### relations.py

- `parse_atom`: Return name, architecture qualifier, operator and required version.
- `parse_group`: Preserve every OR alternative in its original declaration order.
- `provided_names`: Read unversioned or exact-version Provides, rejecting other operators.

### repository.py

- `unpack_index`: Recognize gzip/xz by magic bytes and bound decompressed size.
- `download_index`: Download one Packages index with a timeout and size limit.
- `__init__`: Parse an already downloaded index without running apt or dpkg.
- `root`: Require an exact version and show available versions on failure.
- `direct`: Return direct declarations without discarding version constraints.

### resolver.py

- `__init__`: Index real names and virtual providers once per repository.
- `architecture_matches`: Accept native/any within the single-architecture binary index.
- `targets`: Resolve concrete versions and matching virtual providers.
- `virtual_targets`: Match versioned Provides without using the provider's own version.
- `newest`: Choose the greatest Debian version, not lexicographic order.
- `children`: Expand all available alternatives; fail unsatisfied OR groups.

### reverse.py

- `reverse_index`: Invert all declared edges, matching every satisfying target version.

### versions.py

- `split_version`: Split epoch and final Debian revision, validating version syntax.
- `character_order`: Sort tilde before end, letters before all other non-digit symbols.
- `compare_part`: Compare alternating nondigit and digit runs using Debian rules.
- `compare_versions`: Compare epochs, upstream versions, then Debian revisions.
- `satisfies`: Evaluate the five Debian relationship operators.

## Проверки

tests содержит функциональные тесты и проверку структуры/ограничений исходников.
Перед коммитом также проверяются flake8 (включая naming) и radon.
Источники формата: Debian Policy, разделы 5 (control fields) и 7 (relationships).
https://www.debian.org/doc/debian-policy/ch-controlfields.html
https://www.debian.org/doc/debian-policy/ch-relationships.html
