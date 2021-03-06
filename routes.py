from bottle import route, view, run, request
import telegram
import sqlite3
import requests
import datetime as dtime
from datetime import datetime
import emoji
import calendar

DEBUG = True

# BOT SETTINGS
TOKEN = '552988587:AAFOqPcC-5eDV3HWeYS9yUGGsx_2IiLLCxM'
APPNAME = 'worldcupbetsbot'
ADMIN_USER_ID = 20961293

# RESPONSE RESULTS
SUCCESS_RESPONSE = 'success'

# RESPONSE PREFIX
PREFIX_BET_COMMAND = '/bet' # allowed only in private chat
PREFIX_MY_BETS_COMMAND = '/mybets' # allowed only in private chat
PREFIX_RANKS_COMMAND = '/ranks' # allowed only in groups
PREFIX_AUTHORIZE_GROUP_COMMAND = '/authorizegroup' # allowed only in groups
PREFIX_JOIN_COMMAND = '/join' # allowed only in groups
PREFIX_CHOSEN_MATCH = 'match'
PREFIX_BACK_CHOOSE_MATCH = 'backmatch'
PREFIX_HOME_BET = 'home'
PREFIX_AWAY_BET = 'away'

# UI
USR_INPUT_ERROR = "Communication with this bot is command based only. Type / and choose a command from the list."
USR_GROUP_INPUT_ERROR = "This command is valid only when sent from a group chat."
USR_PRIVATE_INPUT_ERROR = "This command is valid only when sent from the bot chat."
PICK_MATCHDAY = 'Please choose the match day.'
CHOOSE_MATCH = 'Choose a match to bet on. Mathces with a green mark are the ones you have already placed a bet on, so choose them only if you want to edit your bet.'
GOALS_AMOUNT_HOME = 'How many goals will be scored by {}?'
GOALS_AMOUNT_AWAY = 'And how many goals will be scored by {}?'
BTN_BACK = '{} BACK {}'
BTN_MATCH = '{} / {} {} - {} {}\n({})'
DECIDE_MATCH_SCORE = 'Decide how many goals will be scored by each team.\n{} is on the left, and {} is on the right.'
CONFIRM_BET = 'Your bet on {} vs. {} is registered. Use the /mybets command to review your bets.'
MATCH_ALREADY_STARTED = "Unfortunately, the match between {} and {} has already started. You can see the start time of a match before you choose to bet on it."
NO_USER_BETS = 'You have no bets at the moment. Use the /bet command to start betting.'
USR_INVALID_INPUT_HERE = 'Unkown command. Type in / and pick a command from the list.'

# SQLITE QUERIES
#SELECT_MATCHES = "SELECT * FROM groupStage WHERE start > datetime('now', '+{} day', '-{} hour') AND start < datetime('now', '+{} day', '+{} hour') ORDER BY start"
SELECT_MATCHES = "SELECT * FROM groupStage WHERE start > datetime('now') ORDER BY start LIMIT {}"
CREATE_GROUPSTAGE_TABLE = '''CREATE TABLE groupStage (matchId integer, groupName text, homeTeam text, awayTeam text, start timestamp, homeUnicode text, awayUnicode text)'''
INSERT_INTO_GROUPSTAGE = 'INSERT INTO groupStage VALUES (?,?,?,?,?,?,?)'
CREATE_BETS_TABLE = '''CREATE TABLE bets (userId text, userName text, matchId integer, homeBet integer, awayBet integer)'''
INSERT_INTO_BETS = 'INSERT INTO bets VALUES (?,?,?,?,?)'
EDIT_BET = "UPDATE bets SET homeBet=?, awayBet=? WHERE userId=? AND matchId=?"
SELECT_USER_BETS = "SELECT * FROM bets WHERE userId=?"
SELECT_USER_MATCH_BETS = "SELECT * FROM bets WHERE userId=? AND matchId=?"
SELECT_FUTURE_MATCH = "SELECT * FROM groupStage WHERE matchId=? AND start > datetime('now')"
CREATE_AUTHORIZED_GROUPS_TABLE = '''CREATE TABLE authorizedGroups (groupId text)'''
INSERT_INTO_AUTHORIZED_GROUPS = 'INSERT INTO authorizedGroups VALUES (?)'
SELECT_AUTHORIZED_GROUP = "SELECT * FROM authorizedGroups WHERE groupId=?"
CREATE_GROUP_USERS_TABLE = '''CREATE TABLE groupUsers (userId text, username text, groupId text)'''
INSERT_INTO_GROUP_USERS = 'INSERT INTO groupUsers VALUES (?,?,?)'
SELECT_GROUP_USER = "SELECT * FROM groupUsers WHERE groupId=? AND userId=?"
SELECT_USER_FROM_ANY_GROUP = "SELECT userId FROM groupUsers WHERE userId=?"
CREATE_USER_SCORE_TABLE = '''CREATE TABLE userScore (userId text, score real)'''
SELECT_USER_SCORE = "SELECT * FROM userScore WHERE userId=?"
INSERT_INTO_USER_SCORE = 'INSERT INTO userScore VALUES (?,?)'

