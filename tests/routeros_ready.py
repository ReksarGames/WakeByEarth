"""Generate an offline integration test for the READY script on disposable RouterOS 6.

python3 tests/routeros_ready.py > ready-test.rsc
Import after install.rsc in a VM with a test bridge named bridge.
This replaces the installed script's HTTP I/O and ping destination, then runs
real command dispatch, WoL and Scheduler. NEVER run this on the real router.
"""
import json
import re
from pathlib import Path

root = Path(__file__).resolve().parents[1]
source = (root / 'MikroTik-ready/WakeByEarth.rsc').read_text()
installer = (root / 'MikroTik-ready/install.rsc').read_text()
scheduler = (root / 'MikroTik-ready/scheduler.rsc').read_text()
assert 'source={\n' + source + '}\n' + scheduler in installer
assert 'policy=ftp,read,write,test' in installer and 'policy=ftp,read,write,test' in scheduler
assert not re.search(r'/ping[^\n]*as-value', source)
owner = 12345  # Synthetic test identity.
source = source.replace(':local chatid "YOUR_TELEGRAM_ID";', f':local chatid "{owner}";')
source = source.replace('XX:XX:XX:XX:XX:XX', '02:00:00:00:00:01')
source = re.sub(r':local token "[^"]+";', ':local token "TEST";', source)
source = source.replace(':local result [/tool fetch url=$url as-value output=user];\n:local body ($result->"data");', ':local body $wolTestBody;')
source, replaced = re.subn(r'/tool fetch \\\n\s*url=(.*?) \\\n\s*keep-result=no;', r':set wolTestRequests ($wolTestRequests, \1);', source)
assert replaced == 4, replaced
# Real ping, deterministic loopback destination. No requests to Telegram.
source = source.replace('/ping 8.8.8.8 count=5', '/ping 127.0.0.1 count=5')
assert '/tool fetch' not in source
print('/system scheduler disable WakeByEarth')
print('/system script set WakeByEarth source={\n:global wolTestBody;\n:global wolTestRequests;\n' + source + '}')
print(':global wolTestBody; :global wolTestRequests; :global wolLastOffset;')

def quote(s):
    return '"' + s.replace('\\', '\\\\').replace('"', '\\"').replace('$', '\\$').replace('?', '\\?') + '"'

def fixture(text, sender=owner):
    return json.dumps({'ok': True, 'result': [{'update_id': 100, 'message': {'from': {'id': sender}, 'chat': {'id': sender, 'type': 'private'}, 'text': text}}]}, separators=(',', ':'))

for name, sender, expected, text in [
    ('turnon', owner, 2, 'Wake-on-LAN%20packet%20sent%20successfully.'),
    ('status', owner, 2, 'Computer%20IP%20is%20not%20configured.'),
    ('internet', owner, 2, 'Internet%20check:%205%20of%205%20ping%20replies.'),
    ('turnon', 42, 1, ''),
]:
    label = name + '-' + str(sender)
    print(':set wolTestBody ' + quote(fixture(name, sender)) + '; :set wolTestRequests [:toarray ""];')
    print('/system script run WakeByEarth')
    print(':if (([:len $wolTestRequests] != ' + str(expected) + ') || ($wolLastOffset != 101)) do={ :error "FAIL ' + label + '"; };')
    if text:
        print(':if ([:pick ($wolTestRequests->1) ([:len ($wolTestRequests->1)] - ' + str(len(text)) + ') [:len ($wolTestRequests->1)]] != ' + quote(text) + ') do={ :error "FAIL reply ' + label + '"; };')
    print(':put "PASS ' + label + '";')
# Scheduler executes in its own environment; put the fixture inside its source.
scheduled = ':local wolTestBody ' + quote(fixture('noop')) + ';\n:global wolTestRequests; :set wolTestRequests [:toarray ""];\n' + source
scheduled += '\n:if ([:len $wolTestRequests] != 1) do={ :error "FAIL scheduler ack"; };\n:log info "WOL_SCHEDULER_PASS";\n'
print('/system script set WakeByEarth source={\n' + scheduled + '}')
print('/system scheduler set WakeByEarth interval=1s disabled=no')
print(':delay 4s; /system scheduler disable WakeByEarth')
print(':if ([:len [/log find where message="WOL_SCHEDULER_PASS"]] = 0) do={ :error "FAIL scheduler"; };')
print(':put "PASS scheduler";')
