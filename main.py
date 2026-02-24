import os
from telegram import Bot
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta
import calendar

TOKEN = os.environ["TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
SHEET_NAME = os.environ["SHEET_NAME"]
PLAN = int(os.environ["PLAN"])

current_month = "ОПТ Февраль 2026"  # меняй каждый месяц

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

all_rows = sheet.get_all_values()

header_row_1 = all_rows[0]
header_row_2 = all_rows[1]

headers = []
for i in range(len(header_row_1)):
    part1 = header_row_1[i] if i < len(header_row_1) else ""
    part2 = header_row_2[i] if i < len(header_row_2) else ""
    headers.append((part1 + " " + part2).strip().lower())


def find_column(keyword):
    for i, col in enumerate(headers):
        if keyword in col:
            return i
    raise Exception(f"Колонка '{keyword}' не найдена")


manager_col = find_column("менеджер")
date_col = find_column("дата")
payment_col = find_column("оплат")

today = datetime.now().date()
data_rows = all_rows[2:]

managers_data = {}

for row in data_rows:

    if len(row) <= max(manager_col, date_col, payment_col):
        continue

    manager = row[manager_col].strip()
    date_raw = row[date_col].strip()
    sum_raw = row[payment_col].strip()

    if not manager or not date_raw or not sum_raw:
        continue

    # --- ПАРСИНГ ДАТЫ ---
    payment_date = None

    # если число (google serial date)
    if date_raw.isdigit():
        try:
            serial = int(date_raw)
            payment_date = datetime(1899, 12, 30) + timedelta(days=serial)
            payment_date = payment_date.date()
        except:
            continue
    else:
        # если строка
        for fmt in ("%d.%m.%Y", "%d.%m.%y", "%Y-%m-%d"):
            try:
                payment_date = datetime.strptime(date_raw, fmt).date()
                break
            except:
                continue

    if not payment_date:
        continue

    # --- ПАРСИНГ СУММЫ ---
    sum_raw = (
        sum_raw.replace("р.", "")
        .replace("р", "")
        .replace(" ", "")
        .replace(",", ".")
    )

    try:
        amount = float(sum_raw)
    except:
        continue

    if manager not in managers_data:
        managers_data[manager] = {"today": 0, "month": 0}

    if payment_date.month == today.month and payment_date.year == today.year:
        managers_data[manager]["month"] += amount

        if payment_date == today:
            managers_data[manager]["today"] += amount


today_str = today.strftime("%d.%m.%Y")
message = f"📊 Отчёт за {today_str}\n\n"

if not managers_data:
    message += "Нет данных для расчёта."
else:
    for manager, data in managers_data.items():

        percent = round(data["month"] / PLAN * 100, 1) if PLAN else 0

        message += (
            f"{manager}\n"
            f"Сегодня: {int(data['today']):,}\n"
            f"Месяц: {int(data['month']):,} / {PLAN:,}\n"
            f"Выполнение: {percent}%\n\n"
        )

    last_day = calendar.monthrange(today.year, today.month)[1]
    if today.day == last_day:
        message += "🏁 Итог месяца сформирован\n"

bot = Bot(token=TOKEN)
bot.send_message(chat_id=CHAT_ID, text=message)
