import os
import json
import requests
from flask import Flask, request

app = Flask(__name__)
app.config['DEBUG'] = True

SLACK_HISTORY_TOKEN = os.environ.get('SLACK_HISTORY_TOKEN', None)
SLACK_CHANNEL_HISTORY_URL = 'https://slack.com/api/channels.history'
SLACK_USER_INFO_URL = 'https://slack.com/api/users.info'
SLACK_OUTGOING_WEBHOOK_TOKEN = os.environ.get('SLACK_OUTGOING_WEBHOOK_TOKEN', None)
SLACK_INCOMING_WEBHOOK_URL = os.environ['SLACK_INCOMING_WEBHOOK_URL']

@app.route('/webhook', methods=['POST'])
def webhook():
    token = request.form.get('token')
    if not SLACK_OUTGOING_WEBHOOK_TOKEN or token == SLACK_OUTGOING_WEBHOOK_TOKEN:
        shamer = '@%s' % request.form.get('user_name')
        shamee = request.form.get('text')
        if not shamee and SLACK_HISTORY_TOKEN:
            params = {
                'token': SLACK_HISTORY_TOKEN,
                'channel': request.form.get('channel_id')
            }
            try:
                response = requests.get(SLACK_CHANNEL_HISTORY_URL, params=params)
                data = json.loads(response.content)
                for message in data['messages']:
                    if message['type'] == 'message' and ('<!everyone>' in message['text'] or '<!channel>' in message['text']):
                        response = requests.get(SLACK_USER_INFO_URL, params={'token': SLACK_HISTORY_TOKEN, 'user': message['user']})
                        data = json.loads(response.content)
                        if 'ok' in data and data['ok'] == True:
                            shamee = '@%s' % data['user']['name']
                            break
            except Exception, e:
                return 'Oops! There was a problem finding last @channel or @everyone mention: %s' % str(e)
        elif SLACK_HISTORY_TOKEN:
            return 'Could not find last @everyone or @channel mention :\'('

        if not shamee.startswith('@'):
            return 'Please enter a valid username to shame'

        text = '%s shamed %s' % (shamer, shamee) if shamer != shamee else '%s shamed themself' % shamer
        params = {
                'username': 'shamebot',
                'icon_emoji': ':bell:',
                'text': text,
                'channel': '#%s' % request.form.get('channel_name')
        }

        try:
            requests.post(SLACK_INCOMING_WEBHOOK_URL, data=json.dumps(params))
            params['channel'] = shamee
            params['text'] = 'SHAME'
            for i in range(3):
                requests.post(SLACK_INCOMING_WEBHOOK_URL, data=json.dumps(params))
        except Exception, e:
            return 'Oops! Something went wrong: %s' % str(e)
    return ''

