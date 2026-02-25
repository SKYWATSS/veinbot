import discord
from discord.ext import commands
from discord import app_commands
import json, random, datetime
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def xp_for_level(level: int) -> int:
    return int(100 * (level ** 1.5))


class Leveling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.xp_data = {}
        self.cooldowns = {}
        self.load_data()

    def load_data(self):
        try:
            with open('database.json', 'r') as f:
                data = json.load(f)
            self.xp_data = data.get('xp', {})
        except:
            self.xp_data = {}

    def save_data(self):
        try:
            with open('database.json', 'r') as f:
                data = json.load(f)
        except:
            data = {}
        data['xp'] = self.xp_data
        with open('database.json', 'w') as f:
            json.dump(data, f, indent=4)

    def get_user(self, guild_id, user_id):
        key = f'{guild_id}:{user_id}'
        if key not in self.xp_data:
            self.xp_data[key] = {'xp': 0, 'level': 0, 'messages': 0}
        return self.xp_data[key]

    def get_multiplier(self, guild_id):
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
            return config.get(str(guild_id), {}).get('xp_multiplier', 1)
        except:
            return 1

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return
        uid = message.author.id
        now = datetime.datetime.utcnow()
        cd_key = f'{message.guild.id}:{uid}'
        last = self.cooldowns.get(cd_key)
        if last and (now - last).total_seconds() < 60:
            return
        self.cooldowns[cd_key] = now

        user = self.get_user(message.guild.id, uid)
        mult = self.get_multiplier(message.guild.id)
        gain = int(random.randint(15, 25) * mult)
        user['xp'] += gain
        user['messages'] = user.get('messages', 0) + 1

        needed = xp_for_level(user['level'] + 1)
        if user['xp'] >= needed:
            user['level'] += 1
            user['xp'] -= needed
            self.save_data()
            embed = discord.Embed(
                title='🎉 Level Up!',
                description=f'{message.author.mention} reached **Level {user["level"]}**!',
                color=discord.Color.gold()
            )
            await message.channel.send(embed=embed)
            await self._check_role_rewards(message.guild, message.author, user['level'])
        else:
            self.save_data()

    async def _check_role_rewards(self, guild, member, level):
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
            rewards = config.get(str(guild.id), {}).get('level_roles', {})
            role_id = rewards.get(str(level))
            if role_id:
                role = guild.get_role(role_id)
                if role:
                    await member.add_roles(role)
        except:
            pass

    @commands.hybrid_command(name='rank', description='View your or another member\'s rank card')
    @app_commands.describe(member='Member to check (defaults to yourself)')
    async def rank(self, ctx, member: Optional[discord.Member] = None):
        member = member or ctx.author
        user = self.get_user(ctx.guild.id, member.id)
        level = user['level']
        xp = user['xp']
        needed = xp_for_level(level + 1)
        progress = int((xp / needed) * 20) if needed else 0
        bar = '█' * progress + '░' * (20 - progress)

        guild_id = str(ctx.guild.id)
        sorted_users = sorted(
            [(k, v) for k, v in self.xp_data.items() if k.startswith(f'{guild_id}:')],
            key=lambda x: (x[1]['level'], x[1]['xp']),
            reverse=True
        )
        rank_pos = next(
            (i + 1 for i, (k, _) in enumerate(sorted_users) if k == f'{guild_id}:{member.id}'),
            '?'
        )

        embed = discord.Embed(
            title=f'📊 {member.display_name}',
            color=member.color if member.color.value else discord.Color.blue()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name='Level', value=f'**{level}**', inline=True)
        embed.add_field(name='XP', value=f'**{xp:,}** / {needed:,}', inline=True)
        embed.add_field(name='Rank', value=f'**#{rank_pos}**', inline=True)
        embed.add_field(name='Progress', value=f'`{bar}` {int((xp/needed)*100)}%', inline=False)
        embed.add_field(name='Messages', value=f'**{user.get("messages", 0):,}**', inline=True)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name='leaderboard', description='View the XP leaderboard')
    async def leaderboard(self, ctx):
        guild_id = str(ctx.guild.id)
        sorted_users = sorted(
            [(k, v) for k, v in self.xp_data.items() if k.startswith(f'{guild_id}:')],
            key=lambda x: (x[1]['level'], x[1]['xp']),
            reverse=True
        )[:10]

        embed = discord.Embed(title='🏆 XP Leaderboard', color=discord.Color.gold())
        medals = ['🥇', '🥈', '🥉']
        if not sorted_users:
            embed.description = 'No data yet. Start chatting to earn XP!'
        else:
            for i, (key, data) in enumerate(sorted_users):
                uid = int(key.split(':')[1])
                m = ctx.guild.get_member(uid)
                name = m.display_name if m else f'User {uid}'
                medal = medals[i] if i < 3 else f'{i + 1}.'
                embed.add_field(
                    name=f'{medal} {name}',
                    value=f'Level **{data["level"]}** • {data["xp"]:,} XP',
                    inline=False
                )
        await ctx.send(embed=embed)

    @commands.hybrid_command(name='setxp', description='Set XP for a member (Admin)')
    @commands.has_permissions(administrator=True)
    @app_commands.describe(member='Member', amount='XP amount')
    async def setxp(self, ctx, member: discord.Member, amount: int):
        user = self.get_user(ctx.guild.id, member.id)
        user['xp'] = amount
        self.save_data()
        await ctx.send(f'✅ Set {member.mention}\'s XP to **{amount:,}**.')

    @commands.hybrid_command(name='setlevel', description='Set level for a member (Admin)')
    @commands.has_permissions(administrator=True)
    @app_commands.describe(member='Member', level='Target level')
    async def setlevel(self, ctx, member: discord.Member, level: int):
        user = self.get_user(ctx.guild.id, member.id)
        user['level'] = level
        user['xp'] = 0
        self.save_data()
        await ctx.send(f'✅ Set {member.mention}\'s level to **{level}**.')

    @commands.hybrid_command(name='resetxp', description='Reset XP and level for a member (Admin)')
    @commands.has_permissions(administrator=True)
    @app_commands.describe(member='Member to reset')
    async def resetxp(self, ctx, member: discord.Member):
        key = f'{ctx.guild.id}:{member.id}'
        self.xp_data[key] = {'xp': 0, 'level': 0, 'messages': 0}
        self.save_data()
        await ctx.send(f'✅ Reset XP and level for {member.mention}.')

    @commands.hybrid_command(name='xpmultiplier', description='Set the server XP multiplier (Admin)')
    @commands.has_permissions(administrator=True)
    @app_commands.describe(multiplier='Multiplier value (e.g. 2 for double XP)')
    async def xpmultiplier(self, ctx, multiplier: float):
        if multiplier <= 0:
            return await ctx.send('❌ Multiplier must be greater than 0.')
        if multiplier > 10:
            return await ctx.send('❌ Maximum multiplier is 10x.')
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
        except:
            config = {}
        config.setdefault(str(ctx.guild.id), {})['xp_multiplier'] = multiplier
        with open('config.json', 'w') as f:
            json.dump(config, f, indent=4)
        await ctx.send(f'✅ XP multiplier set to **{multiplier}x**.')


async def setup(bot):
    await bot.add_cog(Leveling(bot))
