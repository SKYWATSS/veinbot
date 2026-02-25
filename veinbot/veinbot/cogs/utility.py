import discord
from discord.ext import commands
from discord import app_commands
import datetime, time, json, os
from typing import Optional
import logging

logger = logging.getLogger(__name__)

try:
    import psutil
    PSUTIL = True
except ImportError:
    PSUTIL = False


class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.start_time = time.time()

    @commands.hybrid_command(name='ping', description='Check the bot\'s latency')
    async def ping(self, ctx):
        start = time.time()
        msg = await ctx.send('Measuring...')
        rtt = round((time.time() - start) * 1000)
        ws = round(self.bot.latency * 1000)

        if ws < 100:
            color = discord.Color.green()
            status = 'Excellent'
        elif ws < 200:
            color = discord.Color.gold()
            status = 'Good'
        else:
            color = discord.Color.red()
            status = 'Slow'

        embed = discord.Embed(title='🏓 Pong!', color=color, timestamp=datetime.datetime.utcnow())
        embed.add_field(name='WebSocket', value=f'`{ws}ms`', inline=True)
        embed.add_field(name='Round Trip', value=f'`{rtt}ms`', inline=True)
        embed.add_field(name='Status', value=status, inline=True)
        await msg.edit(content=None, embed=embed)

    @commands.hybrid_command(name='stats', description='View bot statistics')
    async def stats(self, ctx):
        up = int(time.time() - self.start_time)
        uptime_str = str(datetime.timedelta(seconds=up))
        total_users = sum(g.member_count for g in self.bot.guilds)

        embed = discord.Embed(
            title='📊 Vein — Statistics',
            color=discord.Color.dark_purple(),
            timestamp=datetime.datetime.utcnow()
        )
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        embed.add_field(name='Servers', value=f'`{len(self.bot.guilds):,}`', inline=True)
        embed.add_field(name='Users', value=f'`{total_users:,}`', inline=True)
        embed.add_field(name='Latency', value=f'`{round(self.bot.latency * 1000)}ms`', inline=True)
        embed.add_field(name='Uptime', value=f'`{uptime_str}`', inline=True)

        if PSUTIL:
            proc = psutil.Process(os.getpid())
            mem = proc.memory_info().rss / 1024 / 1024
            embed.add_field(name='Memory', value=f'`{mem:.1f} MB`', inline=True)
            embed.add_field(name='CPU', value=f'`{psutil.cpu_percent()}%`', inline=True)

        embed.set_footer(text='Vein Bot')
        await ctx.send(embed=embed)

    @commands.hybrid_command(name='serverinfo', description='View information about this server')
    async def serverinfo(self, ctx):
        g = ctx.guild
        humans = sum(1 for m in g.members if not m.bot)
        bots = sum(1 for m in g.members if m.bot)
        online = sum(1 for m in g.members if m.status != discord.Status.offline and not m.bot)

        embed = discord.Embed(
            title=g.name,
            description=g.description or '',
            color=discord.Color.blue(),
            timestamp=datetime.datetime.utcnow()
        )
        if g.icon:
            embed.set_thumbnail(url=g.icon.url)
        if g.banner:
            embed.set_image(url=g.banner.url)

        embed.add_field(name='Owner', value=g.owner.mention if g.owner else 'Unknown', inline=True)
        embed.add_field(name='Server ID', value=f'`{g.id}`', inline=True)
        embed.add_field(name='Created', value=f'<t:{int(g.created_at.timestamp())}:D>\n(<t:{int(g.created_at.timestamp())}:R>)', inline=True)
        embed.add_field(
            name=f'Members ({g.member_count})',
            value=f'👤 {humans} humans\n🟢 {online} online\n🤖 {bots} bots',
            inline=True
        )
        embed.add_field(
            name='Channels',
            value=f'💬 {len(g.text_channels)} text\n🔊 {len(g.voice_channels)} voice\n📁 {len(g.categories)} categories',
            inline=True
        )
        embed.add_field(
            name='Other',
            value=f'🎭 {len(g.roles)} roles\n😀 {len(g.emojis)} emojis\n✨ Boost Tier {g.premium_tier} ({g.premium_subscription_count} boosts)',
            inline=True
        )
        embed.set_footer(text=f'Requested by {ctx.author.name}', icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name='userinfo', description='View information about a user')
    @app_commands.describe(member='Member to look up (defaults to yourself)')
    async def userinfo(self, ctx, member: Optional[discord.Member] = None):
        member = member or ctx.author

        key_perms = []
        if member.guild_permissions.administrator: key_perms.append('Administrator')
        if member.guild_permissions.manage_guild: key_perms.append('Manage Server')
        if member.guild_permissions.ban_members: key_perms.append('Ban Members')
        if member.guild_permissions.kick_members: key_perms.append('Kick Members')
        if member.guild_permissions.manage_roles: key_perms.append('Manage Roles')
        if member.guild_permissions.manage_channels: key_perms.append('Manage Channels')
        if member.guild_permissions.manage_messages: key_perms.append('Manage Messages')

        roles = [r.mention for r in reversed(member.roles) if r.name != '@everyone']

        embed = discord.Embed(
            title=f'{member.display_name}',
            color=member.color if member.color.value else discord.Color.blue(),
            timestamp=datetime.datetime.utcnow()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name='Username', value=f'{member.name}', inline=True)
        embed.add_field(name='User ID', value=f'`{member.id}`', inline=True)
        embed.add_field(name='Bot', value='Yes' if member.bot else 'No', inline=True)
        embed.add_field(name='Account Created', value=f'<t:{int(member.created_at.timestamp())}:D>\n(<t:{int(member.created_at.timestamp())}:R>)', inline=True)
        embed.add_field(name='Joined Server', value=f'<t:{int(member.joined_at.timestamp())}:D>\n(<t:{int(member.joined_at.timestamp())}:R>)' if member.joined_at else 'Unknown', inline=True)
        embed.add_field(name='Nickname', value=member.nick or 'None', inline=True)
        embed.add_field(
            name=f'Roles ({len(roles)})',
            value=', '.join(roles[:8]) + (f' +{len(roles)-8} more' if len(roles) > 8 else '') if roles else 'None',
            inline=False
        )
        if key_perms:
            embed.add_field(name='Key Permissions', value=', '.join(key_perms), inline=False)

        embed.set_footer(text=f'Requested by {ctx.author.name}', icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name='roleinfo', description='View information about a role')
    @app_commands.describe(role='Role to look up')
    async def roleinfo(self, ctx, role: discord.Role):
        key_perms = []
        if role.permissions.administrator: key_perms.append('Administrator')
        if role.permissions.manage_guild: key_perms.append('Manage Server')
        if role.permissions.ban_members: key_perms.append('Ban Members')
        if role.permissions.kick_members: key_perms.append('Kick Members')
        if role.permissions.manage_roles: key_perms.append('Manage Roles')
        if role.permissions.manage_channels: key_perms.append('Manage Channels')
        if role.permissions.manage_messages: key_perms.append('Manage Messages')

        embed = discord.Embed(
            title=f'Role — {role.name}',
            color=role.color if role.color.value else discord.Color.default(),
            timestamp=datetime.datetime.utcnow()
        )
        embed.add_field(name='Role ID', value=f'`{role.id}`', inline=True)
        embed.add_field(name='Color', value=str(role.color), inline=True)
        embed.add_field(name='Position', value=str(role.position), inline=True)
        embed.add_field(name='Members', value=str(len(role.members)), inline=True)
        embed.add_field(name='Hoisted', value='Yes' if role.hoist else 'No', inline=True)
        embed.add_field(name='Mentionable', value='Yes' if role.mentionable else 'No', inline=True)
        embed.add_field(name='Created', value=f'<t:{int(role.created_at.timestamp())}:R>', inline=True)
        if key_perms:
            embed.add_field(name='Key Permissions', value=', '.join(key_perms), inline=False)

        await ctx.send(embed=embed)

    @commands.hybrid_command(name='botinfo', description='View information about Vein')
    async def botinfo(self, ctx):
        embed = discord.Embed(
            title='Vein',
            description='An all-in-one Discord bot built for serious servers.',
            color=discord.Color.dark_purple(),
            timestamp=datetime.datetime.utcnow()
        )
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        embed.add_field(name='Library', value='discord.py', inline=True)
        embed.add_field(name='Prefix', value='`.` or `/`', inline=True)
        embed.add_field(name='Servers', value=str(len(self.bot.guilds)), inline=True)
        embed.add_field(
            name='Modules',
            value='Moderation • Anti-Nuke • Leveling\nEconomy • Music • Tickets\nGiveaways • AI • Logging\nWelcome • Filter • Suggestions',
            inline=False
        )
        embed.set_footer(text='Use .help to see all commands')
        await ctx.send(embed=embed)

    @commands.hybrid_command(name='invite', description='Get the invite link for Vein')
    async def invite(self, ctx):
        perms = discord.Permissions(administrator=True)
        link = discord.utils.oauth_url(self.bot.user.id, permissions=perms)
        embed = discord.Embed(
            title='📨 Invite Vein',
            description='Add Vein to your own server using the link below.',
            color=discord.Color.blue()
        )
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label='Invite Vein', url=link, emoji='📨'))
        await ctx.send(embed=embed, view=view)

    @commands.hybrid_command(name='uptime', description='Check how long the bot has been online')
    async def uptime(self, ctx):
        up = int(time.time() - self.start_time)
        uptime_str = str(datetime.timedelta(seconds=up))
        embed = discord.Embed(
            title='⏰ Uptime',
            description=f'Vein has been online for **{uptime_str}**.',
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(name='prefix', description='Change the command prefix for this server')
    @commands.has_permissions(administrator=True)
    @app_commands.describe(new_prefix='The new prefix to use (e.g. !, ?, $)')
    async def prefix(self, ctx, new_prefix: str):
        if len(new_prefix) > 5:
            return await ctx.send('❌ Prefix must be 5 characters or fewer.')
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
        except:
            config = {}
        config.setdefault(str(ctx.guild.id), {})['prefix'] = new_prefix
        with open('config.json', 'w') as f:
            json.dump(config, f, indent=4)
        await ctx.send(f'✅ Prefix updated to `{new_prefix}`.')

    @commands.hybrid_command(name='logs', description='Set the mod-log channel for this server')
    @commands.has_permissions(administrator=True)
    @app_commands.describe(channel='Channel to send log events to')
    async def logs(self, ctx, channel: discord.TextChannel):
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
        except:
            config = {}
        config.setdefault(str(ctx.guild.id), {})['logs_channel'] = channel.id
        with open('config.json', 'w') as f:
            json.dump(config, f, indent=4)
        await ctx.send(f'✅ Mod logs will now be sent to {channel.mention}.')


async def setup(bot):
    await bot.add_cog(Utility(bot))
