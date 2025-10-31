# config_templates
В gitlab в ветке main хранятся переменные (variables) и сгенерированные скриптом конфигурации (results)

В main запрещены прямые коммиты, только через MR.\
При изменении переменных пользователь создает новую ветку "candidate*" и при коммите в нее создается вебхук в сторону внешнего генератора конфигурации. \
Генератор конфигурации использует шаблоны jinja2 и создает конфигурации с новыми переменными. Результат сохраняет в директорию results. Затем делает коммит в ту же ветку и создает MR в main с удалением исходной ветки. Согласующий подтверждает слияние. 

**Плюсы**

- Автоматизация — генерация конфигурации без ручного вмешательства

- Консистентность — переменные и конфигурации всегда синхронизированы

- Review — согласование сгенерированных конфигураций перед публикацией (вливанием в main)

- Безопасность — запрет прямых коммитов в main защищает от случайных изменений

- Полная история изменений переменных и конфигураций.

- Ветвление — параллельная работа над изменениями разных переменных

- Идемпотентность — генератор конфигурации создает MR только если есть изменения в конфиге (например, игнорируются изменения readme)

- Автоочистка репозитория — автоматическое удаление веток после мерджа

**Минусы**

- При изменении шаблона jinja2 требуется вручную запустить генератор конфигурации и провести Review

- Хранение исходных данных (переменных) и производных (конфигураций) в одном репозитории

- Возможны конфликты нескольких "долгоиграющих" изменений

## GIT graph
### Одно изменение
```mermaid
gitGraph
    commit id: "Initial"
    branch candidate_SRTxxxxx
    checkout candidate_SRTxxxxx
    commit id: "Коммит в variables"
    commit id: "Коммит в result" type: HIGHLIGHT
    checkout main
    merge candidate_SRTxxxxx id: "Merge SRTxxxxx"
```
### Последовательные изменения
```mermaid
gitGraph
    commit id: "Initial"
    branch candidate_SRTxxxxx
    checkout candidate_SRTxxxxx
    commit id: "Коммит в variables"
    commit id: "Коммит в result" type: HIGHLIGHT
    checkout main
    merge candidate_SRTxxxxx id: "Merge SRTxxxxx"
    branch candidate_SRTyyyyy
    checkout candidate_SRTyyyyy
    commit id: "Коммит_ в variables"
    commit id: "Коммит_ в result" type: HIGHLIGHT
    checkout main
    merge candidate_SRTyyyyy id: "Merge SRTyyyyy"
```

### Предварительная подготовка переменных без генерации конфига
```mermaid
gitGraph
    commit id: "Initial"
    checkout main
    branch prepare_SRTzzzzz
    commit id: "Коммит1 в variables"
    commit id: "Коммит2 в variables" 
    commit id: "Коммит3 в variables"
    commit id: "Коммит4 в variables"
    branch candidate_SRTzzzzz
    checkout candidate_SRTzzzzz
    commit id: "Коммит в result" type: HIGHLIGHT
    checkout main
    merge candidate_SRTzzzzz id: "Merge SRTzzzzz"
```

### Параллельная работа над переменными
```mermaid
gitGraph
    commit id: "Initial"
    branch candidate_SRTyyyyy
    checkout candidate_SRTyyyyy
    commit id: "Коммит_ в variables"
    commit id: "Коммит_ в result" type: HIGHLIGHT
    checkout main
    branch prepare_SRTzzzzz
    commit id: "Коммит1 в variables"
    commit id: "Коммит2 в variables" 
    commit id: "Коммит3 в variables"
    commit id: "Коммит4 в variables"
    branch candidate_SRTzzzzz
    checkout candidate_SRTzzzzz
    commit id: "Коммит5 в result" type: HIGHLIGHT
    checkout main
    merge candidate_SRTyyyyy id: "Merge SRTyyyyy"
    merge candidate_SRTzzzzz id: "Merge SRTzzzzz"
```

## Sequence Diagram

```mermaid
sequenceDiagram
    actor U as Инициатор изменения
    participant G as GitLab
    participant C as Генератор конфигурации
    actor A as Согласующий изменение


    U->>G: Забирает актуальное состояние ветки main
    activate U
    U->>G: Изменяет переменные
    U->>G: Создает ветку candidate*
    U->>G: Коммит в variables/ в ветку candidate*

    deactivate U
    
    G->>C: Вебхук на коммит в candidate*
    activate C
    
    C->>C: Забирает ветку candidate*
    C->>C: Генерирует конфигурацию с новыми переменными
    C->>G: Коммит в results/
    C->>G: Создает MR в main
    C->>G: Создает MR на удаление ветки
    
    deactivate C
    
    A->>G: Проверяет изменения в MR
    A->>G: Подтверждает слияние
    G->>G: Вливает candidate* в main
    G->>G: Удаляет ветку candidate*
```

## Процесс

```mermaid
graph TD
    subgraph "Ветка main"
        K[variables/]
        L[results/]
    end
    K --> A
    A[Инициатор изменения изменяет переменные и создает ветку candidate*] --> B[Коммит в variables/]
    B --> C[При каждом коммите от пользователя создается вебхук в генератор конфигурации]
    C --> D[Генерация конфигурации]
    D --> E[Коммит в results/]
    E --> F[Создание MR в main]
    F --> G[Согласующий изменение подтверждает слияние]
    G --> H[MR закрывается, ветка candidate* удаляется]
    
    subgraph "Ветка candidate*"
        B
        E
    end
    
    subgraph "Ветка main"
        I[variables/]
        J[results/]
    end
    
    H --> I
    H --> J
```