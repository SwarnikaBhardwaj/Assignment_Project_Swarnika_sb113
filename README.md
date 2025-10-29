# FinTrack - Personal Finance Dashboard

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

Assignment 4 update - I wired two function based views for the Transactions list. One view returns an HttpResponse using loader.get_template() and the other uses the render() shortcut. Both share the same template (transaction_list.html) that extends base.html and implements a {% for %} … {% empty %} state.

A5 Update - I added two class based views for transactions. One uses a base CBV with manual get() and the other uses a generic ListView. Templates extend base.html and include {% for %} loops with {% empty %}. I hve also refactored URL structure to include app urls separately.

A3 update - tightened data constraints. Category uniqueness split into scoped and global constraints so transactions now validate that their kind matches the linked category and require positive amounts.

A6 update - Added a Financial insights dashboardthat allows multi field filtering (basically search, category, date range, amount range) on transactions. The page displays dynamic aggregations including overall totals, spending breakdown by category with visual progress bars, top merchants by spending, and monthly spending trends. All aggregations update based on active filters.

A7 update - Added static file configuration and data visualization using Django staticfiles system and matplotlib charts. Static files are organized at my project root in static/tracker/ with custom CSS. Logo has also been added to navigation bar using {% load static %} and {% static %} template tags configured via STATICFILES_DIRS. 2 matplotlib charts generate PNG images from database aggregations. Monthly spending bar chart uses TruncMonth() and Sum() to show last 6 months of spending. Category pie chart again uses values() and annotate() to display top 6 expense categories. Charts served via BytesIO and HttpResponse with content_type='image/png' for memory efficiency.
New Charts page at /charts/ displays my visualizations with stat cards showing total transactions, total spending, and average transaction from Transaction model aggregations. Category breakdown table provides detailed data with real time updates.

A8 update - I use GET for searching transactions because the search parameters actually appear in the URL which lets users bookmark/share their own searches. I did used POST for creating new transactions because POST sends data securely in the request body and protects against CSRF attacks. Basically, GET is for reading and filtering data while POST is for creating or modifying data. Also, Function based views give me more control because I can see exactly what happens on GET and POST requests in one function. Class based views are shorter and cleaner as Django only handles the repetitive parts automatically. I used FormView for the CBV which required much less code (phew) but FBV felt easier to understand because everything is explicit.

A9 update - I added some API endpoints that return transaction data as JSON instead of HTML. This basically lets other programs access my data easily. The APIs I built give total transactions and spending and then the second one also breaks down spending by category with counts. Then I made a chart view that actually fetches data from my own API and draws a bar chart. Its pretty cool because the chart view acts like a client consuming the API. The chart shows up as a PNG image that browser displays. I also compared HttpResponse versus JsonResponse to understand the difference. JsonResponse automatically sets the content type to application/json and formats the data nicely. HttpResponse is more basic and I have to do everything myself.
To summarise the flow goes like database → API view → JSON → chart view → matplotlib → PNG → browser displays image.

