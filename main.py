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

# данные начинаются с 5 строки (по твоему скрину)
data_rows = rows[4:]

sales = []

for row in data_rows:
    if len(row) < 10:
        continue

    manager = row[0]      # колонка A
    date = row[1]         # колонка B
    amount = row[9]       # колонка J (Оплата)

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

# Проверка последний ли день месяца
last_day = calendar.monthrange(today.year, today.month)[1]
if today.day == last_day:
    message += "🏁 Итог месяца сформирован\n"

bot = Bot(token=TOKEN)
bot.send_message(chat_id=CHAT_ID, text=message)
