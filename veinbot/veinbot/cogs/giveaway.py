import discord
from discord.ext import commands
from discord import app_commands
import asyncio, json, datetime, random, re
import logging

logger = logging.getLogger(__name__)

GIVEAWAY_EMOJI = '🎉'


def parse_time(time_str: str) -> int:
    """Parse a time string like 1d2h30m10s into seconds. Returns -1 on failure."""
    pattern = re.compile(r'(?:(\d+)d)?(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?')
    match = pattern.fullmatch(time_str.lower().strip())
    if not match or not any(match.groups()):
        return -1
    days = int(match.group(1) or 0)
    hours = int(match.group(2) or 0)
    minutes = int(match.group(3) or 0)
    seconds = int(match.group(4) or 0)
    total = days * 86400 + hours * 3600 + minutes * 60 + seconds
    return total


def format_time(seconds: int) -> str:
    d, rem = divmod(seconds, 86400)
    h, rem = divmod(rem, 3600)
    m, s = divmod(rem, 60)
    parts = []
    if d: parts.append(f'{d}d')
    if h: parts.append(f'{h}h')
    if m: parts.append(f'{m}m')
    if s: parts.append(f'{s}s')
    return ' '.join(parts) if parts else '0s'


def load_giveaways():
    try:
        with open('database.json', 'r') as f:
            data = json.load(f)
        return data.get('giveaways', {})
    except:
        return {}


def save_giveaways(giveaways):
    try:
        with open('database.json', 'r') as f:
            data = json.load(f)
    except:
        data = {}
    data['giveaways'] = giveaways
    with open('database.json', 'w') as f:
        json.dump(data, f, indent=4)


