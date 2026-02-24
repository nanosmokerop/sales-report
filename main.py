import os
import re
from telegram import Bot
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import calendar

TOKEN = os.environ["TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
SHEET_NAME = os.environ["SHEET_NAME"]
PLAN = float(os.environ["PLAN"])  # 🔥 общий план

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

# ⚠️ Меняй каждый месяц
current_month = "ОПТ Февраль 2026"

sales_sheet = spreadsheet.worksheet(current_month)
rows = sales_sheet.get_all_values()

data_rows = rows[4:]

sales = []

for row in data_rows:
    if len(row) < 10:
        continue

    manager = row[0]
    date = row[1]
    amount = row[9]

    if not manager or not amount:
        continue

    try:
        cleaned = re.sub(r"[^\d.,]", "", str(amount))
        cleaned = cleaned.replace(" ", "").replace(",", ".")
        amount = float(cleaned)
    except:
        amount = 0

    sales.append({
        "Менеджер": manager.strip(),
        "Дата": date.strip(),
        "Сумма": amount
    })

managers = sorted(list(set(row["Менеджер"] for row in sales)))

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

    percent = round((month_sum / PLAN) * 100, 1) if PLAN else 0

    message += (
        f"{manager}\n"
        f"Сегодня: {int(today_sum):,}\n"
        f"Месяц: {int(month_sum):,} / {int(PLAN):,}\n"
        f"Выполнение: {percent}%\n\n"
    )

last_day = calendar.monthrange(today.year, today.month)[1]
if today.day == last_day:
    message += "🏁 Итог месяца сформирован\n"

bot = Bot(token=TOKEN)
bot.send_message(chat_id=CHAT_ID, text=message)
