# Vein — All-in-One Discord Bot

A powerful, modular Discord bot with moderation, economy, leveling, giveaways, AI, music, tickets, and more.

---

## Quick Start

### 1. Install Python 3.10+

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Set up your environment
```bash
cp .env.example .env
```
Edit `.env` and fill in your values:
- `TOKEN` — Your bot token from the Discord Developer Portal
- `OPENAI_KEY` — Your OpenAI API key (required for AI @mention feature)

### 4. Run the bot
```bash
python main.py
```

---

## File Structure
```
vein-bot/
├── main.py
├── requirements.txt
├── .env.example
├── config.json          (auto-created)
├── database.json        (auto-created)
└── cogs/
    ├── ai.py
    ├── antinuke.py
    ├── economy.py
    ├── filter.py
    ├── fun.py
    ├── giveaway.py
    ├── leveling.py
    ├── mod_logging.py
    ├── moderation.py
    ├── music.py
    ├── suggestions.py
    ├── tickets.py
    ├── utility.py
    └── welcome.py
```

---

## Features

| Module | Commands |
|--------|----------|
| 🛡️ Moderation | ban, unban, kick, timeout, warn, purge (up to 10,000), snipe, editsnipe, lock, unlock, slowmode, nick |
| 🔒 Anti-Nuke | Auto-detects mass bans/channel/role deletions; whitelist system |
| 📊 Leveling | XP per message, rank cards, leaderboard, role rewards, multipliers |
| 💰 Economy | Balance, daily (streaks), work, gamble, bank, shop, inventory, transfer |
| 🎵 Music | play, pause, skip, queue, loop, shuffle, volume (requires Lavalink) |
| 🎉 Giveaways | gstart, gend, greroll, glist — reaction-based with time parsing |
| 🎫 Tickets | Button-based tickets, transcripts, staff roles, categories |
| 🤖 AI | @mention the bot to chat — ban/whitelist system, full bot knowledge |
| 📝 Logging | Messages, members, voice, channels, roles — all logged |
| 👋 Welcome | Custom welcome/leave messages, auto-role |
| 🚫 Filter | Spam, links, invites, caps, custom word blacklist |
| 💡 Suggestions | Submit, approve, deny — with DM notifications |
| 🎮 Fun | 8ball, dice, rps, meme, joke, poll, avatar, and more |
| 🔧 Utility | ping, serverinfo, userinfo, roleinfo, botinfo, uptime |

---

## AI Setup

The AI is triggered by **@mentioning** the bot. There are no commands needed.

```
@Vein what commands do you have?
@Vein how do I set up tickets?
```

### AI Management
- **Server owner** and user `1102734526670708737` always have full management access
- `.whitelistai @user` — Add a user as an AI manager
- `.banai @user` — Ban a user from using AI
- `.aimanagers` — View current managers
- `.aibanned` — View banned users

---

## Giveaway Usage

```
.gstart 1h 1 Discord Nitro
.gstart 30m 2 Custom Role
.gstart 1d12h 1 Steam Gift Card
```

Time format: `1d` `2h` `30m` `10s` or combinations like `1h30m`

---

## Music Setup (Optional)

Music requires Lavalink. If you don't need music, skip this.

1. Download Lavalink.jar from https://github.com/lavalink-devs/Lavalink/releases
2. Create `application.yml`:
```yaml
server:
  port: 2333
  address: 0.0.0.0
lavalink:
  server:
    password: "youshallnotpass"
    sources:
      youtube: true
      soundcloud: true
      http: true
```
3. Run `java -jar Lavalink.jar`
4. Uncomment `wavelink>=3.0.0` in `requirements.txt` and run `pip install wavelink>=3.0.0`

---

## Discord Developer Portal Setup

1. Go to https://discord.com/developers/applications
2. Create an application → Bot
3. Enable all three **Privileged Gateway Intents**:
   - Presence Intent
   - Server Members Intent
   - Message Content Intent
4. Copy token → paste into `.env`
5. Invite with **Administrator** permission

---

## First-Time Server Setup

After inviting the bot, run these commands to configure everything:

```
.logs #mod-logs           — Enable audit logging
.setwelcome #welcome      — Set the welcome channel
.setautorole @Member      — Auto-assign a role to new members
.ticketpanel              — Post the ticket creation button
.suggestchannel #suggest  — Set the suggestions channel
.antinuke true            — Enable anti-nuke protection
```

---

## Hosting on fps.ms

1. Upload all files maintaining the folder structure above
2. Create your `.env` file with your TOKEN and OPENAI_KEY
3. Set the startup command to: `python main.py`
4. Install dependencies: `pip install -r requirements.txt`
