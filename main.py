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

current_month = "ОПТ Февраль 2026"  # 👈 меняй каждый месяц

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

# === ОБЪЕДИНЯЕМ 1 И 2 СТРОКУ ЗАГОЛОВКОВ ===
header_row_1 = all_rows[0]
header_row_2 = all_rows[1] if len(all_rows) > 1 else []

headers = []
for i in range(max(len(header_row_1), len(header_row_2))):
    part1 = header_row_1[i] if i < len(header_row_1) else ""
    part2 = header_row_2[i] if i < len(header_row_2) else ""
    headers.append((part1 + " " + part2).strip())


def find_column(keyword):
    for i, col in enumerate(headers):
        if keyword.lower() in col.lower():
            return i
    raise Exception(f"Колонка с текстом '{keyword}' не найдена")


manager_col = find_column("менеджер")
payment_date_col = find_column("дата оплат")
payment_col = find_column("оплат")

today = datetime.now()
today_str = today.strftime("%d.%m.%Y")

clean_rows = []

# === ДАННЫЕ НАЧИНАЮТСЯ С 3 СТРОКИ ===
for row in all_rows[2:]:

    if len(row) <= max(manager_col, payment_date_col, payment_col):
        continue

    manager = row[manager_col].strip()
    payment_date = row[payment_date_col].strip()
    raw_sum = row[payment_col].strip()

    if not manager or not payment_date or not raw_sum:
        continue

    # === ИСПРАВЛЯЕМ ФОРМАТ ДАТЫ 09.02.26 → 09.02.2026 ===
    try:
        parts = payment_date.split(".")
        if len(parts[2]) == 2:
            payment_date = parts[0] + "." + parts[1] + ".20" + parts[2]
    except:
        pass

    # === ОЧИЩАЕМ СУММУ ===
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

if not clean_rows:
    message = f"📊 Отчёт за {today_str}\n\nНет данных для расчёта."
else:

    managers = sorted(list(set(row[0] for row in clean_rows)))

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

    last_day = calendar.monthrange(today.year, today.month)[1]
    if today.day == last_day:
        message += "🏁 Итог месяца сформирован\n"

bot = Bot(token=TOKEN)
bot.send_message(chat_id=CHAT_ID, text=message)
