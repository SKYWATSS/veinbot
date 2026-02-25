import discord
from discord.ext import commands
from discord import app_commands
import json, re, time
import logging

logger = logging.getLogger(__name__)


class Filter(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.spam_tracker = {}

    def get_filters(self, guild_id):
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
            return config.get(str(guild_id), {}).get('filters', {})
        except:
            return {}

    def update_filter(self, guild_id, key, value):
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
        except:
            config = {}
        config.setdefault(str(guild_id), {}).setdefault('filters', {})[key] = value
        with open('config.json', 'w') as f:
            json.dump(config, f, indent=4)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return
        if message.author.guild_permissions.manage_messages:
            return
        filters = self.get_filters(message.guild.id)

        if filters.get('spam'):
            uid = message.author.id
            cid = message.channel.id
            key = f'{cid}:{uid}'
            now = time.time()
            self.spam_tracker.setdefault(key, [])
            self.spam_tracker[key] = [t for t in self.spam_tracker[key] if now - t < 5]
            self.spam_tracker[key].append(now)
            if len(self.spam_tracker[key]) >= 5:
                await message.delete()
                await message.channel.send(
                    f'⚠️ {message.author.mention} — slow down!',
                    delete_after=4
                )
                return

        if filters.get('links'):
            if re.search(r'https?://', message.content):
                await message.delete()
                await message.channel.send(
                    f'⚠️ {message.author.mention} — links are not allowed here.',
                    delete_after=4
                )
                return

        if filters.get('invites'):
            if re.search(r'discord\.gg/\w+', message.content, re.IGNORECASE):
                await message.delete()
                await message.channel.send(
                    f'⚠️ {message.author.mention} — Discord invites are not allowed.',
                    delete_after=4
                )
                return

        if filters.get('caps'):
            text = message.content
            if len(text) > 10 and sum(c.isupper() for c in text if c.isalpha()) / max(sum(c.isalpha() for c in text), 1) > 0.7:
                await message.delete()
                await message.channel.send(
                    f'⚠️ {message.author.mention} — excessive caps are not allowed.',
                    delete_after=4
                )
                return

        custom_words = filters.get('words', [])
        if custom_words:
            content_lower = message.content.lower()
            for word in custom_words:
                if word.lower() in content_lower:
                    await message.delete()
                    await message.channel.send(
                        f'⚠️ {message.author.mention} — that word is not allowed.',
                        delete_after=4
                    )
                    return

    @commands.hybrid_group(name='filter', description='View and manage message filters')
    @commands.has_permissions(manage_guild=True)
    async def filter_group(self, ctx):
        if ctx.invoked_subcommand is None:
            filters = self.get_filters(ctx.guild.id)
            embed = discord.Embed(title='🚫 Message Filters', color=discord.Color.blue())
            for k in ['spam', 'links', 'invites', 'caps']:
                status = '✅ Enabled' if filters.get(k) else '❌ Disabled'
                embed.add_field(name=k.title(), value=status, inline=True)
            words = filters.get('words', [])
            embed.add_field(name='Banned Words', value=f'{len(words)} word(s)', inline=True)
            embed.set_footer(text='Use .filter <type> true/false to toggle')
            await ctx.send(embed=embed)

    @filter_group.command(name='spam', description='Toggle spam detection')
    @app_commands.describe(enabled='true to enable, false to disable')
    async def filter_spam(self, ctx, enabled: bool):
        self.update_filter(ctx.guild.id, 'spam', enabled)
        await ctx.send(f'✅ Spam filter {"enabled" if enabled else "disabled"}.')

    @filter_group.command(name='links', description='Toggle link blocking')
    @app_commands.describe(enabled='true to enable, false to disable')
    async def filter_links(self, ctx, enabled: bool):
        self.update_filter(ctx.guild.id, 'links', enabled)
        await ctx.send(f'✅ Link filter {"enabled" if enabled else "disabled"}.')

    @filter_group.command(name='invites', description='Toggle invite link blocking')
    @app_commands.describe(enabled='true to enable, false to disable')
    async def filter_invites(self, ctx, enabled: bool):
        self.update_filter(ctx.guild.id, 'invites', enabled)
        await ctx.send(f'✅ Invite filter {"enabled" if enabled else "disabled"}.')

    @filter_group.command(name='caps', description='Toggle excessive caps filter')
    @app_commands.describe(enabled='true to enable, false to disable')
    async def filter_caps(self, ctx, enabled: bool):
        self.update_filter(ctx.guild.id, 'caps', enabled)
        await ctx.send(f'✅ Caps filter {"enabled" if enabled else "disabled"}.')

    @filter_group.command(name='addword', description='Add a word to the banned list')
    @app_commands.describe(word='Word to ban')
    async def filter_addword(self, ctx, word: str):
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
        except:
            config = {}
        gid = str(ctx.guild.id)
        config.setdefault(gid, {}).setdefault('filters', {}).setdefault('words', [])
        if word.lower() not in config[gid]['filters']['words']:
            config[gid]['filters']['words'].append(word.lower())
        with open('config.json', 'w') as f:
            json.dump(config, f, indent=4)
        await ctx.send(f'✅ Added `{word}` to the banned word list.')

    @filter_group.command(name='removeword', description='Remove a word from the banned list')
    @app_commands.describe(word='Word to remove')
    async def filter_removeword(self, ctx, word: str):
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
        except:
            config = {}
        gid = str(ctx.guild.id)
        words = config.get(gid, {}).get('filters', {}).get('words', [])
        if word.lower() in words:
            words.remove(word.lower())
            with open('config.json', 'w') as f:
                json.dump(config, f, indent=4)
            await ctx.send(f'✅ Removed `{word}` from the banned word list.')
        else:
            await ctx.send('❌ That word is not on the list.')


async def setup(bot):
    await bot.add_cog(Filter(bot))
