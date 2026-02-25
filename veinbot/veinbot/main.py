import discord
from discord.ext import commands
import json, os, logging, asyncio
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[logging.FileHandler('vein.log'), logging.StreamHandler()]
)
logger = logging.getLogger('vein')


def get_prefix(bot, message):
    if not message.guild:
        return '.'
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
        return config.get(str(message.guild.id), {}).get('prefix', '.')
    except:
        return '.'


intents = discord.Intents.all()
bot = commands.Bot(
    command_prefix=get_prefix,
    intents=intents,
    help_command=None,
    case_insensitive=True
)

COGS = [
    'cogs.moderation',
    'cogs.antinuke',
    'cogs.leveling',
    'cogs.economy',
    'cogs.welcome',
    'cogs.filter',
    'cogs.music',
    'cogs.tickets',
    'cogs.ai',
    'cogs.mod_logging',
    'cogs.fun',
    'cogs.utility',
    'cogs.suggestions',
    'cogs.giveaway',
]


@bot.event
async def on_ready():
    logger.info(f'Logged in as {bot.user} (ID: {bot.user.id})')
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name=f'{len(bot.guilds)} servers | .help'
        )
    )
    try:
        synced = await bot.tree.sync()
        logger.info(f'Synced {len(synced)} slash commands')
    except Exception as e:
        logger.error(f'Sync failed: {e}')


@bot.event
async def on_guild_join(guild):
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
    except:
        config = {}
    if str(guild.id) not in config:
        config[str(guild.id)] = {'prefix': '.'}
        with open('config.json', 'w') as f:
            json.dump(config, f, indent=4)


