import discord
from discord.ext import commands
from discord import app_commands
import json, datetime, asyncio
import logging

logger = logging.getLogger(__name__)


class AntiNuke(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.whitelist = {}
        self.action_log = {}
        self.load_data()

    def load_data(self):
        try:
            with open('database.json', 'r') as f:
                data = json.load(f)
            self.whitelist = data.get('antinuke_whitelist', {})
        except:
            self.whitelist = {}

    def save_data(self):
        try:
            with open('database.json', 'r') as f:
                data = json.load(f)
        except:
            data = {}
        data['antinuke_whitelist'] = self.whitelist
        with open('database.json', 'w') as f:
            json.dump(data, f, indent=4)

    def is_whitelisted(self, guild_id, user_id):
        return str(user_id) in self.whitelist.get(str(guild_id), [])

    def is_enabled(self, guild_id):
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
            return config.get(str(guild_id), {}).get('antinuke_enabled', True)
        except:
            return True

    def log_action(self, guild_id, user_id, action):
        key = f'{guild_id}:{user_id}'
        if key not in self.action_log:
            self.action_log[key] = []
        now = datetime.datetime.utcnow()
        self.action_log[key].append({'action': action, 'time': now})
        cutoff = now - datetime.timedelta(seconds=10)
        self.action_log[key] = [e for e in self.action_log[key] if e['time'] > cutoff]
        return len(self.action_log[key])

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        if not self.is_enabled(channel.guild.id):
            return
        async for entry in channel.guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_delete):
            if entry.user.bot or self.is_whitelisted(channel.guild.id, entry.user.id):
                return
            count = self.log_action(channel.guild.id, entry.user.id, 'channel_delete')
            if count >= 3:
                await self._punish(channel.guild, entry.user, 'Mass channel deletion detected')

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        if not self.is_enabled(role.guild.id):
            return
        async for entry in role.guild.audit_logs(limit=1, action=discord.AuditLogAction.role_delete):
            if entry.user.bot or self.is_whitelisted(role.guild.id, entry.user.id):
                return
            count = self.log_action(role.guild.id, entry.user.id, 'role_delete')
            if count >= 3:
                await self._punish(role.guild, entry.user, 'Mass role deletion detected')

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        if not self.is_enabled(guild.id):
            return
        async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.ban):
            if entry.user.bot or self.is_whitelisted(guild.id, entry.user.id):
                return
            count = self.log_action(guild.id, entry.user.id, 'ban')
            if count >= 3:
                await self._punish(guild, entry.user, 'Mass ban detected')

    async def _punish(self, guild, user, reason):
        try:
            member = guild.get_member(user.id)
            if member:
                await member.ban(reason=f'Anti-Nuke: {reason}')
                logger.warning(f'Anti-Nuke banned {user} in {guild.name}: {reason}')
        except Exception as e:
            logger.error(f'Anti-Nuke punish error: {e}')

    @commands.hybrid_command(name='antinuke', description='Enable or disable the Anti-Nuke system')
    @commands.has_permissions(administrator=True)
    @app_commands.describe(enabled='Enable or disable anti-nuke')
    async def antinuke(self, ctx, enabled: bool = True):
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
        except:
            config = {}
        config.setdefault(str(ctx.guild.id), {})['antinuke_enabled'] = enabled
        with open('config.json', 'w') as f:
            json.dump(config, f, indent=4)
        status = 'enabled' if enabled else 'disabled'
        embed = discord.Embed(
            title='🔒 Anti-Nuke',
            description=f'The Anti-Nuke system has been **{status}**.',
            color=discord.Color.green() if enabled else discord.Color.red()
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(name='whitelist', description='Whitelist a user from Anti-Nuke detection')
    @commands.has_permissions(administrator=True)
    @app_commands.describe(member='Member to whitelist')
    async def whitelist_add(self, ctx, member: discord.Member):
        key = str(ctx.guild.id)
        if key not in self.whitelist:
            self.whitelist[key] = []
        uid = str(member.id)
        if uid not in self.whitelist[key]:
            self.whitelist[key].append(uid)
            self.save_data()
        await ctx.send(f'✅ {member.mention} has been whitelisted from Anti-Nuke detection.')

    @commands.hybrid_command(name='unwhitelist', description='Remove a user from the Anti-Nuke whitelist')
    @commands.has_permissions(administrator=True)
    @app_commands.describe(member='Member to remove')
    async def whitelist_remove(self, ctx, member: discord.Member):
        key = str(ctx.guild.id)
        uid = str(member.id)
        if key in self.whitelist and uid in self.whitelist[key]:
            self.whitelist[key].remove(uid)
            self.save_data()
            await ctx.send(f'✅ Removed {member.mention} from the Anti-Nuke whitelist.')
        else:
            await ctx.send('❌ That user is not on the whitelist.')

    @commands.hybrid_command(name='whitelistlist', description='View all Anti-Nuke whitelisted users')
    @commands.has_permissions(administrator=True)
    async def whitelist_list(self, ctx):
        key = str(ctx.guild.id)
        ids = self.whitelist.get(key, [])
        if not ids:
            return await ctx.send('No users are currently whitelisted.')
        members = [ctx.guild.get_member(int(i)) for i in ids]
        names = [m.mention if m else f'<@{i}>' for m, i in zip(members, ids)]
        embed = discord.Embed(title='🔒 Anti-Nuke Whitelist', description='\n'.join(names), color=discord.Color.blue())
        embed.set_footer(text=f'{len(ids)} user(s) whitelisted')
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(AntiNuke(bot))
