import os
from telegram import Bot
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import calendar

TOKEN = os.environ["TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
SHEET_NAME = os.environ["SHEET_NAME"]
PLAN = int(os.environ["PLAN"])

# 👇 МЕНЯЙ КАЖДЫЙ МЕСЯЦ НАЗВАНИЕ ЛИСТА
current_month = "ОПТ Февраль 2026"

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]

creds = ServiceAccountCredentials.from_json_keyfile_dict(
    eval(os.environ["GOOGLE_CREDENTIALS"]), scope
)

client = gspread.authorize(creds)
spreadsheet = client.open(SHEET_NAME)
sheet = spreadsheet.worksheet(current_month)

# 🔥 Читаем ВСЮ таблицу
all_rows = sheet.get_all_values()

# ✅ Заголовки в первой строке
headers = all_rows[0]

# Находим нужные колонки
manager_col = headers.index("Менеджер")
payment_date_col = headers.index("Дата оплаты")
payment_col = headers.index("Оплата")

today = datetime.now()
today_str = today.strftime("%d.%m.%Y")

clean_rows = []

# Данные начинаются со второй строки
for row in all_rows[1:]:

    # защита от коротких строк
    if len(row) <= max(manager_col, payment_date_col, payment_col):
        continue

    manager = row[manager_col].strip()
    payment_date = row[payment_date_col].strip()
    raw_sum = row[payment_col].strip()

    if not manager or not payment_date or not raw_sum:
        continue

    # очищаем "р. 85 675"
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

# Уникальные менеджеры
managers = list(set(row[0] for row in clean_rows))

message = f"📊 Отчёт за {today_str}\n\n"

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

# Если последний день месяца
last_day = calendar.monthrange(today.year, today.month)[1]
if today.day == last_day:
    message += "🏁 Итог месяца сформирован\n"

bot = Bot(token=TOKEN)
bot.send_message(chat_id=CHAT_ID, text=message)
