from bottle import route, view, run, request
import telegram

TOKEN = '552988587:AAFOqPcC-5eDV3HWeYS9yUGGsx_2IiLLCxM'
APPNAME = 'worldcupbetsbot'

@route('/setWebhook')
def setWebhook():
	bot = telegram.Bot(TOKEN)
	botWebhookResult = bot.setWebhook(webhook_url='https://{}.azurewebsites.net/botHook'.format(APPNAME))
	return str(botWebhookResult)

@route('/botHook', method='POST')
def botHook():
	bot = telegram.Bot(TOKEN)
	update = telegram.update.Update.de_json(request.json, bot)
	if update.message is not None:
		bot.sendMessage(chat_id=update.message.chat_id, text='Got you message loud and clear, {}.'.format(update.message.from_user.username))
	elif update.inline_query is not None:
		bot.answerInlineQuery(update.inline_query.id, ['First option - which is nice', 'Second option - not as much', 'Third option - total shit'])
	return 'OK'