# MATCH DB INDICES
DB_INDEX_MATCH_ID = 0
DB_INDEX_GROUP_NAME = 1
DB_INDEX_HOME_TEAM = 2
DB_INDEX_AWAY_TEAM = 3
DB_INDEX_MATCH_START = 4
DB_INDEX_HOME_UNICODE = 5
DB_INDEX_AWAY_UNICODE = 6

#BET DB INDICES
BET_DB_INDEX_USER_ID = 0
BET_DB_INDEX_USERNAME = 1
BET_DB_INDEX_MATCH_ID = 2
BET_DB_INDEX_HOME_GOALS = 3
BET_DB_INDEX_AWAY_GOALS = 4

ENTITY_BOT_CMD = 'bot_command'
CALLBACK_MATCH_SEPARATOR = '*'

MAX_UPCOMING_MATCHES = 6
MAX_GOALS_BET_AMOUNT = 8
HALF_BET_NUM_PARMS = 4
# END CONSTS

# UNICODE
UNICODE_BACK_ARROW = ':arrow_left:'
UNICODE_CHECK_MARK = ':white_check_mark:'
UNICODE_QUESTION_MARK = ':grey_question:'
UNICODE_CLAPPING_HANDS = ':clap:'
emoji_dict = {
    'Argentina:': ':flag_for_Argentina:',
	'Australia:': ':flag_for_Australia:',
	'Belgium:': ':flag_for_Belgium:',
	'Brazil:': ':flag_br:',
	'Colombia:': ':flag_co:',
	'Costa_Rica:': ':flag_cr:',
	'Croatia:': ':flag_hr:',
	'Denmark:': ':flag_dk:',
	'Egypt:': ':flag_eg:',
	'France:': ':flag_fr:',
	'Germany:': ':flag_de:',
	'Iceland:': ':flag_is:',
	'Iran:': ':flag_ir:',
	'Japan:': ':flag_jp:',
	'Mexico:': ':flag_mx:',
	'Morocco:': ':flag_ma:',
	'Nigeria:': ':flag_ng:',
	'Panama:': ':flag_pa:',
	'Peru:': ':flag_pe:',
	'Poland:': ':flag_pl:',
	'Portugal:': ':flag_pt:',
	'Russia:': ':flag_ru:',
	'Saudi_Arabia:': ':flag_sa:',
	'Senegal:': ':flag_sn:',
	'Serbia:': ':flag_rs:',
	'South_Korea:': ':flag_kr:',
	'Spain:': ':flag_es:',
	'Sweden:': ':flag_se:',
	'Switzerland:': ':flag_ch:',
	'Tunisia:': ':flag_tn:',
	'England:': ':flag_gb:',
	'Uruguay:': ':flag_uy:',
	}
