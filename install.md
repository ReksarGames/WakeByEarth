# Installation

## 1. Prepare the computer and bot

Enable Wake-on-LAN in the computer's BIOS/UEFI and Ethernet adapter settings.
Record its MAC address. The computer must remain connected to Ethernet and
standby power. Its IP address is not required.

Create a Telegram bot with `@BotFather` using `/newbot`, then send a private
message to the new bot. Request the following URL locally, substituting your
token:

```text
https://api.telegram.org/botYOUR_BOT_TOKEN/getUpdates
```

Use `result[].message.from.id` as `YOUR_TELEGRAM_ID`. In the same message,
`message.chat.type` must be `private` and `message.chat.id` must equal that user
ID. Group and channel IDs will not work. Keep the token and API response private.

## 2. Configure a local copy

```sh
cp MikroTik-ready/install.rsc MikroTik-ready/install.local.rsc
```

Edit only the local copy:

| Template value | Replace with |
| --- | --- |
| `YOUR_BOT_TOKEN` | The token issued by BotFather. |
| `YOUR_TELEGRAM_ID` | Your numeric user ID, keeping the surrounding quotes. |
| `XX:XX:XX:XX:XX:XX` | The computer's Ethernet MAC address. |
| `interface=bridge` | Set the interface connected to the computer's LAN if its name differs. |

## 3. Install the script and scheduler

If upgrading from WakeOnEarth, disable its scheduler before installing WakeByEarth.

Upload `install.local.rsc` to the router's **Files**, then run this in
**New Terminal**:

```routeros
/import file-name=install.local.rsc
```

The installer creates both the script and scheduler. It stops before making
changes if either name already exists. Do not also import `scheduler.rsc`.
If the file was uploaded under `flash/`, use
`file-name=flash/install.local.rsc` instead.
After a successful installation, delete the uploaded file from the router's
**Files**; the saved script already contains its configuration and credentials.

Send `turnon` and `internet` in your private chat with the bot. Allow for the
one-minute polling interval and the computer's boot time. `status` currently
reports that the computer's IP is not configured; it does not check connectivity.

`MikroTik-ready/WakeByEarth.rsc` contains the same script source as the installer
for integration tests and manual installation. For manual installation, configure
a local copy and paste it into **System → Scripts → WakeByEarth → Source** with
policies `ftp,read,write,test`, then import `scheduler.rsc` once. If modifying the
script's logic, update the embedded source in `install.rsc` too.

## Tests

Generate the 40 authorization cases from `MikroTik-ready/WakeByEarth.rsc`:

```sh
python3 tests/routeros_auth.py > auth-test.rsc
```

Import `auth-test.rsc` into a disposable RouterOS
instance and check for 40 `PASS` lines.

The integration test uses synthetic credentials, replaces Telegram HTTP calls
with fixtures, and sends internet-check pings to loopback. In a disposable
RouterOS instance, create a test bridge named `bridge` and import the unmodified
public `MikroTik-ready/install.rsc` template. Then generate and import:

```sh
python3 tests/routeros_ready.py > ready-test.rsc
```

Expect five `PASS` lines, including the scheduler check. This test replaces the
installed script, sends a Wake-on-LAN packet on the test bridge and changes the
scheduler. Run it only in a disposable instance.
