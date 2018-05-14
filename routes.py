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
		bot.sendMessage(chat_id=update.message.chat_id, text='Got your message loud and clear, {}.'.format(update.message.from_user.username))
	elif update.inline_query is not None:
		res = []
		res.append(getArticleFromText('First option - which is nice'))
		res.append(getArticleFromText('Second option - not as much'))
		res.append(getArticleFromText('Third option - total shit'))
		bot.answerInlineQuery(update.inline_query.id, res)
	return 'OK'

def getArticleFromText(text):
	return telegram.InlineQueryResultArticle(id=text.upper(), title=text, input_message_content=telegram.InputTextMessageContent(text))