UNICODE_DIGITS = {
	5 : ':keycap_digit_five:',
	4: ':keycap_digit_four:',
	1: ':keycap_digit_one:',
	7: ':keycap_digit_seven:',
	6: ':keycap_digit_six:',
	3: ':keycap_digit_three:',
	2: ':keycap_digit_two:',
	0: ':keycap_digit_zero:',
}

def get_execution_configuration():
	return 'Debug' if DEBUG else 'Prod'

def create_back_button():
	back_sign = emoji.emojize(UNICODE_BACK_ARROW, use_aliases=True)
	return telegram.InlineKeyboardButton(BTN_BACK.format(back_sign, back_sign), callback_data=PREFIX_BACK_CHOOSE_MATCH)

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
		return handle_message_update(update.message)
	elif update.callback_query is not None:
		return handle_callback_query(update.callback_query)
	return 'unkown update type'

#@route('/getUpdates')
#def get_updates():
	#bot = telegram.Bot(TOKEN)
	#update = bot.getUpdates(offset=145072792)[-1]
	#if update.message is not None:
	#	return handle_message_update(update.message)
	#elif update.callback_query is not None:
	#		return handle_callback_query(update.callback_query)
	#return 'unkown update type'

def is_user_authorized(user_id):
	bot = telegram.Bot(TOKEN)
	conn = sqlite3.connect('groupUsers.db')
	crsr = conn.cursor()
	crsr.execute(SELECT_USER_FROM_ANY_GROUP, (user_id,))
	return crsr.fetchone() is not None

def handle_callback_query(query):
	query_data = query.data
	msg = query.message
	if query_data.startswith(PREFIX_CHOSEN_MATCH):
		match_id, home_code, away_code = query_data[len(PREFIX_CHOSEN_MATCH):].split(CALLBACK_MATCH_SEPARATOR)
		return initial_bet_dialog(chat_id=msg.chat.id, message_id=msg.message_id, match_id=match_id, home_code=home_code, away_code=away_code)
	elif query_data.startswith(PREFIX_HOME_BET):
		query_params = query_data[len(PREFIX_HOME_BET):].split(CALLBACK_MATCH_SEPARATOR)
		if len(query_params) > HALF_BET_NUM_PARMS:
			# two bets were already made - place bet and confirm
			match_id, home_code, away_code, away_bet, home_bet = query_params
			return place_bet(
				query=query,
				chat_id=msg.chat.id,
				message_id=msg.message_id,
				match_id=match_id,
				home_code=home_code,
				away_code=away_code,
				home_bet=home_bet,
				away_bet=away_bet)
		else:
			# only home bet is made - mark it and wait for away bet
			match_id, home_code, away_code, home_bet = query_params
			return advanced_bet_dialog(
				chat_id=msg.chat.id,
				message_id=msg.message_id,
				match_id=match_id,
				home_code=home_code,
				away_code=away_code,
				home_bet=home_bet)
	elif query_data.startswith(PREFIX_AWAY_BET):
		query_params = query_data[len(PREFIX_AWAY_BET):].split(CALLBACK_MATCH_SEPARATOR)
		if len(query_params) > HALF_BET_NUM_PARMS:
			# two bets were already made - place bet and confirm
			match_id, home_code, away_code, home_bet, away_bet = query_params
			return place_bet(
				query=query,
				chat_id=msg.chat.id,
				message_id=msg.message_id,
				match_id=match_id,
				home_code=home_code,
				away_code=away_code,
				home_bet=home_bet,
				away_bet=away_bet)
		else:
			# only away bet is made - mark it and wait for home bet
			match_id, home_code, away_code, away_bet = query_params
			return advanced_bet_dialog(
				chat_id=msg.chat.id,
				message_id=msg.message_id,
				match_id=match_id,
				home_code=home_code,
				away_code=away_code,
				away_bet=away_bet)
	elif query_data.startswith(PREFIX_BACK_CHOOSE_MATCH):
		return get_matches(chat_id=msg.chat.id, user_id=msg.chat.id, edit_mode=True, message_id=msg.message_id)
	else:
		return 'unkown callback query'

