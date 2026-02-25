import discord
from discord.ext import commands
from discord import app_commands
import json, datetime, asyncio
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.snipe_cache = {}
        self.edit_snipe_cache = {}
        self.warnings = {}
        self.load_data()

    def load_data(self):
        try:
            with open('database.json', 'r') as f:
                data = json.load(f)
            self.warnings = data.get('warnings', {})
        except:
            self.warnings = {}

    def save_data(self):
        try:
            with open('database.json', 'r') as f:
                data = json.load(f)
        except:
            data = {}
        data['warnings'] = self.warnings
        with open('database.json', 'w') as f:
            json.dump(data, f, indent=4)

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot:
            return
        self.snipe_cache[message.channel.id] = {
            'content': message.content,
            'author': message.author,
            'time': datetime.datetime.utcnow(),
            'attachments': [a.url for a in message.attachments]
        }

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.author.bot or before.content == after.content:
            return
        self.edit_snipe_cache[before.channel.id] = {
            'before': before.content,
            'after': after.content,
            'author': before.author,
            'time': datetime.datetime.utcnow()
        }

    @commands.hybrid_command(name='ban', description='Ban a member from the server')
    @commands.has_permissions(ban_members=True)
    @app_commands.describe(member='Member to ban', reason='Reason for the ban', delete_days='Days of messages to delete (0–7)')
    async def ban(self, ctx, member: discord.Member, reason: str = 'No reason provided', delete_days: int = 0):
        if member == ctx.author:
            return await ctx.send('❌ You cannot ban yourself.')
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            return await ctx.send('❌ You cannot ban someone with an equal or higher role.')
        if not ctx.guild.me.guild_permissions.ban_members:
            return await ctx.send("❌ I don't have permission to ban members.")

        try:
            await member.send(f'You have been **banned** from **{ctx.guild.name}**.\nReason: {reason}')
        except:
            pass

        await member.ban(reason=f'{ctx.author} | {reason}', delete_message_days=min(max(delete_days, 0), 7))

        embed = discord.Embed(title='🔨 Member Banned', color=discord.Color.red(), timestamp=datetime.datetime.utcnow())
        embed.add_field(name='User', value=f'{member} (`{member.id}`)')
        embed.add_field(name='Moderator', value=ctx.author.mention)
        embed.add_field(name='Reason', value=reason, inline=False)
        embed.set_thumbnail(url=member.display_avatar.url)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name='unban', description='Unban a user by their ID')
    @commands.has_permissions(ban_members=True)
    @app_commands.describe(user_id='The user ID to unban', reason='Reason')
    async def unban(self, ctx, user_id: int, reason: str = 'No reason provided'):
        try:
            user = await self.bot.fetch_user(user_id)
            await ctx.guild.unban(user, reason=f'{ctx.author} | {reason}')
            embed = discord.Embed(
                title='✅ Member Unbanned',
                description=f'**{user}** (`{user.id}`) has been unbanned.',
                color=discord.Color.green()
            )
            embed.add_field(name='Moderator', value=ctx.author.mention)
            embed.add_field(name='Reason', value=reason)
            await ctx.send(embed=embed)
        except discord.NotFound:
            await ctx.send('❌ That user was not found or is not banned.')
        except Exception as e:
            await ctx.send(f'❌ Error: {e}')

    @commands.hybrid_command(name='kick', description='Kick a member from the server')
    @commands.has_permissions(kick_members=True)
    @app_commands.describe(member='Member to kick', reason='Reason for the kick')
    async def kick(self, ctx, member: discord.Member, *, reason: str = 'No reason provided'):
        if member == ctx.author:
            return await ctx.send('❌ You cannot kick yourself.')
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            return await ctx.send('❌ You cannot kick someone with an equal or higher role.')

        try:
            await member.send(f'You have been **kicked** from **{ctx.guild.name}**.\nReason: {reason}')
        except:
            pass

        await member.kick(reason=f'{ctx.author} | {reason}')

        embed = discord.Embed(title='👢 Member Kicked', color=discord.Color.orange(), timestamp=datetime.datetime.utcnow())
        embed.add_field(name='User', value=f'{member} (`{member.id}`)')
        embed.add_field(name='Moderator', value=ctx.author.mention)
        embed.add_field(name='Reason', value=reason, inline=False)
        embed.set_thumbnail(url=member.display_avatar.url)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name='timeout', description='Timeout a member')
    @commands.has_permissions(moderate_members=True)
    @app_commands.describe(member='Member to timeout', duration='Duration in minutes (default: 10)', reason='Reason')
    async def timeout(self, ctx, member: discord.Member, duration: int = 10, *, reason: str = 'No reason provided'):
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            return await ctx.send('❌ You cannot timeout someone with an equal or higher role.')

        until = discord.utils.utcnow() + datetime.timedelta(minutes=duration)
        await member.timeout(until, reason=f'{ctx.author} | {reason}')

        embed = discord.Embed(title='⏰ Member Timed Out', color=discord.Color.orange(), timestamp=datetime.datetime.utcnow())
        embed.add_field(name='User', value=f'{member}')
        embed.add_field(name='Duration', value=f'{duration} minutes')
        embed.add_field(name='Expires', value=f'<t:{int(until.timestamp())}:R>')
        embed.add_field(name='Reason', value=reason, inline=False)
        embed.add_field(name='Moderator', value=ctx.author.mention)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name='untimeout', description='Remove a timeout from a member')
    @commands.has_permissions(moderate_members=True)
    @app_commands.describe(member='Member to untimeout')
    async def untimeout(self, ctx, member: discord.Member):
        await member.timeout(None)
        await ctx.send(f'✅ Timeout removed from **{member}**.')

    @commands.hybrid_command(name='warn', description='Issue a warning to a member')
    @commands.has_permissions(manage_messages=True)
    @app_commands.describe(member='Member to warn', reason='Reason for the warning')
    async def warn(self, ctx, member: discord.Member, *, reason: str = 'No reason provided'):
        if member.bot:
            return await ctx.send("❌ You can't warn a bot.")

        key = f'{ctx.guild.id}:{member.id}'
        if key not in self.warnings:
            self.warnings[key] = []
        self.warnings[key].append({
            'reason': reason,
            'moderator': ctx.author.id,
            'time': str(datetime.datetime.utcnow())
        })
        self.save_data()
        count = len(self.warnings[key])

        try:
            await member.send(f'You received a **warning** in **{ctx.guild.name}**.\nReason: {reason}\nTotal warnings: {count}')
        except:
            pass

        embed = discord.Embed(title='⚠️ Member Warned', color=discord.Color.yellow(), timestamp=datetime.datetime.utcnow())
        embed.add_field(name='User', value=str(member))
        embed.add_field(name='Moderator', value=ctx.author.mention)
        embed.add_field(name='Reason', value=reason, inline=False)
        embed.add_field(name='Total Warnings', value=str(count))
        await ctx.send(embed=embed)

        if count >= 3:
            try:
                until = discord.utils.utcnow() + datetime.timedelta(hours=1)
                await member.timeout(until, reason='Auto-timeout: reached 3 warnings')
                await ctx.send(f'⚠️ {member.mention} has been auto-timed out for 1 hour after reaching 3 warnings.')
            except:
                pass

    @commands.hybrid_command(name='warnings', description='View warnings for a member')
    @commands.has_permissions(manage_messages=True)
    @app_commands.describe(member='Member to check')
    async def warnings(self, ctx, member: discord.Member):
        key = f'{ctx.guild.id}:{member.id}'
        warns = self.warnings.get(key, [])
        if not warns:
            return await ctx.send(f'{member.mention} has no warnings on record.')

        embed = discord.Embed(
            title=f'⚠️ Warnings — {member.name}',
            color=discord.Color.yellow(),
            timestamp=datetime.datetime.utcnow()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        for i, w in enumerate(warns, 1):
            mod = ctx.guild.get_member(w['moderator'])
            mod_str = mod.mention if mod else f'<@{w["moderator"]}>'
            embed.add_field(
                name=f'Warning {i}',
                value=f'Reason: {w["reason"]}\nModerator: {mod_str}',
                inline=False
            )
        embed.set_footer(text=f'Total: {len(warns)} warning(s)')
        await ctx.send(embed=embed)

    @commands.hybrid_command(name='clearwarns', description='Clear all warnings for a member')
    @commands.has_permissions(manage_guild=True)
    @app_commands.describe(member='Member to clear warnings for')
    async def clearwarns(self, ctx, member: discord.Member):
        key = f'{ctx.guild.id}:{member.id}'
        self.warnings[key] = []
        self.save_data()
        await ctx.send(f'✅ Cleared all warnings for {member.mention}.')

    @commands.hybrid_command(name='purge', description='Bulk delete messages from a channel')
    @commands.has_permissions(manage_messages=True)
    @app_commands.describe(amount='Number of messages to delete (max 10,000 — use 0 for all)')
    async def purge(self, ctx, amount: int = 10):
        await ctx.defer(ephemeral=True)
        if amount <= 0:
            amount = 10000
        amount = min(amount, 10000)
        deleted = await ctx.channel.purge(limit=amount)
        await ctx.send(f'✅ Deleted **{len(deleted)}** message(s).', ephemeral=True)

    @commands.hybrid_command(name='snipe', description='Show the last deleted message in this channel')
    async def snipe(self, ctx):
        data = self.snipe_cache.get(ctx.channel.id)
        if not data:
            return await ctx.send('There is nothing to snipe in this channel.')

        embed = discord.Embed(
            description=data['content'] or '*[no text content]*',
            color=discord.Color.red(),
            timestamp=data['time']
        )
        embed.set_author(name=str(data['author']), icon_url=data['author'].display_avatar.url)
        embed.set_footer(text='Message deleted')
        if data['attachments']:
            embed.set_image(url=data['attachments'][0])
        await ctx.send(embed=embed)

    @commands.hybrid_command(name='editsnipe', description='Show the last edited message in this channel')
    async def editsnipe(self, ctx):
        data = self.edit_snipe_cache.get(ctx.channel.id)
        if not data:
            return await ctx.send('There is nothing to editsnipe in this channel.')

        embed = discord.Embed(color=discord.Color.orange(), timestamp=data['time'])
        embed.set_author(name=str(data['author']), icon_url=data['author'].display_avatar.url)
        embed.add_field(name='Before', value=data['before'] or '*[no text]*', inline=False)
        embed.add_field(name='After', value=data['after'] or '*[no text]*', inline=False)
        embed.set_footer(text='Message edited')
        await ctx.send(embed=embed)

    @commands.hybrid_command(name='lock', description='Lock a channel so members cannot send messages')
    @commands.has_permissions(manage_channels=True)
    @app_commands.describe(channel='Channel to lock (defaults to current channel)')
    async def lock(self, ctx, channel: Optional[discord.TextChannel] = None):
        channel = channel or ctx.channel
        await channel.set_permissions(ctx.guild.default_role, send_messages=False)
        embed = discord.Embed(
            title='🔒 Channel Locked',
            description=f'{channel.mention} has been locked. Members can no longer send messages.',
            color=discord.Color.red()
        )
        embed.set_footer(text=f'Locked by {ctx.author.name}')
        await ctx.send(embed=embed)

    @commands.hybrid_command(name='unlock', description='Unlock a channel')
    @commands.has_permissions(manage_channels=True)
    @app_commands.describe(channel='Channel to unlock (defaults to current channel)')
    async def unlock(self, ctx, channel: Optional[discord.TextChannel] = None):
        channel = channel or ctx.channel
        await channel.set_permissions(ctx.guild.default_role, send_messages=True)
        embed = discord.Embed(
            title='🔓 Channel Unlocked',
            description=f'{channel.mention} has been unlocked.',
            color=discord.Color.green()
        )
        embed.set_footer(text=f'Unlocked by {ctx.author.name}')
        await ctx.send(embed=embed)

    @commands.hybrid_command(name='slowmode', description='Set slowmode delay in a channel')
    @commands.has_permissions(manage_channels=True)
    @app_commands.describe(seconds='Slowmode in seconds (0 to disable)', channel='Channel (defaults to current)')
    async def slowmode(self, ctx, seconds: int = 0, channel: Optional[discord.TextChannel] = None):
        channel = channel or ctx.channel
        if seconds < 0 or seconds > 21600:
            return await ctx.send('❌ Slowmode must be between 0 and 21600 seconds (6 hours).')
        await channel.edit(slowmode_delay=seconds)
        if seconds == 0:
            await ctx.send(f'✅ Slowmode disabled in {channel.mention}.')
        else:
            await ctx.send(f'✅ Slowmode set to **{seconds}s** in {channel.mention}.')

    @commands.hybrid_command(name='nick', description='Change or reset a member\'s nickname')
    @commands.has_permissions(manage_nicknames=True)
    @app_commands.describe(member='Member to change', nickname='New nickname (leave blank to reset)')
    async def nick(self, ctx, member: discord.Member, *, nickname: str = None):
        try:
            await member.edit(nick=nickname)
            if nickname:
                await ctx.send(f'✅ Nickname changed to **{nickname}** for {member.mention}.')
            else:
                await ctx.send(f'✅ Nickname reset for {member.mention}.')
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to change that member's nickname.")


async def setup(bot):
    await bot.add_cog(Moderation(bot))
