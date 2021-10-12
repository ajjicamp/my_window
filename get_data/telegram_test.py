import telegram

def telegram_massage(msg):
    bot = telegram.Bot(token='2067580744:AAGUlAzHUWQgu4lKQRAvYBEjpW2NPEXDRVg')
    chat_id = 989643939

    bot.sendMessage(chat_id=chat_id, text=msg)