class Giveaway(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_tasks = {}
        self.bot.loop.create_task(self._restore_giveaways())

    async def _restore_giveaways(self):
        await self.bot.wait_until_ready()
        giveaways = load_giveaways()
        now = datetime.datetime.utcnow().timestamp()
        for msg_id, data in list(giveaways.items()):
            if data.get('ended'):
                continue
            remaining = data['end_time'] - now
            if remaining <= 0:
                # End immediately
                self.bot.loop.create_task(self._end_giveaway(int(msg_id), data))
            else:
                task = self.bot.loop.create_task(
                    self._giveaway_timer(int(msg_id), data, remaining)
                )
                self.active_tasks[int(msg_id)] = task

    async def _giveaway_timer(self, msg_id: int, data: dict, delay: float):
        try:
            await asyncio.sleep(delay)
            giveaways = load_giveaways()
            current = giveaways.get(str(msg_id))
            if current and not current.get('ended'):
                await self._end_giveaway(msg_id, current)
        except asyncio.CancelledError:
            pass

    async def _end_giveaway(self, msg_id: int, data: dict):
        channel = self.bot.get_channel(data['channel_id'])
        if not channel:
            return

        try:
            message = await channel.fetch_message(msg_id)
        except discord.NotFound:
            return

        # Collect valid entrants (reacted with 🎉, not a bot)
        entrants = []
        for reaction in message.reactions:
            if str(reaction.emoji) == GIVEAWAY_EMOJI:
                async for user in reaction.users():
                    if not user.bot and user.id != self.bot.user.id:
                        entrants.append(user)
                break

        winner_count = data.get('winners', 1)
        prize = data['prize']

        # Mark ended in DB
        giveaways = load_giveaways()
        if str(msg_id) in giveaways:
            giveaways[str(msg_id)]['ended'] = True
            giveaways[str(msg_id)]['entrants'] = [u.id for u in entrants]
            save_giveaways(giveaways)

        # Remove timer task
        self.active_tasks.pop(msg_id, None)

        if not entrants:
            embed = discord.Embed(
                title=f'🎉 {prize}',
                description='The giveaway has ended.\n\n**No valid entries were found.**',
                color=discord.Color.dark_gray()
            )
            embed.set_footer(text='Giveaway ended')
            embed.timestamp = datetime.datetime.utcnow()
            await message.edit(embed=embed)
            await channel.send(f'**{prize}** ended with no valid entries.')
            return

        winners = random.sample(entrants, min(winner_count, len(entrants)))
        winner_mentions = ', '.join(w.mention for w in winners)

        embed = discord.Embed(
            title=f'🎉 {prize}',
            color=discord.Color.gold()
        )
        embed.description = (
            f'**Winner{"s" if len(winners) > 1 else ""}:** {winner_mentions}\n\n'
            f'**Entries:** {len(entrants)}'
        )
        embed.set_footer(text='Giveaway ended')
        embed.timestamp = datetime.datetime.utcnow()
        await message.edit(embed=embed)

        await channel.send(
            f'🎉 Congratulations {winner_mentions}! You won **{prize}**!'
        )

    @commands.hybrid_command(name='gstart', description='Start a giveaway')
    @commands.has_permissions(manage_guild=True)
    @app_commands.describe(
        time='Duration (e.g. 1h, 30m, 1d)',
        winners='Number of winners',
        prize='What you are giving away'
    )
    async def gstart(self, ctx, time: str, winners: int, *, prize: str):
        duration = parse_time(time)
        if duration <= 0:
            return await ctx.send(
                '❌ Invalid time format. Use combinations like `30s`, `5m`, `2h`, `1d`, `1h30m`.'
            )
        if winners < 1:
            return await ctx.send('❌ There must be at least 1 winner.')
        if winners > 20:
            return await ctx.send('❌ Maximum 20 winners per giveaway.')

        end_time = datetime.datetime.utcnow() + datetime.timedelta(seconds=duration)
        end_ts = int(end_time.timestamp())

        embed = discord.Embed(
            title=f'🎉 {prize}',
            color=discord.Color.blue()
        )
        embed.description = (
            f'React with 🎉 to enter!\n\n'
            f'**Ends:** <t:{end_ts}:R> (<t:{end_ts}:f>)\n'
            f'**Winners:** {winners}\n'
            f'**Hosted by:** {ctx.author.mention}'
        )
        embed.set_footer(text='Giveaway • React with 🎉 to enter')
        embed.timestamp = end_time

        try:
            await ctx.defer()
        except:
            pass

        msg = await ctx.channel.send(embed=embed)
        await msg.add_reaction(GIVEAWAY_EMOJI)

        data = {
            'guild_id': ctx.guild.id,
            'channel_id': ctx.channel.id,
            'host_id': ctx.author.id,
            'prize': prize,
            'winners': winners,
            'end_time': end_time.timestamp(),
            'ended': False,
            'message_id': msg.id
        }

        giveaways = load_giveaways()
        giveaways[str(msg.id)] = data
        save_giveaways(giveaways)

        task = self.bot.loop.create_task(
            self._giveaway_timer(msg.id, data, duration)
        )
        self.active_tasks[msg.id] = task

        confirm = discord.Embed(
            description=f'✅ Giveaway started in {ctx.channel.mention}! Ends in **{format_time(duration)}**.',
            color=discord.Color.green()
        )
        try:
            await ctx.send(embed=confirm, ephemeral=True)
        except:
            pass

    @commands.hybrid_command(name='gend', description='End a giveaway early')
    @commands.has_permissions(manage_guild=True)
    @app_commands.describe(message_id='The message ID of the giveaway')
    async def gend(self, ctx, message_id: str):
        giveaways = load_giveaways()
        data = giveaways.get(message_id)

        if not data:
            return await ctx.send('❌ No active giveaway found with that message ID.')
        if data.get('ended'):
            return await ctx.send('❌ That giveaway has already ended.')
        if data['guild_id'] != ctx.guild.id:
            return await ctx.send('❌ That giveaway is not in this server.')

        # Cancel the scheduled task
        task = self.active_tasks.pop(int(message_id), None)
        if task:
            task.cancel()

        await self._end_giveaway(int(message_id), data)
        await ctx.send('✅ Giveaway ended.', ephemeral=True)

    @commands.hybrid_command(name='greroll', description='Reroll the winner of a giveaway')
    @commands.has_permissions(manage_guild=True)
    @app_commands.describe(message_id='The message ID of the finished giveaway')
    async def greroll(self, ctx, message_id: str):
        giveaways = load_giveaways()
        data = giveaways.get(message_id)

        if not data:
            return await ctx.send('❌ No giveaway found with that message ID.')
        if not data.get('ended'):
            return await ctx.send('❌ That giveaway has not ended yet. Use `.gend` first.')
        if data['guild_id'] != ctx.guild.id:
            return await ctx.send('❌ That giveaway is not in this server.')

        channel = self.bot.get_channel(data['channel_id'])
        if not channel:
            return await ctx.send('❌ Cannot find the original giveaway channel.')

        try:
            message = await channel.fetch_message(int(message_id))
        except discord.NotFound:
            return await ctx.send('❌ Cannot find the original giveaway message.')

        entrants = []
        for reaction in message.reactions:
            if str(reaction.emoji) == GIVEAWAY_EMOJI:
                async for user in reaction.users():
                    if not user.bot and user.id != self.bot.user.id:
                        entrants.append(user)
                break

        if not entrants:
            return await ctx.send('❌ No valid entries to reroll from.')

        winner_count = data.get('winners', 1)
        winners = random.sample(entrants, min(winner_count, len(entrants)))
        winner_mentions = ', '.join(w.mention for w in winners)

        embed = discord.Embed(
            title='🎉 Giveaway Rerolled',
            description=f'New winner{"s" if len(winners) > 1 else ""}: {winner_mentions}',
            color=discord.Color.gold()
        )
        embed.set_footer(text=f'Rerolled by {ctx.author.name}')
        await ctx.send(embed=embed)
        await channel.send(
            f'🎉 The **{data["prize"]}** giveaway has been rerolled! New winner{"s" if len(winners) > 1 else ""}: {winner_mentions}!'
        )

    @commands.hybrid_command(name='glist', description='View all active giveaways in this server')
    async def glist(self, ctx):
        giveaways = load_giveaways()
        active = [
            (mid, d) for mid, d in giveaways.items()
            if d['guild_id'] == ctx.guild.id and not d.get('ended')
        ]

        if not active:
            return await ctx.send('There are no active giveaways in this server right now.')

        embed = discord.Embed(
            title='🎉 Active Giveaways',
            color=discord.Color.blue()
        )
        for mid, d in active:
            end_ts = int(d['end_time'])
            channel = self.bot.get_channel(d['channel_id'])
            ch_mention = channel.mention if channel else 'Unknown channel'
            embed.add_field(
                name=d['prize'],
                value=(
                    f'Channel: {ch_mention}\n'
                    f'Ends: <t:{end_ts}:R>\n'
                    f'Winners: {d["winners"]}\n'
                    f'[Jump to message](https://discord.com/channels/{d["guild_id"]}/{d["channel_id"]}/{mid})'
                ),
                inline=False
            )
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Giveaway(bot))
