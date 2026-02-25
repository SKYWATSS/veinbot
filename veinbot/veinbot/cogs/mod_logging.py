import discord
from discord.ext import commands
import json, datetime
import logging

logger = logging.getLogger(__name__)


class ModLogging(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_log_channel(self, guild_id):
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
            cid = config.get(str(guild_id), {}).get('logs_channel')
            return self.bot.get_channel(cid) if cid else None
        except:
            return None

    async def log(self, guild_id, embed):
        ch = self.get_log_channel(guild_id)
        if ch:
            try:
                await ch.send(embed=embed)
            except:
                pass

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot or not message.guild:
            return
        embed = discord.Embed(title='🗑️ Message Deleted', color=discord.Color.red(), timestamp=datetime.datetime.utcnow())
        embed.set_author(name=str(message.author), icon_url=message.author.display_avatar.url)
        embed.add_field(name='Channel', value=message.channel.mention, inline=True)
        embed.add_field(name='Author', value=message.author.mention, inline=True)
        embed.add_field(name='Content', value=message.content[:1024] or '*No text content*', inline=False)
        if message.attachments:
            embed.add_field(name='Attachments', value=str(len(message.attachments)), inline=True)
        await self.log(message.guild.id, embed)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.author.bot or before.content == after.content or not before.guild:
            return
        embed = discord.Embed(title='✏️ Message Edited', color=discord.Color.orange(), timestamp=datetime.datetime.utcnow())
        embed.set_author(name=str(before.author), icon_url=before.author.display_avatar.url)
        embed.add_field(name='Channel', value=before.channel.mention, inline=True)
        embed.add_field(name='Jump', value=f'[View Message]({after.jump_url})', inline=True)
        embed.add_field(name='Before', value=before.content[:512] or '*No text*', inline=False)
        embed.add_field(name='After', value=after.content[:512] or '*No text*', inline=False)
        await self.log(before.guild.id, embed)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        embed = discord.Embed(title='📥 Member Joined', color=discord.Color.green(), timestamp=datetime.datetime.utcnow())
        embed.set_author(name=str(member), icon_url=member.display_avatar.url)
        embed.add_field(name='Account Created', value=f'<t:{int(member.created_at.timestamp())}:R>', inline=True)
        embed.add_field(name='User ID', value=f'`{member.id}`', inline=True)
        embed.add_field(name='Member Count', value=str(member.guild.member_count), inline=True)
        await self.log(member.guild.id, embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        embed = discord.Embed(title='📤 Member Left', color=discord.Color.red(), timestamp=datetime.datetime.utcnow())
        embed.set_author(name=str(member), icon_url=member.display_avatar.url)
        embed.add_field(name='User ID', value=f'`{member.id}`', inline=True)
        if member.joined_at:
            embed.add_field(name='Joined', value=f'<t:{int(member.joined_at.timestamp())}:R>', inline=True)
        await self.log(member.guild.id, embed)

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        embed = discord.Embed(title='🔨 Member Banned', color=discord.Color.dark_red(), timestamp=datetime.datetime.utcnow())
        embed.set_author(name=str(user), icon_url=user.display_avatar.url)
        embed.add_field(name='User ID', value=f'`{user.id}`', inline=True)
        await self.log(guild.id, embed)

    @commands.Cog.listener()
    async def on_member_unban(self, guild, user):
        embed = discord.Embed(title='✅ Member Unbanned', color=discord.Color.green(), timestamp=datetime.datetime.utcnow())
        embed.set_author(name=str(user), icon_url=user.display_avatar.url)
        embed.add_field(name='User ID', value=f'`{user.id}`', inline=True)
        await self.log(guild.id, embed)

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if before.bot:
            return
        if before.nick != after.nick:
            embed = discord.Embed(title='📝 Nickname Changed', color=discord.Color.blue(), timestamp=datetime.datetime.utcnow())
            embed.set_author(name=str(after), icon_url=after.display_avatar.url)
            embed.add_field(name='Before', value=before.nick or before.name, inline=True)
            embed.add_field(name='After', value=after.nick or after.name, inline=True)
            await self.log(before.guild.id, embed)

        added = set(after.roles) - set(before.roles)
        removed = set(before.roles) - set(after.roles)
        if added:
            embed = discord.Embed(title='➕ Role Added', color=discord.Color.green(), timestamp=datetime.datetime.utcnow())
            embed.set_author(name=str(after), icon_url=after.display_avatar.url)
            embed.add_field(name='Roles Added', value=', '.join(r.mention for r in added))
            await self.log(before.guild.id, embed)
        if removed:
            embed = discord.Embed(title='➖ Role Removed', color=discord.Color.red(), timestamp=datetime.datetime.utcnow())
            embed.set_author(name=str(after), icon_url=after.display_avatar.url)
            embed.add_field(name='Roles Removed', value=', '.join(r.mention for r in removed))
            await self.log(before.guild.id, embed)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member.bot:
            return
        if before.channel is None and after.channel:
            embed = discord.Embed(title='🔊 Joined Voice', color=discord.Color.green(), timestamp=datetime.datetime.utcnow())
            embed.set_author(name=str(member), icon_url=member.display_avatar.url)
            embed.add_field(name='Channel', value=after.channel.mention)
            await self.log(member.guild.id, embed)
        elif before.channel and after.channel is None:
            embed = discord.Embed(title='🔇 Left Voice', color=discord.Color.red(), timestamp=datetime.datetime.utcnow())
            embed.set_author(name=str(member), icon_url=member.display_avatar.url)
            embed.add_field(name='Channel', value=before.channel.mention)
            await self.log(member.guild.id, embed)
        elif before.channel and after.channel and before.channel != after.channel:
            embed = discord.Embed(title='🔁 Moved Voice Channel', color=discord.Color.blue(), timestamp=datetime.datetime.utcnow())
            embed.set_author(name=str(member), icon_url=member.display_avatar.url)
            embed.add_field(name='From', value=before.channel.mention, inline=True)
            embed.add_field(name='To', value=after.channel.mention, inline=True)
            await self.log(member.guild.id, embed)

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        embed = discord.Embed(title='📢 Channel Created', color=discord.Color.green(), timestamp=datetime.datetime.utcnow())
        embed.add_field(name='Name', value=channel.mention if hasattr(channel, 'mention') else channel.name, inline=True)
        embed.add_field(name='Type', value=str(channel.type).title(), inline=True)
        await self.log(channel.guild.id, embed)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        embed = discord.Embed(title='🗑️ Channel Deleted', color=discord.Color.red(), timestamp=datetime.datetime.utcnow())
        embed.add_field(name='Name', value=channel.name, inline=True)
        embed.add_field(name='Type', value=str(channel.type).title(), inline=True)
        await self.log(channel.guild.id, embed)


async def setup(bot):
    await bot.add_cog(ModLogging(bot))
