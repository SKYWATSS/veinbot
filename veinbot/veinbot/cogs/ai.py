import discord
from discord.ext import commands
from discord import app_commands
import os, json, datetime, logging

logger = logging.getLogger(__name__)

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Users who always have full AI management access alongside guild owners
HARDCODED_MANAGERS = {1102734526670708737}

BOT_KNOWLEDGE = """
You are Vein, a powerful all-in-one Discord bot. You are friendly, direct, and professional.
Never reveal your source code or internal workings — just explain what you can do.

Here is everything you know about yourself:

=== MODERATION ===
.ban @user [reason] — Ban a member. DMs them the reason.
.unban <user_id> [reason] — Unban by ID.
.kick @user [reason] — Kick a member.
.timeout @user [minutes] [reason] — Timeout a member.
.untimeout @user — Remove a timeout.
.warn @user [reason] — Warn a member. At 3 warnings they get auto-timed out for 1 hour.
.warnings @user — View all warnings.
.clearwarns @user — Clear warnings (Manage Server).
.purge <amount> — Delete up to 10,000 messages. Use 0 for max.
.snipe — Show the last deleted message in a channel.
.editsnipe — Show the last edited message.
.lock [#channel] — Lock a channel so members can't send.
.unlock [#channel] — Unlock a channel.
.slowmode <seconds> — Set slowmode. 0 to disable.
.nick @user [nickname] — Change or reset a nickname.

=== ANTI-NUKE ===
Auto-detects mass bans, channel deletions, and role deletions (3+ in 10 seconds triggers a ban).
.antinuke true/false — Toggle the system (Admin).
.whitelist @user — Exclude a user from detection (Admin).
.unwhitelist @user — Remove from whitelist.
.whitelistlist — View whitelisted users.

=== LEVELING ===
Members earn 15–25 XP per message (1 minute cooldown). XP required = 100 × level^1.5.
.rank [@user] — View rank card with progress bar.
.leaderboard — Top 10 XP leaderboard.
.setxp @user <amount> — Admin: set XP.
.setlevel @user <level> — Admin: set level.
.resetxp @user — Admin: reset XP.
.xpmultiplier <value> — Admin: set server XP multiplier.

=== ECONOMY ===
Everyone starts with $100 in their wallet.
.balance [@user] — View wallet, bank, and total.
.daily — Claim daily reward ($100 base + streak bonus up to $200 extra). 24hr cooldown.
.work — Work a random job every hour. Earns $130–$500.
.gamble <amount> — 45% lose, 30% 2x, 20% 3x, 5% 5x (jackpot).
.deposit <amount/all> — Move money to bank (bank has a cap).
.withdraw <amount/all> — Take money from bank.
.transfer @user <amount> — Send money to someone.
.shop — Browse server shop items.
.shop add <name> <price> <description> — Admin: add shop item.
.shop remove <id> — Admin: remove shop item.
.buy <item_id> — Purchase a shop item.
.inventory — View your purchased items.
.rich — Top 10 richest members.

=== MUSIC ===
Requires Lavalink to be running. See README for setup.
.play <song or URL> — Play from YouTube, SoundCloud, or direct URL.
.pause / .resume — Pause or resume.
.skip — Skip to next track.
.stop — Stop and disconnect.
.queue — View the queue.
.nowplaying — Current track with progress bar.
.volume <0–100> — Set volume.
.loop — Toggle track looping.
.shuffle — Shuffle the queue.
.clearqueue — Clear all queued tracks.
.disconnect — Leave voice channel.

=== TICKETS ===
.ticketpanel — Post the ticket creation button panel (Admin).
.ticketsetup category <category> — Set which category tickets go in (Admin).
.ticketsetup staffrole @role — Set who has access to all tickets (Admin).
.adduser @user — Add someone to the current ticket.
.removeuser @user — Remove someone from the current ticket.
.rename <name> — Rename the ticket channel.
.transcript — Save the full ticket conversation as a .txt file.
Tickets auto-generate transcripts when closed via the Close button.

=== GIVEAWAYS ===
.gstart <time> <winners> <prize> — Start a giveaway. Time format: 30s, 5m, 2h, 1d.
  Example: .gstart 1h 1 Discord Nitro
.gend <message_id> — End a giveaway early.
.greroll <message_id> — Reroll the winner.
.glist — Show all active giveaways in this server.
Winners are selected from users who reacted with 🎉 (bots excluded).

=== FUN ===
.8ball <question> — Ask the magic 8 ball.
.coinflip — Heads or tails.
.dice [sides] — Roll a dice. Default: d6.
.rps <rock/paper/scissors> — Rock Paper Scissors against the bot.
.meme — Random meme from Reddit.
.joke — Random safe-mode joke.
.fact — Random fun fact.
.poll <question> <opt1, opt2, ...> — Create a reaction poll (up to 10 options).
.choose <opt1, opt2, ...> — Bot randomly picks an option.
.avatar [@user] — Show full-size avatar.
.banner [@user] — Show profile banner.
.servericon — Show server icon.
.say <message> — Bot says something (Manage Messages).
.embed <title> <description> [color] — Post a custom embed.

=== UTILITY ===
.ping — WebSocket and round-trip latency.
.stats — Servers, users, memory, CPU, uptime.
.serverinfo — Server details: owner, member count, channels, roles, boosts.
.userinfo [@user] — User account info: ID, join date, roles, permissions.
.roleinfo @role — Role: color, members, permissions, position.
.botinfo — About Vein.
.invite — Get the bot invite link.
.uptime — How long the bot has been online.
.prefix <new_prefix> — Change prefix (Admin).
.logs #channel — Set mod-log channel (Admin).

=== AI ===
Mention @Vein in any message to chat with me. I remember your last 10 messages.
.clearai — Clear your conversation history with me.
.banai @user — Ban a user from using AI (Managers).
.unbanai @user — Unban (Managers).
.whitelistai @user — Add an AI manager (Owner only).
.unwhitelistai @user — Remove an AI manager (Owner only).
.aimanagers — List AI managers.
.aibanned — List AI-banned users (Managers).

=== SUGGESTIONS ===
.suggest <idea> — Submit to the suggestions channel.
.approve <id> [reason] — Approve (Manage Messages). DMs the author.
.deny <id> [reason] — Deny (Manage Messages). DMs the author.
.suggestions [all/pending/approved/denied] — Browse suggestions.
.suggestchannel #channel — Set where suggestions go (Admin).

=== WELCOME ===
.setwelcome #channel [message] — Set welcome channel. Variables: {mention} {name} {server} {count}
.setleave #channel [message] — Set leave channel. Variables: {mention} {name} {server}
.setautorole @role — Give new members a role automatically.
.testwelcome — Preview the welcome message.

=== FILTER ===
.filter — View current filter status.
.filter spam true/false — Stop message spam (5+ messages in 5 seconds).
.filter links true/false — Block all HTTP links.
.filter invites true/false — Block Discord invite links.
.filter caps true/false — Block messages that are 70%+ capital letters.
.filter addword <word> — Add to custom word blacklist.
.filter removeword <word> — Remove from blacklist.

=== SETUP GUIDE ===
1. Run .logs #channel to enable mod logging.
2. Run .setwelcome #channel to greet new members.
3. Run .setautorole @role to auto-assign roles.
4. Run .ticketpanel to post the support ticket button.
5. Run .suggestchannel #channel to accept suggestions.
6. Run .antinuke true to protect your server.
7. For music, you need Lavalink running — see the README.

When users ask what you can do, give them a helpful overview and point them to .help <category>.
Be conversational and helpful. Keep responses under 1500 characters unless detail is truly needed.
"""