def is_group_command(cmd):
	return is_entity_ranks_command(cmd) or is_entity_join_command(cmd)

def is_private_command(cmd):
	return cmd.startswith(PREFIX_BET_COMMAND) or cmd.startswith(PREFIX_MY_BETS_COMMAND)

def handle_message_update(msg):
	entities = msg.entities
	parsed_entities = [telegram.Message.parse_entity(msg, entity) for entity in entities if entity.type == ENTITY_BOT_CMD]
	if len(parsed_entities) > 0:
		parsed_entity = parsed_entities[0]
		if msg.chat.type != 'group':
			# assert user is joined
			if not is_user_authorized(msg.chat.id):
				return send_error_message(chat_id=msg.chat.id, error_message='You must belong to a betting group if you want us to talk.')
			if parsed_entity == PREFIX_BET_COMMAND:
				return get_matches(chat_id=msg.chat.id, user_id=msg.chat.id)
			elif parsed_entity == PREFIX_MY_BETS_COMMAND:
				return get_user_bets(chat_id=msg.chat.id, user_id=msg.chat.id)
			elif is_group_command(parsed_entity):
				return send_error_message(chat_id=msg.chat.id, error_message=USR_GROUP_INPUT_ERROR)
			else:
				return send_error_message(chat_id=msg.chat.id, error_message=USR_INVALID_INPUT_HERE)
		else:
			group_id = msg.chat.id
			if is_entity_authorize_command(parsed_entity):
				if msg.from_user.id == ADMIN_USER_ID:
					return handle_authorize_command(group_id)
				else:
					# send message that only admin can authorize a group
					return send_premissions_error_message(group_id)
			elif is_entity_join_command(parsed_entity):
				# accept command only if it comes from an authorized group
				if not is_authorized_group(group_id):
					return send_error_message(chat_id=group_id, error_message='Admin user must authorize this group before other users can join.')
				else:
					# group is authorized - handle command
					return handle_join_command(group_id, msg.from_user.id, msg.from_user.username)
			elif is_entity_ranks_command(parsed_entity):
				if not is_authorized_group(group_id):
					return send_premissions_error_message(group_id)
				else:
					# group is authorized - handle command
					return get_group_ranks(group_id=msg.chat.id)
			elif is_private_command(parsed_entity):
				return send_error_message(chat_id=msg.chat.id, error_message=USR_PRIVATE_INPUT_ERROR)
			else:
				# illegal command from group chat
				return send_error_message(chat_id=msg.chat.id, error_message=USR_INVALID_INPUT_HERE)
	else:
		bot.sendMessage(chat=msg.chat.id, text=USR_INPUT_ERROR)
		return 'no parsed entities'

def handle_join_command(group_id, user_id, username):
	if not is_authorized_group(group_id):
		txt = 'Admin user must authorize this group before users can join in.'
	else:
		bot = telegram.Bot(TOKEN)
		conn = sqlite3.connect('groupUsers.db')
		crsr = conn.cursor()
		crsr.execute(SELECT_GROUP_USER, (group_id, user_id))
		if crsr.fetchone() is not None:
			# user is already in this group - tag him
			txt = 'No need to join this group more than once @{}. Just head over to @{} in order to start placing bets.'.format(username, bot.getMe().username)
		else:
			# add group id to the authorized groups db
			crsr.execute(INSERT_INTO_GROUP_USERS, (user_id, username, group_id))
			conn.commit()
			conn.close()
			score_conn = sqlite3.connect('userScore.db')
			score_crsr = score_conn.cursor()
			score_crsr.execute(SELECT_USER_SCORE, (user_id,))
			if score_crsr.fetchone() is None:
				score_crsr.execute(INSERT_INTO_USER_SCORE, (user_id, 0))
				score_conn.commit()
				score_conn.close()
			claps = emoji.emojize(UNICODE_CLAPPING_HANDS, use_aliases=True)
			txt = '@{} has joined this group bets! {} {}'.format(username, claps, claps)
	bot.sendMessage(chat_id=group_id, text=txt)
	return SUCCESS_RESPONSE

