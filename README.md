# FinTrack – Personal Finance Dashboard

A Django app to log expenses/income, set savings goals, and view analytics. Track monthly breakdowns with charts and export reports.

Summary of my data model -
- Transactions belong to a User and a Category (on_delete=PROTECT keeps history).
- Categories can be global (user=None) or user-specific and are unique per (user, name, type).
- Goals are unique per (user, title) and store target/current progress.

![ER Diagram](docs/notes/er_fintrack.png)

*Backup: ER diagram exported from mermaid.live*



Constraints (documented):
Category - UniqueConstraint(user, name, type)
Goal -UniqueConstraint(user, title)
Transaction.category uses on_delete=PROTECT (preserve history)
Default ordering - Transaction newest first, category by type/name; Goal by deadline.