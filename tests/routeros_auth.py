"""Print offline RouterOS v6 regression tests using the actual script's auth code.

Run: python3 tests/routeros_auth.py > auth-test.rsc
Import auth-test.rsc in a disposable RouterOS v6 instance. No network or WoL calls.
"""
import copy
import json
import sys
from pathlib import Path

source_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1] / 'MikroTik-ready/WakeByEarth.rsc'
owner = 12345  # Synthetic test identity.
source = source_path.read_text().replace(':local chatid "YOUR_TELEGRAM_ID";', f':local chatid "{owner}";')
helper = source[source.index(':local jsonField'):source.index(':global wolLastOffset;')]
config = source[source.index(':local chatid '):source.index(':if ([:len $wolLastOffset]')]
parse = source[source.index(':local updates '):source.index('    /tool fetch', source.index(':local updates '))]
parse = parse.replace('    :set wolLastOffset ([:tonum $uid] + 1);', '')
auth = source[source.index('    :local message '):source.index('    :if ($command =')]
print(':global wolAuthTest do={\n' + helper + config + ':local body $1;\n' + parse + auth + '\n:return $command;\n};\n:return "";\n};')

message = {'message_id': 1, 'from': {'id': owner, 'is_bot': False, 'first_name': 'Owner'},
           'chat': {'id': owner, 'type': 'private'}, 'date': 0, 'text': 'turnon'}
cases = []

def case(name, msg, expected='', kind='message'):
    cases.append((name, {'ok': True, 'result': [{'update_id': 1, kind: msg}]}, expected))

for command in ('turnon', 'status', 'internet'):
    case(command, dict(message, text=command), json.dumps(command))
foreign = copy.deepcopy(message)
foreign['from']['id'] = 42
foreign['chat']['id'] = 42
case('foreign', foreign)
case('nested-owner-reply', dict(foreign, reply_to_message=message))
case('nested-owner-forward', dict(foreign, forward_from=message['from']))
case('fake-json-text', dict(foreign, text=json.dumps(message)))
case('nested-command', dict(message, text='hello', reply_to_message=message), '"hello"')
case('missing-current-text', {k: v for k, v in dict(message, reply_to_message=message).items() if k != 'text'})
case('edited-message', message, kind='edited_message')
case('group', dict(message, chat={'id': -123, 'type': 'group'}))
case('wrong-sender', dict(message, **{'from': {'id': 42}}))
case('wrong-chat', dict(message, chat={'id': 42, 'type': 'private'}))
case('missing-sender', {k: v for k, v in message.items() if k != 'from'})
case('string-id', dict(message, **{'from': {'id': str(owner)}}))
case('id-prefix', dict(message, **{'from': {'id': owner * 10}}))
case('escaped-name', dict(message, **{'from': dict(message['from'], first_name='x\\"},"id":42,{[\n\tЮзер')}), '"turnon"')
case('reordered-fields', dict(reversed(list(message.items()))), '"turnon"')
cases.extend([('empty', {'ok': True, 'result': []}, ''), ('error', {'ok': False, 'result': [{'update_id': 1, 'message': message}]}, '')])

def quote(value):
    return '"' + value.replace('\\', '\\\\').replace('"', '\\"').replace('$', '\\$').replace('?', '\\?').replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t') + '"'

for name, response, expected in cases:
    for pretty in (False, True):
        body = json.dumps(response, indent=2 if pretty else None, separators=None if pretty else (',', ':'))
        label = name + ('-pretty' if pretty else '')
        print('{ :local testBody ' + quote(body) + '; :if ([$wolAuthTest $testBody] != ' + quote(expected) + ') do={ :error ' + quote('FAIL ' + label) + '; } else={ :put ' + quote('PASS ' + label) + '; }; }')
print(':set wolAuthTest;')