def is_authorized_group(group_id):
	bot = telegram.Bot(TOKEN)
	conn = sqlite3.connect('authorizedGroups.db')
	crsr = conn.cursor()
	crsr.execute(SELECT_AUTHORIZED_GROUP, (group_id,))
	return crsr.fetchone() is not None

def send_premissions_error_message(chat_id):
	return send_error_message(chat_id, 'Only admin user can authorize groups.')

def handle_authorize_command(group_id):
	bot = telegram.Bot(TOKEN)
	conn = sqlite3.connect('authorizedGroups.db')
	crsr = conn.cursor()
	crsr.execute(SELECT_AUTHORIZED_GROUP, (group_id,))
	if crsr.fetchone() is not None:
		# group already authorized - notify group
		txt = 'This group has already been authorized.'
	else:
		# add group id to the authorized groups db
		crsr.execute(INSERT_INTO_AUTHORIZED_GROUPS, (group_id,))
		conn.commit()
		conn.close()
		txt = 'Hurray! Now that this group has been authorized, each user can hit the /join command and get started!'
	bot.sendMessage(chat_id=group_id, text=txt)
	return SUCCESS_RESPONSE

def is_entity_join_command(entity):
	return is_legal_command_format(entity, PREFIX_JOIN_COMMAND)

def is_entity_authorize_command(entity):
	return is_legal_command_format(entity, PREFIX_AUTHORIZE_GROUP_COMMAND)

def is_entity_ranks_command(entity):
	return is_legal_command_format(entity, PREFIX_RANKS_COMMAND)

def is_legal_command_format(command, expected):
	return command == expected or command == '{}@{}'.format(expected, telegram.Bot(TOKEN).getMe().username)

def get_group_ranks(group_id):
	# get user ids of users in given group id from group db
	bot = telegram.Bot(TOKEN)
	conn = sqlite3.connect('groupUsers.db')
	crsr = conn.cursor()
	crsr.execute("SELECT userId, username FROM groupUsers WHERE groupId=?", (group_id,))
	users = crsr.fetchall()
	if users is not None:
		score_conn = sqlite3.connect('userScore.db')
		score_crsr = score_conn.cursor()
		score_crsr.execute("SELECT * FROM userScore")
		scores = score_crsr.fetchall()
		if scores is not None:
			f = {}
			for t in scores:
				f[int(t[0])] = t[1]
			x = [(username, f[int(user_id)]) for user_id, username in users]
			x.sort(key=lambda r: r[1], reverse=True) # sort by score
			y = ['{}. {} - {}'.format(index+1, m[0], m[1]) for index, m in enumerate(x)]
			bot.sendMessage(chat_id=group_id, text='\n'.join(y))
			return SUCCESS_RESPONSE
	bot.sendMessage(chat_id=group_id, text='No scores at the moment..')
	return SUCCESS_RESPONSE

def send_error_message(chat_id, error_message):
	bot = telegram.Bot(TOKEN)
	bot.sendMessage(chat_id=chat_id, text=error_message)
	return SUCCESS_RESPONSE

