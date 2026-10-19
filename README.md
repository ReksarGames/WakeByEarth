# WakeByEarth

Wake your PC from anywhere via Telegram using a MikroTik router. The router polls the
Telegram Bot API and sends a Wake-on-LAN packet when you send `turnon`.
No separate bot server or inbound port forwarding is required.

```text
Telegram → MikroTik RouterOS → Wake-on-LAN → Computer
```

## Commands

Send these messages in a private chat with your bot, without a leading `/`:

| Message | Action |
| --- | --- |
| `turnon` | Send a Wake-on-LAN packet to the configured MAC address. |
| `status` | Report that the computer's IP address is not configured. |
| `internet` | Report how many of five pings to `8.8.8.8` received replies. |

Only the configured Telegram user is allowed to send commands, and only in
their private chat. Sender IDs embedded in replies or forwarded messages do not
grant access.

## Requirements

- A MikroTik router with RouterOS v6 or later and outbound internet access.
- A computer connected by Ethernet with Wake-on-LAN enabled in its firmware
  and network adapter settings.
- A Telegram bot token, your numeric Telegram user ID, the computer's MAC
  address, and the router interface connected to that computer.

## Setup

1. Create a bot through `@BotFather` and obtain your user ID from a private
   message to the bot.
2. Copy [`MikroTik-ready/install.rsc`](MikroTik-ready/install.rsc) to
   `MikroTik-ready/install.local.rsc`. Replace the token, Telegram ID, MAC
   address and interface in this local copy.
3. Upload `install.local.rsc` to the router's **Files** and run
   `/import file-name=install.local.rsc` in **New Terminal**. This creates the
   `WakeByEarth` script and a scheduler that runs it every minute.
4. Delete the uploaded file from the router's **Files** after installation.
5. Send `turnon` to the bot. A successful reply confirms that the packet was sent.

See [install.md](install.md) for the full procedure. The script does not require
the computer's IP address; `status` currently reports that it is not configured.

## Privacy and security

Public templates contain placeholders. Keep configured copies as `*.local.rsc`
files, which are excluded by `.gitignore`. Do not put credentials into tracked
templates or commit router exports, backups, or Telegram API responses.

Keep your bot token private. If it has been exposed, revoke it through
`@BotFather`; deleting a file does not remove it from Git history.
The current RouterOS fetch commands do not enable HTTPS certificate validation.

WakeByEarth only controls wake-up and connectivity checks. Remote desktop or
game streaming needs a separate setup, such as Tailscale with Sunshine and
Moonlight.

## Tests

Python 3 generates offline RouterOS authorization tests from the actual script:

```sh
python3 tests/routeros_auth.py > auth-test.rsc
```

Import the generated file into a disposable RouterOS instance. All 40 cases
should print `PASS`; these tests make no network or Wake-on-LAN calls.

[`tests/routeros_ready.py`](tests/routeros_ready.py) also generates an integration
test for the installer variant. See [install.md](install.md#tests) for its setup.
Both generators use synthetic Telegram IDs and require no bot credentials.

## License

[MIT](LICENSE). The original copyright notice is preserved.
