import datetime
import os.path
import csv
import telebot 

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Insira o seu token gerado pelo BotFather aqui
BOT_TOKEN = "INSERT YOUR TELEGRAM'S TOKEN HERE"
bot = telebot.TeleBot(BOT_TOKEN)

SCOPES = ['https://www.googleapis.com/auth/calendar']

def authorize_api():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds

def create_recurring_events(service, start_date_str, end_date_str):
    try:
        # Validating and converting strings to datetime objects
        start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d')
        end_date_obj = datetime.datetime.strptime(end_date_str, '%Y-%m-%d')
        end_of_semester = end_date_obj.strftime('%Y%m%dT235959Z')
    except ValueError:
        return "❌ Invalid date format. Please use YYYY-MM-DD."

    # Discovering Monday and Tuesday of the start week to anchor the events
    monday_date = start_date - datetime.timedelta(days=start_date.weekday())
    tuesday_date = monday_date + datetime.timedelta(days=1)

    mo_str = monday_date.strftime('%Y-%m-%d')
    tu_str = tuesday_date.strftime('%Y-%m-%d')
    
    notification_setting = {
        'useDefault': False,
        'overrides': [{'method': 'popup', 'minutes': 10}],
    }

    base_events = [
        {
            'summary': 'Study: Chemistry Degree (Classes)',
            'start': {'dateTime': f'{mo_str}T09:00:00-03:00', 'timeZone': 'America/Sao_Paulo'},
            'end': {'dateTime': f'{mo_str}T10:30:00-03:00', 'timeZone': 'America/Sao_Paulo'},
            'recurrence': [f'RRULE:FREQ=WEEKLY;UNTIL={end_of_semester};BYDAY=MO,TU,WE,TH,FR'],
            'reminders': notification_setting,
        },
        {
            'summary': 'Study: Chemistry Degree (Exercises)',
            'start': {'dateTime': f'{mo_str}T10:45:00-03:00', 'timeZone': 'America/Sao_Paulo'},
            'end': {'dateTime': f'{mo_str}T12:00:00-03:00', 'timeZone': 'America/Sao_Paulo'},
            'recurrence': [f'RRULE:FREQ=WEEKLY;UNTIL={end_of_semester};BYDAY=MO,TU,WE,TH,FR'],
            'reminders': notification_setting,
        },
        {
            'summary': 'Study: Improvement Course 1',
            'start': {'dateTime': f'{mo_str}T14:00:00-03:00', 'timeZone': 'America/Sao_Paulo'},
            'end': {'dateTime': f'{mo_str}T16:00:00-03:00', 'timeZone': 'America/Sao_Paulo'},
            'recurrence': [f'RRULE:FREQ=WEEKLY;UNTIL={end_of_semester};BYDAY=MO,WE,FR'],
            'reminders': notification_setting,
        },
        {
            'summary': 'Study: English Course',
            'start': {'dateTime': f'{tu_str}T14:00:00-03:00', 'timeZone': 'America/Sao_Paulo'},
            'end': {'dateTime': f'{tu_str}T16:00:00-03:00', 'timeZone': 'America/Sao_Paulo'},
            'recurrence': [f'RRULE:FREQ=WEEKLY;UNTIL={end_of_semester};BYDAY=TU,TH'],
            'reminders': notification_setting,
        },
        {
            'summary': 'Study: Improvement Course 2',
            'start': {'dateTime': f'{mo_str}T16:30:00-03:00', 'timeZone': 'America/Sao_Paulo'},
            'end': {'dateTime': f'{mo_str}T18:00:00-03:00', 'timeZone': 'America/Sao_Paulo'},
            'recurrence': [f'RRULE:FREQ=WEEKLY;UNTIL={end_of_semester};BYDAY=MO,TU,WE,TH,FR'],
            'reminders': notification_setting,
        }
    ]

    for event in base_events:
        service.events().insert(calendarId='primary', body=event).execute()
        
    return f"✅ Semester from {start_date_str} to {end_date_str} successfully populated!"