def get_user_bets(chat_id, user_id):
	bot = telegram.Bot(TOKEN)
	conn = sqlite3.connect('bets.db')
	crsr = conn.cursor()
	crsr.execute(SELECT_USER_BETS, (user_id,))
	dic_user_bets = dict( [(bet[BET_DB_INDEX_MATCH_ID], (bet[BET_DB_INDEX_HOME_GOALS], bet[BET_DB_INDEX_AWAY_GOALS])) for bet in crsr.fetchall()] )
	if len(dic_user_bets) < 1:
		bot.sendMessage(chat_id=chat_id, text=NO_USER_BETS)
		return SUCCESS_RESPONSE
	matches_conn = sqlite3.connect('groupStage.db')
	group_crsr = matches_conn.cursor()
	group_crsr.execute("SELECT matchId, homeTeam, awayTeam, homeUnicode, awayUnicode FROM groupStage ORDER BY start DESC")
	template = '{} {} {} - {} {} {}'
	bets_lst = []
	for match in group_crsr.fetchall():
		match_id_val = int(match[0])
		if match_id_val in dic_user_bets:
			home_flag = emoji.emojize(match[3], use_aliases=True)
			home_team_name = match[1]
			home_bet = dic_user_bets[match_id_val][0]
			away_bet = dic_user_bets[match_id_val][1]
			away_team_name = match[2]
			away_flag = emoji.emojize(match[4], use_aliases=True)
			bets_lst.append(template.format(home_flag, home_team_name, home_bet, away_bet, away_team_name, away_flag))
	user_bets_msg = '\n\n'.join(bets_lst)
	bot.sendMessage(chat_id=chat_id, text=user_bets_msg)
	return SUCCESS_RESPONSE

def place_bet(query, chat_id, message_id, match_id, home_code, away_code, home_bet, away_bet):
	bot = telegram.Bot(TOKEN)
	frm = query.message.chat
	user_name = frm.username
	user_id = frm.id
	matches_conn = sqlite3.connect('groupStage.db')
	group_crsr = matches_conn.cursor()
	group_crsr.execute(SELECT_FUTURE_MATCH, (match_id,))
	if group_crsr.fetchone() is None:
		bot.editMessageText(chat_id=chat_id, message_id=message_id, text=MATCH_ALREADY_STARTED.format(home_code, away_code))
		return SUCCESS_RESPONSE
	conn = sqlite3.connect('bets.db')
	crsr = conn.cursor()
	crsr.execute(SELECT_USER_MATCH_BETS, (user_id, match_id))
	if len(crsr.fetchall()) > 0:
		crsr.execute(EDIT_BET, (home_bet, away_bet, user_id, match_id))
	else:
		crsr.execute(INSERT_INTO_BETS, (user_id, user_name, match_id, int(home_bet), int(away_bet)))
		crsr.execute("SELECT * FROM bets WHERE matchId=?", (match_id,))
		if len(crsr.fetchall()) == 1:
			# first bet on this match - alert everyone
			conn1 = sqlite3.connect('groupUsers.db')
			crsr1 = conn1.cursor()
			crsr1.execute("SELECT * FROM groupUsers WHERE userId=?", (user_id,))
			for user_id, username, group_id in crsr1.fetchall():
				bot.sendMessage(chat_id=group_id, text='@{} has placed a bet on {} vs. {}!'.format(user_name, home_code, away_code))
	conn.commit()
	conn.close()
	bot.editMessageText(chat_id=chat_id, message_id=message_id, text=CONFIRM_BET.format(home_code, away_code))
	return SUCCESS_RESPONSE

def initial_bet_dialog(chat_id, message_id, match_id, home_code, away_code):
	buttons = bet_dialog(match_id, home_code, away_code)
	bot = telegram.Bot(TOKEN)
	bot.editMessageText(text=DECIDE_MATCH_SCORE.format(home_code, away_code), chat_id=chat_id, message_id=message_id, reply_markup=buttons)
	return SUCCESS_RESPONSE

def advanced_bet_dialog(chat_id, message_id, match_id, home_code, away_code, home_bet=None, away_bet=None):
	buttons = bet_dialog(match_id, home_code, away_code, home_bet, away_bet)
	bot = telegram.Bot(TOKEN)
	bot.editMessageReplyMarkup(chat_id=chat_id, message_id=message_id, reply_markup=buttons)
	return SUCCESS_RESPONSE