@bot.hybrid_command(name='help', description='Show all commands and how to use them')
async def help_command(ctx: commands.Context, category: str = None):
    cats = {
        'moderation': (
            '🛡️ Moderation',
            [
                ('ban <@user> [reason]', 'Ban a member from the server'),
                ('unban <user_id> [reason]', 'Unban a user by their ID'),
                ('kick <@user> [reason]', 'Kick a member from the server'),
                ('timeout <@user> [minutes] [reason]', 'Timeout a member'),
                ('untimeout <@user>', 'Remove a timeout'),
                ('warn <@user> [reason]', 'Issue a warning (3 warnings = auto timeout)'),
                ('warnings <@user>', 'View a member\'s warnings'),
                ('clearwarns <@user>', 'Clear all warnings for a member'),
                ('purge <amount>', 'Delete messages (max 10,000 — use 0 for all)'),
                ('snipe', 'Recover the last deleted message'),
                ('editsnipe', 'Recover the last edited message'),
                ('lock [#channel]', 'Prevent members from sending messages'),
                ('unlock [#channel]', 'Restore send permissions'),
                ('slowmode <seconds> [#channel]', 'Set slowmode (0 to disable)'),
                ('nick <@user> [nickname]', 'Change or reset a member\'s nickname'),
            ]
        ),
        'antinuke': (
            '🔒 Anti-Nuke',
            [
                ('antinuke <true/false>', 'Toggle the anti-nuke system'),
                ('whitelist <@user>', 'Whitelist a user from anti-nuke detection'),
                ('unwhitelist <@user>', 'Remove a user from the whitelist'),
                ('whitelistlist', 'View all whitelisted users'),
            ]
        ),
        'leveling': (
            '📊 Leveling',
            [
                ('rank [@user]', 'View your or another member\'s rank card'),
                ('leaderboard', 'View the top 10 members by XP'),
                ('setxp <@user> <amount>', 'Set XP for a member (Admin)'),
                ('setlevel <@user> <level>', 'Set level for a member (Admin)'),
                ('resetxp <@user>', 'Reset XP for a member (Admin)'),
                ('xpmultiplier <value>', 'Set server-wide XP multiplier (Admin)'),
            ]
        ),
        'economy': (
            '💰 Economy',
            [
                ('balance [@user]', 'Check wallet and bank balance'),
                ('daily', 'Claim your daily reward (streak bonuses apply)'),
                ('work', 'Work a job to earn money (1hr cooldown)'),
                ('gamble <amount>', 'Gamble your money for a chance to win big'),
                ('deposit <amount/all>', 'Deposit money into your bank'),
                ('withdraw <amount/all>', 'Withdraw money from your bank'),
                ('transfer <@user> <amount>', 'Send money to another member'),
                ('shop', 'Browse the server shop'),
                ('shop add <name> <price> <desc>', 'Add item to shop (Admin)'),
                ('shop remove <id>', 'Remove item from shop (Admin)'),
                ('buy <item_id>', 'Purchase an item from the shop'),
                ('inventory', 'View your purchased items'),
                ('rich', 'Top 10 richest members leaderboard'),
            ]
        ),
        'music': (
            '🎵 Music',
            [
                ('play <song/url>', 'Play a song from YouTube or URL'),
                ('pause', 'Pause playback'),
                ('resume', 'Resume playback'),
                ('skip', 'Skip the current track'),
                ('stop', 'Stop music and disconnect'),
                ('queue', 'View the current queue'),
                ('nowplaying', 'Show the currently playing track'),
                ('volume <0-100>', 'Adjust playback volume'),
                ('loop', 'Toggle track looping'),
                ('shuffle', 'Shuffle the queue'),
                ('clearqueue', 'Clear all tracks from the queue'),
                ('disconnect', 'Disconnect from voice channel'),
            ]
        ),
        'tickets': (
            '🎫 Tickets',
            [
                ('ticketpanel', 'Send the ticket creation panel (Admin)'),
                ('ticketsetup category <category>', 'Set ticket category (Admin)'),
                ('ticketsetup staffrole <@role>', 'Set staff role for tickets (Admin)'),
                ('adduser <@user>', 'Add a user to the current ticket'),
                ('removeuser <@user>', 'Remove a user from the current ticket'),
                ('rename <name>', 'Rename the current ticket channel'),
                ('transcript', 'Save the ticket transcript as a file'),
            ]
        ),
        'giveaway': (
            '🎉 Giveaway',
            [
                ('gstart <time> <winners> <prize>', 'Start a giveaway (e.g. .gstart 1h 1 Nitro)'),
                ('gend <message_id>', 'End a giveaway early and pick winners'),
                ('greroll <message_id>', 'Reroll the winner of a finished giveaway'),
                ('glist', 'View all active giveaways in this server'),
            ]
        ),
        'fun': (
            '🎮 Fun',
            [
                ('8ball <question>', 'Ask the magic 8 ball'),
                ('coinflip', 'Flip a coin'),
                ('dice [sides]', 'Roll a dice (default: d6)'),
                ('rps <rock/paper/scissors>', 'Play rock paper scissors'),
                ('meme', 'Fetch a random meme'),
                ('joke', 'Get a random joke'),
                ('fact', 'Get a random fun fact'),
                ('poll <question> <opt1, opt2,...>', 'Create a reaction poll'),
                ('choose <opt1, opt2,...>', 'Let the bot choose for you'),
                ('avatar [@user]', 'Display a user\'s avatar'),
                ('banner [@user]', 'Display a user\'s banner'),
                ('servericon', 'Display the server icon'),
                ('say <message>', 'Make the bot say something (Manage Messages)'),
                ('embed <title> <desc> [color]', 'Create a custom embed (Manage Messages)'),
            ]
        ),
        'utility': (
            '🔧 Utility',
            [
                ('ping', 'Check bot latency'),
                ('stats', 'View bot statistics'),
                ('serverinfo', 'View server information'),
                ('userinfo [@user]', 'View user information'),
                ('roleinfo <@role>', 'View role information'),
                ('botinfo', 'View Vein\'s information'),
                ('invite', 'Get the bot invite link'),
                ('uptime', 'Check how long the bot has been online'),
                ('prefix <new_prefix>', 'Change the command prefix (Admin)'),
                ('logs <#channel>', 'Set the logging channel (Admin)'),
            ]
        ),
        'ai': (
            '🤖 AI',
            [
                ('@Vein <message>', 'Chat with Vein AI — just mention the bot'),
                ('clearai', 'Clear your personal AI conversation history'),
                ('banai <@user>', 'Ban a user from using AI (Managers only)'),
                ('unbanai <@user>', 'Unban a user from AI (Managers only)'),
                ('whitelistai <@user>', 'Add a user as an AI manager (Owner only)'),
                ('unwhitelistai <@user>', 'Remove an AI manager (Owner only)'),
                ('aimanagers', 'List current AI managers'),
                ('aibanned', 'List users banned from AI (Managers only)'),
            ]
        ),
        'suggestions': (
            '💡 Suggestions',
            [
                ('suggest <idea>', 'Submit a suggestion to the server'),
                ('approve <id> [reason]', 'Approve a suggestion (Manage Messages)'),
                ('deny <id> [reason]', 'Deny a suggestion (Manage Messages)'),
                ('suggestions [all/pending/approved/denied]', 'Browse suggestions'),
                ('suggestchannel <#channel>', 'Set the suggestions channel (Admin)'),
            ]
        ),
        'welcome': (
            '👋 Welcome',
            [
                ('setwelcome <#channel> [message]', 'Set the welcome channel and message'),
                ('setleave <#channel> [message]', 'Set the leave channel and message'),
                ('setautorole <@role>', 'Assign a role to new members automatically'),
                ('testwelcome', 'Preview the welcome message'),
            ]
        ),
        'filter': (
            '🚫 Filter',
            [
                ('filter', 'View current filter settings'),
                ('filter spam <true/false>', 'Toggle spam detection'),
                ('filter links <true/false>', 'Toggle link blocking'),
                ('filter invites <true/false>', 'Toggle invite blocking'),
                ('filter caps <true/false>', 'Toggle excessive caps filter'),
                ('filter addword <word>', 'Add a word to the banned list'),
                ('filter removeword <word>', 'Remove a word from the banned list'),
            ]
        ),
    }

    if category and category.lower() in cats:
        name, cmds = cats[category.lower()]
        embed = discord.Embed(
            title=f'{name} — Command Reference',
            color=discord.Color.blue()
        )
        embed.description = '\n'.join([f'`{cmd}` — {desc}' for cmd, desc in cmds])
        embed.set_footer(text='Prefix: . | Also supports / slash commands • <required> [optional]')
        return await ctx.send(embed=embed)

    embed = discord.Embed(
        title='Vein — Command Help',
        description='Use `.help <category>` to see detailed commands for each module.\nAll commands work with `.` prefix or `/` slash commands.',
        color=discord.Color.dark_purple()
    )
    for key, (name, _) in cats.items():
        embed.add_field(name=name, value=f'`.help {key}`', inline=True)

    embed.set_thumbnail(url=bot.user.display_avatar.url)
    embed.set_footer(text='Prefix: . | Slash: / | Mention the bot to use AI')
    await ctx.send(embed=embed)


async def main():
    for fname in ('config.json', 'database.json'):
        if not os.path.exists(fname):
            with open(fname, 'w') as f:
                json.dump({}, f)

    async with bot:
        for cog in COGS:
            try:
                await bot.load_extension(cog)
                logger.info(f'Loaded: {cog}')
            except Exception as e:
                logger.error(f'Failed to load {cog}: {e}')

        token = os.getenv('TOKEN')
        if not token:
            logger.critical('No TOKEN found in .env — bot cannot start.')
            return
        await bot.start(token)


if __name__ == '__main__':
    asyncio.run(main())
