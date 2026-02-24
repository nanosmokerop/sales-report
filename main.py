import os
from telegram import Bot
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import calendar

# ===== НАСТРОЙКИ =====

TOKEN = os.environ["TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
SHEET_NAME = os.environ["SHEET_NAME"]
PLAN = int(os.environ["PLAN"])

current_month = "ОПТ Февраль 2026"

# ===== GOOGLE SHEETS =====

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]

creds = ServiceAccountCredentials.from_json_keyfile_dict(
    eval(os.environ["GOOGLE_CREDENTIALS"]), scope
)

client = gspread.authorize(creds)
spreadsheet = client.open(SHEET_NAME)
sales_sheet = spreadsheet.worksheet(current_month)

sales = sales_sheet.get_all_values()[1:]

today = datetime.now()
today_str = today.strftime("%d.%m.%Y")

# ===== ФИЛЬТРУЕМ ТОЛЬКО РЕАЛЬНЫЕ ПРОДАЖИ =====

clean_rows = []

for row in sales:

    if len(row) < 10:
        continue

    manager = row[0].strip()
    payment_date = row[8].strip()
    raw_sum = row[9].strip()

    if not manager:
        continue

    if not payment_date:
        continue

    if not raw_sum:
        continue

    # чистим сумму
    raw_sum = (
        raw_sum
        .replace("р.", "")
        .replace("р", "")
        .replace(" ", "")
        .replace(",", ".")
        .strip()
    )

    try:
        amount = float(raw_sum)
    except:
        continue

    clean_rows.append((manager, payment_date, amount))

# получаем список менеджеров
managers = list(set(row[0] for row in clean_rows))

message = f"📊 Отчёт за {today_str}\n\n"

# ===== РАСЧЁТ =====

for manager in managers:

    today_sum = 0
    month_sum = 0

    for row in clean_rows:

        row_manager, payment_date, amount = row

        if row_manager != manager:
            continue

        month_sum += amount

        if payment_date == today_str:
            today_sum += amount

    percent = round(month_sum / PLAN * 100, 1) if PLAN else 0

    message += (
        f"{manager}\n"
        f"Сегодня: {int(today_sum):,}\n"
        f"Месяц: {int(month_sum):,} / {PLAN:,}\n"
        f"Выполнение: {percent}%\n\n"
    )

# ===== ПОСЛЕДНИЙ ДЕНЬ МЕСЯЦА =====

last_day = calendar.monthrange(today.year, today.month)[1]
if today.day == last_day:
    message += "🏁 Итог месяца сформирован\n"

bot = Bot(token=TOKEN)
bot.send_message(chat_id=CHAT_ID, text=message)
