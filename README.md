# FinTrack – Personal Finance Dashboard

A Django app to log expenses/income, set savings goals, and view analytics. Track monthly breakdowns with charts and export reports.

Summary of my data model -
- Transactions belong to a User and a Category (on_delete=PROTECT keeps history).
- Categories can be global (user=None) or user-specific and are unique per (user, name, type).
- Goals are unique per (user, title) and store target/current progress.

## ER Diagram

```mermaid
erDiagram
    USER ||--o{ CATEGORY : "defines (optional)"
    USER ||--o{ TRANSACTION : "owns"
    USER ||--o{ GOAL : "owns"
    CATEGORY ||--o{ TRANSACTION : "classifies"

    USER {
        int id PK
        string username
    }
    CATEGORY {
        int id PK
        int user_id FK "nullable for global"
        string name
        string type "EXPENSE/INCOME"
        UNIQUE (user_id, name, type)
    }
    TRANSACTION {
        int id PK
        int user_id FK
        int category_id FK
        decimal amount
        string kind "EXPENSE/INCOME"
        date date
        string merchant
        text notes
    }
    GOAL {
        int id PK
        int user_id FK
        string title
        decimal target_amount
        decimal current_amount
        date deadline
        UNIQUE (user_id, title)
    }