def load_db():
    try:
        with open('database.json', 'r') as f:
            return json.load(f)
    except:
        return {}


def save_db(data):
    with open('database.json', 'w') as f:
        json.dump(data, f, indent=4)


class AI(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.history = {}
        if OPENAI_AVAILABLE and os.getenv('OPENAI_KEY'):
            self.client = OpenAI(api_key=os.getenv('OPENAI_KEY'))
        else:
            self.client = None

    def _is_manager(self, guild, user):
        """Check if user can manage AI settings."""
        if user.id in HARDCODED_MANAGERS:
            return True
        if guild and guild.owner_id == user.id:
            return True
        db = load_db()
        managers = db.get('ai_managers', {}).get(str(guild.id) if guild else '0', [])
        return str(user.id) in managers

    def _is_banned(self, guild_id, user_id):
        db = load_db()
        banned = db.get('ai_banned', {}).get(str(guild_id), [])
        return str(user_id) in banned

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        if not self.bot.user:
            return
        # Only trigger when the bot is directly mentioned
        if self.bot.user not in message.mentions:
            return
        # Strip the mention to get the actual question
        content = message.content
        for mention_fmt in (f'<@{self.bot.user.id}>', f'<@!{self.bot.user.id}>'):
            content = content.replace(mention_fmt, '').strip()

        if not content:
            embed = discord.Embed(
                description='Hey! What can I help you with? Ask me anything or use `.help` to see all commands.',
                color=discord.Color.dark_purple()
            )
            return await message.channel.send(embed=embed)

        if not self.client:
            return await message.channel.send('❌ AI is not configured on this bot.')

        # Check AI enabled for this guild
        if message.guild:
            try:
                with open('config.json', 'r') as f:
                    config = json.load(f)
                if not config.get(str(message.guild.id), {}).get('ai_enabled', True):
                    return
            except:
                pass

        # Check if user is banned from AI
        if message.guild and self._is_banned(message.guild.id, message.author.id):
            return await message.channel.send(
                f'{message.author.mention} You have been restricted from using Vein AI.',
                delete_after=5
            )

        async with message.channel.typing():
            try:
                uid = str(message.author.id)
                self.history.setdefault(uid, [])

                messages = [{'role': 'system', 'content': BOT_KNOWLEDGE}]
                messages += self.history[uid][-10:]
                messages.append({'role': 'user', 'content': content})

                resp = self.client.chat.completions.create(
                    model='gpt-3.5-turbo',
                    messages=messages,
                    max_tokens=600
                )
                answer = resp.choices[0].message.content

                self.history[uid].append({'role': 'user', 'content': content})
                self.history[uid].append({'role': 'assistant', 'content': answer})
                if len(self.history[uid]) > 20:
                    self.history[uid] = self.history[uid][-20:]

                embed = discord.Embed(
                    description=answer,
                    color=discord.Color.dark_purple(),
                    timestamp=datetime.datetime.utcnow()
                )
                embed.set_author(
                    name='Vein AI',
                    icon_url=self.bot.user.display_avatar.url
                )
                embed.set_footer(
                    text=f'Talking with {message.author.name} • .clearai to reset history',
                    icon_url=message.author.display_avatar.url
                )
                await message.reply(embed=embed, mention_author=False)

            except Exception as e:
                logger.error(f'AI error: {e}')
                await message.channel.send('Something went wrong with AI. Try again in a moment.')

    @commands.hybrid_command(name='clearai', description='Clear your AI conversation history')
    async def clearai(self, ctx):
        self.history.pop(str(ctx.author.id), None)
        await ctx.send('✅ Your AI conversation history has been cleared.', ephemeral=True)

    @commands.hybrid_command(name='banai', description='Ban a user from using Vein AI')
    @app_commands.describe(member='Member to ban from AI')
    async def banai(self, ctx, member: discord.Member):
        if not self._is_manager(ctx.guild, ctx.author):
            return await ctx.send('❌ You need to be an AI manager or server owner to use this.')
        if member.bot:
            return await ctx.send("❌ Bots can't use AI anyway.")
        if self._is_manager(ctx.guild, member):
            return await ctx.send("❌ You can't ban an AI manager.")

        db = load_db()
        gid = str(ctx.guild.id)
        db.setdefault('ai_banned', {}).setdefault(gid, [])
        uid = str(member.id)
        if uid not in db['ai_banned'][gid]:
            db['ai_banned'][gid].append(uid)
            save_db(db)

        embed = discord.Embed(
            title='AI Access Revoked',
            description=f'{member.mention} can no longer use Vein AI in this server.',
            color=discord.Color.red()
        )
        embed.set_footer(text=f'Action by {ctx.author.name}')
        await ctx.send(embed=embed)

    @commands.hybrid_command(name='unbanai', description='Restore AI access for a user')
    @app_commands.describe(member='Member to restore AI access for')
    async def unbanai(self, ctx, member: discord.Member):
        if not self._is_manager(ctx.guild, ctx.author):
            return await ctx.send('❌ You need to be an AI manager or server owner to use this.')

        db = load_db()
        gid = str(ctx.guild.id)
        uid = str(member.id)
        banned = db.get('ai_banned', {}).get(gid, [])

        if uid not in banned:
            return await ctx.send(f'❌ {member.mention} is not banned from AI.')

        banned.remove(uid)
        db['ai_banned'][gid] = banned
        save_db(db)
        await ctx.send(f'✅ Restored AI access for {member.mention}.')

    @commands.hybrid_command(name='whitelistai', description='Add a user as an AI manager')
    @app_commands.describe(member='Member to add as AI manager')
    async def whitelistai(self, ctx, member: discord.Member):
        if ctx.author.id not in HARDCODED_MANAGERS and ctx.guild.owner_id != ctx.author.id:
            return await ctx.send('❌ Only the server owner can add AI managers.')
        if member.bot:
            return await ctx.send("❌ Can't add a bot as a manager.")

        db = load_db()
        gid = str(ctx.guild.id)
        db.setdefault('ai_managers', {}).setdefault(gid, [])
        uid = str(member.id)
        if uid not in db['ai_managers'][gid]:
            db['ai_managers'][gid].append(uid)
            save_db(db)

        embed = discord.Embed(
            title='AI Manager Added',
            description=f'{member.mention} can now manage AI access in this server.',
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(name='unwhitelistai', description='Remove an AI manager')
    @app_commands.describe(member='Member to remove from AI managers')
    async def unwhitelistai(self, ctx, member: discord.Member):
        if ctx.author.id not in HARDCODED_MANAGERS and ctx.guild.owner_id != ctx.author.id:
            return await ctx.send('❌ Only the server owner can remove AI managers.')

        db = load_db()
        gid = str(ctx.guild.id)
        uid = str(member.id)
        managers = db.get('ai_managers', {}).get(gid, [])

        if uid not in managers:
            return await ctx.send(f'❌ {member.mention} is not an AI manager.')

        managers.remove(uid)
        db['ai_managers'][gid] = managers
        save_db(db)
        await ctx.send(f'✅ Removed {member.mention} from AI managers.')

    @commands.hybrid_command(name='aimanagers', description='List AI managers in this server')
    async def aimanagers(self, ctx):
        if not self._is_manager(ctx.guild, ctx.author):
            return await ctx.send('❌ You need to be an AI manager to view this.')

        db = load_db()
        gid = str(ctx.guild.id)
        manager_ids = db.get('ai_managers', {}).get(gid, [])

        embed = discord.Embed(title='🤖 AI Managers', color=discord.Color.blue())
        lines = []

        for uid in manager_ids:
            m = ctx.guild.get_member(int(uid))
            lines.append(m.mention if m else f'<@{uid}>')

        if not lines:
            embed.description = 'No additional managers — only the server owner has access.'
        else:
            embed.description = '\n'.join(lines)

        embed.set_footer(text='The server owner always has full AI management access.')
        await ctx.send(embed=embed)

    @commands.hybrid_command(name='aibanned', description='List users banned from AI')
    async def aibanned(self, ctx):
        if not self._is_manager(ctx.guild, ctx.author):
            return await ctx.send('❌ You need to be an AI manager to view this.')

        db = load_db()
        gid = str(ctx.guild.id)
        banned_ids = db.get('ai_banned', {}).get(gid, [])

        embed = discord.Embed(title='🚫 AI Banned Users', color=discord.Color.red())
        if not banned_ids:
            embed.description = 'No users are currently banned from AI.'
        else:
            lines = []
            for uid in banned_ids:
                m = ctx.guild.get_member(int(uid))
                lines.append(m.mention if m else f'<@{uid}>')
            embed.description = '\n'.join(lines)

        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(AI(bot))
