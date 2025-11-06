import os
import json
import gspread
from datetime import datetime
from oauth2client.service_account import ServiceAccountCredentials
from config import GOOGLE_SHEET_NAME


def connect_to_sheet():
    """Подключение к Google Sheets через JSON из переменных окружения."""
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    json_data = os.getenv("GOOGLE_CREDENTIALS_JSON")

    if not json_data:
        raise Exception("❌ GOOGLE_CREDENTIALS_JSON is missing in environment variables")

    creds_dict = json.loads(json_data)
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)

    try:
        sheet = client.open(GOOGLE_SHEET_NAME).sheet1
    except gspread.SpreadsheetNotFound:
        sheet = client.create(GOOGLE_SHEET_NAME).sheet1
        sheet.append_row(["Время", "Клиент", "Заказ", "Адрес", "Сумма", "Оплата"])
    return sheet


def add_order(sheet, username, items, address, total, phone):
    """
    Добавляет новую строку в таблицу заказов.
    username — Telegram username клиента
    items — состав заказа
    address — адрес или комментарий "самовывоз"
    total — сумма заказа
    phone — номер телефона или статус оплаты
    """
    row = [
        datetime.now().strftime("%Y-%m-%d %H:%M"),
        username,
        items,
        address,
        total,
        phone
    ]
    sheet.append_row(row)
    print(f"✅ Добавлен заказ в таблицу: {username} — {total}₽")


def get_orders(sheet):
    """
    Возвращает все заказы в виде списка словарей:
    [
      {"Время": "...", "Клиент": "...", "Заказ": "...", "Адрес": "...", "Сумма": "...", "Оплата": "..."},
      ...
    ]
    Используется в /remind для отправки напоминаний.
    """
    try:
        data = sheet.get_all_records()
        print(f"📄 Загружено {len(data)} заказов из Google Sheets")
        return data
    except Exception as e:
        print(f"❌ Ошибка чтения заказов: {e}")
        return []
