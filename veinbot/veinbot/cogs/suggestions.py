import discord
from discord.ext import commands
from discord import app_commands
import json, datetime
import logging

logger = logging.getLogger(__name__)


class Suggestions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.suggestions = {}
        self.counter = 0
        self.load_data()

    def load_data(self):
        try:
            with open('database.json', 'r') as f:
                data = json.load(f)
            self.suggestions = data.get('suggestions', {})
            for gdata in self.suggestions.values():
                for sid in gdata.keys():
                    self.counter = max(self.counter, int(sid))
        except:
            self.suggestions = {}

    def save_data(self):
        try:
            with open('database.json', 'r') as f:
                data = json.load(f)
        except:
            data = {}
        data['suggestions'] = self.suggestions
        with open('database.json', 'w') as f:
            json.dump(data, f, indent=4)

    def get_sug_channel(self, guild_id):
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
            cid = config.get(str(guild_id), {}).get('suggestions_channel')
            return self.bot.get_channel(cid) if cid else None
        except:
            return None

    @commands.hybrid_command(name='suggest', description='Submit a suggestion to the server')
    @app_commands.describe(suggestion='Your suggestion')
    async def suggest(self, ctx, *, suggestion: str):
        channel = self.get_sug_channel(ctx.guild.id)
        if not channel:
            return await ctx.send('❌ No suggestions channel has been set up. Ask an admin to run `.suggestchannel #channel`.')
        self.counter += 1
        sid = self.counter

        embed = discord.Embed(
            title=f'Suggestion #{sid}',
            description=suggestion,
            color=discord.Color.blue(),
            timestamp=datetime.datetime.utcnow()
        )
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)
        embed.add_field(name='Status', value='⏳ Awaiting Review', inline=False)
        embed.set_footer(text=f'Submitted by {ctx.author.name} ({ctx.author.id})')

        msg = await channel.send(embed=embed)
        await msg.add_reaction('✅')
        await msg.add_reaction('❌')

        gid = str(ctx.guild.id)
        self.suggestions.setdefault(gid, {})[str(sid)] = {
            'author': ctx.author.id,
            'content': suggestion,
            'message_id': msg.id,
            'channel_id': channel.id,
            'status': 'pending',
            'created_at': str(datetime.datetime.utcnow())
        }
        self.save_data()
        await ctx.send(f'✅ Your suggestion has been submitted as **#{sid}** in {channel.mention}.', ephemeral=True)

    @commands.hybrid_command(name='approve', description='Approve a suggestion')
    @commands.has_permissions(manage_messages=True)
    @app_commands.describe(suggestion_id='The suggestion number', reason='Reason for approving')
    async def approve(self, ctx, suggestion_id: int, *, reason: str = 'No reason provided'):
        gid = str(ctx.guild.id)
        sid = str(suggestion_id)
        if gid not in self.suggestions or sid not in self.suggestions[gid]:
            return await ctx.send('❌ Suggestion not found.')
        sug = self.suggestions[gid][sid]
        ch = self.bot.get_channel(sug['channel_id'])
        if ch:
            try:
                msg = await ch.fetch_message(sug['message_id'])
                embed = msg.embeds[0]
                embed.color = discord.Color.green()
                embed.set_field_at(0, name='Status', value='✅ Approved', inline=False)
                embed.add_field(name='Approved By', value=ctx.author.mention, inline=True)
                embed.add_field(name='Reason', value=reason, inline=True)
                await msg.edit(embed=embed)
            except:
                pass
        sug.update({
            'status': 'approved',
            'approved_by': ctx.author.id,
            'approved_reason': reason,
            'approved_at': str(datetime.datetime.utcnow())
        })
        self.save_data()
        await ctx.send(f'✅ Suggestion #{suggestion_id} approved.')
        try:
            author = await self.bot.fetch_user(sug['author'])
            e = discord.Embed(
                title='Your Suggestion Was Approved',
                description=f'**{ctx.guild.name}** approved your suggestion.',
                color=discord.Color.green()
            )
            e.add_field(name='Suggestion', value=sug['content'][:512], inline=False)
            e.add_field(name='Reason', value=reason, inline=False)
            await author.send(embed=e)
        except:
            pass

    @commands.hybrid_command(name='deny', description='Deny a suggestion')
    @commands.has_permissions(manage_messages=True)
    @app_commands.describe(suggestion_id='The suggestion number', reason='Reason for denying')
    async def deny(self, ctx, suggestion_id: int, *, reason: str = 'No reason provided'):
        gid = str(ctx.guild.id)
        sid = str(suggestion_id)
        if gid not in self.suggestions or sid not in self.suggestions[gid]:
            return await ctx.send('❌ Suggestion not found.')
        sug = self.suggestions[gid][sid]
        ch = self.bot.get_channel(sug['channel_id'])
        if ch:
            try:
                msg = await ch.fetch_message(sug['message_id'])
                embed = msg.embeds[0]
                embed.color = discord.Color.red()
                embed.set_field_at(0, name='Status', value='❌ Denied', inline=False)
                embed.add_field(name='Denied By', value=ctx.author.mention, inline=True)
                embed.add_field(name='Reason', value=reason, inline=True)
                await msg.edit(embed=embed)
            except:
                pass
        sug.update({
            'status': 'denied',
            'denied_by': ctx.author.id,
            'denied_reason': reason,
            'denied_at': str(datetime.datetime.utcnow())
        })
        self.save_data()
        await ctx.send(f'✅ Suggestion #{suggestion_id} denied.')
        try:
            author = await self.bot.fetch_user(sug['author'])
            e = discord.Embed(
                title='Your Suggestion Was Denied',
                description=f'**{ctx.guild.name}** denied your suggestion.',
                color=discord.Color.red()
            )
            e.add_field(name='Suggestion', value=sug['content'][:512], inline=False)
            e.add_field(name='Reason', value=reason, inline=False)
            await author.send(embed=e)
        except:
            pass

    @commands.hybrid_command(name='suggestions', description='Browse suggestions by status')
    @app_commands.describe(status='Filter: all, pending, approved, or denied')
    async def list_suggestions(self, ctx, status: str = 'all'):
        gid = str(ctx.guild.id)
        all_sug = self.suggestions.get(gid, {})
        filtered = {k: v for k, v in all_sug.items() if status == 'all' or v['status'] == status.lower()}
        if not filtered:
            return await ctx.send(f'No **{status}** suggestions found.')

        embed = discord.Embed(
            title=f'Suggestions — {status.title()}',
            color=discord.Color.blue()
        )
        emoji_map = {'pending': '⏳', 'approved': '✅', 'denied': '❌'}
        for sid, sug in list(sorted(filtered.items(), key=lambda x: int(x[0]), reverse=True))[:10]:
            em = emoji_map.get(sug['status'], '❓')
            short = sug['content'][:80] + ('...' if len(sug['content']) > 80 else '')
            embed.add_field(
                name=f'{em} #{sid}',
                value=f'{short}\n*by <@{sug["author"]}>*',
                inline=False
            )
        embed.set_footer(text=f'Showing {min(10, len(filtered))} of {len(filtered)} suggestions')
        await ctx.send(embed=embed)

    @commands.hybrid_command(name='suggestchannel', description='Set the suggestions channel')
    @commands.has_permissions(administrator=True)
    @app_commands.describe(channel='Channel for suggestions')
    async def suggestchannel(self, ctx, channel: discord.TextChannel):
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
        except:
            config = {}
        config.setdefault(str(ctx.guild.id), {})['suggestions_channel'] = channel.id
        with open('config.json', 'w') as f:
            json.dump(config, f, indent=4)
        await ctx.send(f'✅ Suggestions will be posted in {channel.mention}.')


async def setup(bot):
    await bot.add_cog(Suggestions(bot))
