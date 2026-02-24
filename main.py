import os
from telegram import Bot
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import calendar

TOKEN = os.environ["TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
SHEET_NAME = os.environ["SHEET_NAME"]

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]

creds = ServiceAccountCredentials.from_json_keyfile_dict(
    eval(os.environ["GOOGLE_CREDENTIALS"]), scope
)

client = gspread.authorize(creds)
spreadsheet = client.open(SHEET_NAME)

today = datetime.now()
today_str = today.strftime("%d.%m.%Y")
current_month = "ОПТ Февраль 2026"

# 🔥 Берём лист текущего месяца
sales_sheet = spreadsheet.worksheet(current_month)

rows = sales_sheet.get_all_values()

# предполагаем что данные начинаются с 5 строки
data_rows = rows[4:]  

sales = []

for row in data_rows:
    if len(row) < 3:
        continue

    manager = row[0]        # колонка A — Менеджер
    date = row[1]           # колонка B — Дата оформления
    amount = row[9]         # колонка J — Оплата (проверь номер!)

    if not manager or not amount:
        continue

    try:
        amount = float(str(amount).replace(" ", "").replace(",", "."))
    except:
        amount = 0

    sales.append({
        "Менеджер": manager,
        "Дата": date,
        "Сумма": amount
    })
managers = list(set(row["Менеджер"] for row in sales))

message = f"📊 Отчёт за {today_str}\n\n"

for manager in managers:
    today_sum = sum(
        row["Сумма"]
        for row in sales
        if row["Менеджер"] == manager and row["Дата"] == today_str
    )

    month_sum = sum(
        row["Сумма"]
        for row in sales
        if row["Менеджер"] == manager
    )

message += (
    f"{manager}\n"
    f"Сегодня: {today_sum}\n"
    f"Месяц: {month_sum}\n\n"
)

    message += (
        f"{manager}\n"
        f"Сегодня: {today_sum}\n"
        f"Месяц: {month_sum} / {plan}\n"
        f"Выполнение: {percent}%\n\n"
    )

# Проверка последний ли день месяца
last_day = calendar.monthrange(today.year, today.month)[1]
if today.day == last_day:
    message += "🏁 Итог месяца сформирован\n"

bot = Bot(token=TOKEN)
bot.send_message(chat_id=CHAT_ID, text=message)
