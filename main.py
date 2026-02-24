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
PLAN = int(os.environ["PLAN"])  # например 2300000

current_month = "ОПТ Февраль 2026"  # ← меняешь вручную раз в месяц

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

# Берём ВСЕ строки начиная со 2-й (игнорируем кривые заголовки)
sales = sales_sheet.get_all_values()[1:]

# ===== ДАТА =====

today = datetime.now()
today_str = today.strftime("%d.%m.%Y")

# ===== СОБИРАЕМ МЕНЕДЖЕРОВ =====

managers = list(set(row[0] for row in sales if row[0]))

message = f"📊 Отчёт за {today_str}\n\n"

# ===== РАСЧЁТ =====

for manager in managers:

    today_sum = 0
    month_sum = 0

    for row in sales:

        row_manager = row[0]              # Менеджер
        payment_date = row[8]             # Дата оплаты (колонка I)
        raw_sum = row[9]                  # Оплата (колонка J)

        if row_manager != manager:
            continue

        # очищаем сумму
        if isinstance(raw_sum, str):
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
            amount = 0

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

# ===== ПРОВЕРКА ПОСЛЕДНИЙ ЛИ ДЕНЬ =====

last_day = calendar.monthrange(today.year, today.month)[1]
if today.day == last_day:
    message += "🏁 Итог месяца сформирован\n"

# ===== ОТПРАВКА В TELEGRAM =====

bot = Bot(token=TOKEN)
bot.send_message(chat_id=CHAT_ID, text=message)