def bet_dialog(match_id, home_code, away_code, home_bet=None, away_bet=None):
	home_bet_buttons = build_bet_buttons(match_id, PREFIX_HOME_BET, home_code, away_code, home_bet, away_bet)
	away_bet_buttons = build_bet_buttons(match_id, PREFIX_AWAY_BET, home_code, away_code, away_bet, home_bet)
	raw_union_buttons = [[home_bet_buttons[i], away_bet_buttons[i]] for i in range(0, len(home_bet_buttons))]
	raw_union_buttons.insert(0, [create_back_button()])
	return telegram.InlineKeyboardMarkup(raw_union_buttons)

def build_bet_buttons(match_id, curr_bet_prefix, home_code, away_code, bet_str, opposed_bet):
	if opposed_bet is None:
		buttons = [telegram.InlineKeyboardButton(num, callback_data=curr_bet_prefix + CALLBACK_MATCH_SEPARATOR.join((match_id, home_code, away_code, str(num)))) for num in range(0, MAX_GOALS_BET_AMOUNT)]
	else:
		buttons = [telegram.InlineKeyboardButton(num, callback_data=curr_bet_prefix + CALLBACK_MATCH_SEPARATOR.join((match_id, home_code, away_code, opposed_bet, str(num)))) for num in range(0, MAX_GOALS_BET_AMOUNT)]
	if bet_str is not None:
		bet_val = int(bet_str)
		btn_text = buttons[bet_val].text
		buttons[bet_val].text = emoji.emojize(UNICODE_DIGITS[bet_val], use_aliases=True)
	return buttons

def get_matches(chat_id, user_id, edit_mode=False, message_id=None):
	bot = telegram.Bot(TOKEN)
	conn = sqlite3.connect('groupStage.db', detect_types=sqlite3.PARSE_DECLTYPES)
	crsr = conn.cursor()
	crsr.execute(SELECT_MATCHES.format(MAX_UPCOMING_MATCHES))
	bets_conn = sqlite3.connect('bets.db', detect_types=sqlite3.PARSE_DECLTYPES)
	bets_crsr = bets_conn.cursor()
	t = (user_id,)
	bets_crsr.execute(SELECT_USER_BETS, t)
	user_bets = [bet[BET_DB_INDEX_MATCH_ID] for bet in bets_crsr.fetchall()] # match id of matches that user has already placed a bet on
	rows = []
	for row in crsr.fetchall():
		match_id = row[DB_INDEX_MATCH_ID]
		if match_id in user_bets:
			sign = emoji.emojize(UNICODE_CHECK_MARK, use_aliases=True)
		else:
			sign = emoji.emojize(UNICODE_QUESTION_MARK, use_aliases=True)
		home_flag = emoji.emojize(row[DB_INDEX_HOME_UNICODE], use_aliases=True)
		home_team_name = row[DB_INDEX_HOME_TEAM]
		away_team_name = row[DB_INDEX_AWAY_TEAM]
		away_flag = emoji.emojize(row[DB_INDEX_AWAY_UNICODE], use_aliases=True)
		starting_at = get_effective_match_day(row[DB_INDEX_MATCH_START])
		btn_txt = BTN_MATCH.format(sign, home_flag, home_team_name, away_team_name, away_flag, starting_at)
		rows.append((btn_txt, str(match_id), home_team_name, away_team_name))
	match_buttons = []
	for row in rows:
		match_buttons.append([telegram.InlineKeyboardButton(row[0], callback_data=PREFIX_CHOSEN_MATCH + CALLBACK_MATCH_SEPARATOR.join(row[1:]))])
	keyboard = telegram.InlineKeyboardMarkup(match_buttons)
	if edit_mode:
		bot.editMessageText(chat_id=chat_id, message_id=message_id, text=CHOOSE_MATCH, reply_markup=keyboard)
	else:
		bot.sendMessage(chat_id=chat_id, text=CHOOSE_MATCH, reply_markup=keyboard)
	return SUCCESS_RESPONSE