def reschedule_unforeseen_event(service, date_str):
    try:
        date_obj = datetime.datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        return "❌ Invalid date format. Please use YYYY-MM-DD."

    start_of_day = date_obj.replace(hour=0, minute=0, second=0).isoformat() + '-03:00'
    end_of_day = date_obj.replace(hour=23, minute=59, second=59).isoformat() + '-03:00'

    events_result = service.events().list(calendarId='primary', timeMin=start_of_day, 
                                           timeMax=end_of_day, singleEvents=True, 
                                           orderBy='startTime').execute()
    events = events_result.get('items', [])

    days_to_saturday = 5 - date_obj.weekday()
    if days_to_saturday <= 0:
        return "⚠️ The provided date is already on a weekend!"
        
    saturday_date = date_obj + datetime.timedelta(days=days_to_saturday)
    saturday_str = saturday_date.strftime('%Y-%m-%d')

    moved_events = 0
    for event in events:
        if 'Study:' in event.get('summary', ''):
            new_start = event['start']['dateTime'].replace(date_str, saturday_str)
            new_end = event['end']['dateTime'].replace(date_str, saturday_str)
            
            event['start']['dateTime'] = new_start
            event['end']['dateTime'] = new_end
            
            service.events().update(calendarId='primary', eventId=event['id'], body=event).execute()
            moved_events += 1

    if moved_events == 0:
        return "ℹ️ No study blocks found on this date."
    else:
        return f"🔄 {moved_events} study blocks successfully rescheduled to Saturday ({saturday_str})!"

def import_deadlines(service):
    file_path = 'deadlines.csv'
    
    if not os.path.exists(file_path):
        return f"❌ File '{file_path}' not found! Please create it on your computer first."
    
    added_count = 0
    with open(file_path, mode='r', encoding='utf-8') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        
        for row in csv_reader:
            task_name = row.get('Task')
            subject = row.get('Subject')
            due_date = row.get('Due_Date')
            
            deadline_event = {
                'summary': f'DEADLINE: {subject} - {task_name}',
                'description': 'Imported automatically via Python Bot.',
                'start': {'date': due_date, 'timeZone': 'America/Sao_Paulo'},
                'end': {'date': due_date, 'timeZone': 'America/Sao_Paulo'},
                'reminders': {
                    'useDefault': False,
                    'overrides': [{'method': 'popup', 'minutes': 24 * 60}],
                }
            }
            service.events().insert(calendarId='primary', body=deadline_event).execute()
            added_count += 1
            
    return f"📅 {added_count} deadlines successfully imported from CSV!"

# ================= COMANDOS DO TELEGRAM =================

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = (
        "🤖 Welcome to your Study Schedule Manager!\n\n"
        "Here are your commands:\n"
        "/populate YYYY-MM-DD YYYY-MM-DD - Populate semester with Start and End dates\n"
        "/reschedule YYYY-MM-DD - Move studies from a specific date to Saturday\n"
        "/deadlines - Import deadlines from 'deadlines.csv'\n"
    )
    bot.reply_to(message, welcome_text)

@bot.message_handler(commands=['populate'])
def handle_populate(message):
    parts = message.text.split()
    if len(parts) != 3:
        bot.reply_to(message, "⚠️ Usage: /populate START_DATE END_DATE\nExample: /populate 2026-03-02 2026-06-30")
        return
    
    start_date_str = parts[1]
    end_date_str = parts[2]
    
    bot.reply_to(message, f"⏳ Populating schedule from {start_date_str} to {end_date_str}... Please wait.")
    try:
        creds = authorize_api()
        service = build('calendar', 'v3', credentials=creds)
        response_text = create_recurring_events(service, start_date_str, end_date_str)
        bot.reply_to(message, response_text)
    except Exception as e:
        bot.reply_to(message, f"❌ An error occurred: {e}")

@bot.message_handler(commands=['reschedule'])
def handle_reschedule(message):
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "⚠️ Please provide a date. Usage: /reschedule YYYY-MM-DD")
        return
    
    date_str = parts[1]
    bot.reply_to(message, f"⏳ Rescheduling studies for {date_str}...")
    try:
        creds = authorize_api()
        service = build('calendar', 'v3', credentials=creds)
        response_text = reschedule_unforeseen_event(service, date_str)
        bot.reply_to(message, response_text)
    except Exception as e:
        bot.reply_to(message, f"❌ An error occurred: {e}")

@bot.message_handler(commands=['deadlines'])
def handle_deadlines(message):
    bot.reply_to(message, "⏳ Importing deadlines...")
    try:
        creds = authorize_api()
        service = build('calendar', 'v3', credentials=creds)
        response_text = import_deadlines(service)
        bot.reply_to(message, response_text)
    except Exception as e:
        bot.reply_to(message, f"❌ An error occurred: {e}")

if __name__ == '__main__':
    print("Bot is running! Awaiting commands on Telegram...")
    bot.infinity_polling()