import discord
from discord.ext import commands
from discord import app_commands
import json
import logging

logger = logging.getLogger(__name__)


class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_config(self, guild_id):
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
            return config.get(str(guild_id), {})
        except:
            return {}

    def save_config(self, guild_id, guild_config):
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
        except:
            config = {}
        config[str(guild_id)] = guild_config
        with open('config.json', 'w') as f:
            json.dump(config, f, indent=4)

    def format_message(self, msg, member):
        return (
            msg.replace('{mention}', member.mention)
               .replace('{name}', member.display_name)
               .replace('{server}', member.guild.name)
               .replace('{count}', str(member.guild.member_count))
        )

    @commands.Cog.listener()
    async def on_member_join(self, member):
        gc = self.get_config(member.guild.id)

        ch_id = gc.get('welcome_channel')
        if ch_id:
            channel = member.guild.get_channel(ch_id)
            if channel:
                msg = gc.get('welcome_message', 'Welcome {mention} to **{server}**! You are member #{count}.')
                text = self.format_message(msg, member)
                embed = discord.Embed(description=text, color=discord.Color.green())
                embed.set_thumbnail(url=member.display_avatar.url)
                embed.set_footer(text=member.guild.name, icon_url=member.guild.icon.url if member.guild.icon else None)
                try:
                    await channel.send(embed=embed)
                except:
                    pass

        ar_id = gc.get('autorole')
        if ar_id:
            role = member.guild.get_role(ar_id)
            if role:
                try:
                    await member.add_roles(role, reason='Auto-role on join')
                except:
                    pass

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        gc = self.get_config(member.guild.id)
        ch_id = gc.get('leave_channel')
        if ch_id:
            channel = member.guild.get_channel(ch_id)
            if channel:
                msg = gc.get('leave_message', '**{name}** has left the server. We now have {count} members.')
                text = self.format_message(msg, member)
                embed = discord.Embed(description=text, color=discord.Color.red())
                embed.set_thumbnail(url=member.display_avatar.url)
                try:
                    await channel.send(embed=embed)
                except:
                    pass

    @commands.hybrid_command(name='setwelcome', description='Set the welcome channel and optional message')
    @commands.has_permissions(administrator=True)
    @app_commands.describe(
        channel='Channel to send welcome messages in',
        message='Custom message. Use: {mention} {name} {server} {count}'
    )
    async def setwelcome(self, ctx, channel: discord.TextChannel, *, message: str = None):
        gc = self.get_config(ctx.guild.id)
        gc['welcome_channel'] = channel.id
        if message:
            gc['welcome_message'] = message
        self.save_config(ctx.guild.id, gc)
        await ctx.send(f'✅ Welcome messages will be sent to {channel.mention}.')

    @commands.hybrid_command(name='setleave', description='Set the leave channel and optional message')
    @commands.has_permissions(administrator=True)
    @app_commands.describe(
        channel='Channel to send leave messages in',
        message='Custom message. Use: {mention} {name} {server} {count}'
    )
    async def setleave(self, ctx, channel: discord.TextChannel, *, message: str = None):
        gc = self.get_config(ctx.guild.id)
        gc['leave_channel'] = channel.id
        if message:
            gc['leave_message'] = message
        self.save_config(ctx.guild.id, gc)
        await ctx.send(f'✅ Leave messages will be sent to {channel.mention}.')

    @commands.hybrid_command(name='setautorole', description='Automatically assign a role to new members')
    @commands.has_permissions(administrator=True)
    @app_commands.describe(role='Role to assign to new members')
    async def setautorole(self, ctx, role: discord.Role):
        gc = self.get_config(ctx.guild.id)
        gc['autorole'] = role.id
        self.save_config(ctx.guild.id, gc)
        await ctx.send(f'✅ New members will automatically receive {role.mention}.')

    @commands.hybrid_command(name='testwelcome', description='Preview the welcome message')
    @commands.has_permissions(administrator=True)
    async def testwelcome(self, ctx):
        await self.on_member_join(ctx.author)
        await ctx.send('✅ Welcome message sent as a preview.', ephemeral=True)


async def setup(bot):
    await bot.add_cog(Welcome(bot))