def get_effective_match_day(dt):
	immediate_template = '{} {}:{}'
	padded_minute = '0' + str(dt.minute) if dt.minute < 10 else dt.minute
	padded_hour = '0' + str(dt.hour) if dt.hour < 10 else dt.hour
	d = dt.date()
	today = datetime.now().date()
	if today == d:
		return immediate_template.format('Today', padded_hour, padded_minute)
	if today + dtime.timedelta(days=1) == d:
		return immediate_template.format('Tomorrow', padded_hour, padded_minute)
	future_template = '{} {}/{} {}:{}'
	wd = calendar.day_name[d.weekday()]
	return future_template.format(wd[:3], dt.day, dt.month, padded_hour, padded_minute)

@route('/buildTeamsDB')
def buildTeamsDB():
	conn = sqlite3.connect('teams.db')
	crsr = conn.cursor()
	crsr.execute('''CREATE TABLE teams (id integer, name text, fifaCode text, emojiString text)''')
	r = requests.get('https://raw.githubusercontent.com/lsv/fifa-worldcup-2018/master/data.json').json()
	teams_json = r['teams']
	teams_objects = [(team['id'], team['name'], team['fifaCode'], team['emojiString']) for team in teams_json]
	crsr.executemany('INSERT INTO teams VALUES (?,?,?,?)', teams_objects)
	conn.commit()
	conn.close()
	return 'success!'

@route('/buildGroupStageDB')
def buildGroupStageDB():
	conn = sqlite3.connect('groupStage.db')
	crsr = conn.cursor()
	crsr.execute(CREATE_GROUPSTAGE_TABLE)
	r = requests.get('https://raw.githubusercontent.com/lsv/fifa-worldcup-2018/master/data.json').json()
	groups_json = r['groups']
	teams_json = r['teams']
	team_fifa_dict = {}
	teams_dict = {}
	for team in teams_json:
		teams_dict[int(team['id'])] = team['name']
		team_fifa_dict[int(team['id'])] = team['fifaCode']
	resiko = []
	cnt = 0
	for group, val in groups_json.items():
		for match in val['matches']:
			home_name = teams_dict[int(match['home_team'])]
			key_home_name = ':flag_for_{}:'.format(home_name.replace(' ', '_'))
			#home_unicode = emoji_dict[key_home_name] if key_home_name in emoji_dict else ''
			away_name = teams_dict[int(match['away_team'])]
			key_away_name = ':flag_for_{}:'.format(away_name.replace(' ', '_'))
			#away_unicode = emoji_dict[key_away_name] if key_away_name in emoji_dict else ''
			home_fifa_code = team_fifa_dict[int(match['home_team'])]
			away_fifa_code = team_fifa_dict[int(match['away_team'])]
			resiko.append((cnt, val['name'], home_fifa_code, away_fifa_code, datetime.strptime(match['date'][:-6], '%Y-%m-%dT%H:%M:%S'), key_home_name, key_away_name))
			cnt += 1	
	crsr.executemany(INSERT_INTO_GROUPSTAGE, resiko)
	conn.commit()
	conn.close()
	return 'success!'

@route('/buildBetsDB')
def buildBetsDB():
	conn = sqlite3.connect('bets.db')
	crsr = conn.cursor()
	crsr.execute(CREATE_BETS_TABLE)
	conn.commit()
	conn.close()

@route('/buildAuthorizedGroupsDB')
def buildAuthorizedGroupsDB():
	conn = sqlite3.connect('authorizedGroups.db')
	crsr = conn.cursor()
	crsr.execute(CREATE_AUTHORIZED_GROUPS_TABLE)
	conn.commit()
	conn.close()

@route('/buildGroupUsersDB')
def buildGroupUsersDB():
	conn = sqlite3.connect('groupUsers.db')
	crsr = conn.cursor()
	crsr.execute(CREATE_GROUP_USERS_TABLE)
	conn.commit()
	conn.close()

@route('/buildUserScoreDB')
def buildUserScoreDB():
	conn = sqlite3.connect('userScore.db')
	crsr = conn.cursor()
	crsr.execute(CREATE_USER_SCORE_TABLE)
	conn.commit()
	conn.close()