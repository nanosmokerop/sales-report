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
plans_sheet = spreadsheet.worksheet("Годовой план 26")

sales = sales_sheet.get_all_records()
plans = plans_sheet.get_all_records()

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

    plan = next(
        (row["План"] for row in plans
         if row["Менеджер"] == manager and row["Месяц"] == current_month),
        0
    )

    percent = round(month_sum / plan * 100, 1) if plan else 0

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
