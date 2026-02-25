import discord
from discord.ext import commands
from discord import app_commands
import random, datetime, aiohttp
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name='8ball', description='Ask the magic 8 ball a question')
    @app_commands.describe(question='Your question for the 8 ball')
    async def eight_ball(self, ctx, *, question: str):
        positive = [
            'It is certain.', 'It is decidedly so.', 'Without a doubt.',
            'Yes, definitely.', 'You may rely on it.', 'As I see it, yes.',
            'Most likely.', 'Outlook good.', 'Yes.', 'Signs point to yes.'
        ]
        neutral = [
            'Reply hazy, try again.', 'Ask again later.',
            'Better not tell you now.', 'Cannot predict now.',
            'Concentrate and ask again.'
        ]
        negative = [
            "Don't count on it.", 'My reply is no.',
            'My sources say no.', 'Outlook not so good.', 'Very doubtful.'
        ]
        all_responses = positive + neutral + negative
        answer = random.choice(all_responses)

        if answer in positive:
            color = discord.Color.green()
        elif answer in neutral:
            color = discord.Color.orange()
        else:
            color = discord.Color.red()

        embed = discord.Embed(title='🎱 Magic 8 Ball', color=color)
        embed.add_field(name='Question', value=question, inline=False)
        embed.add_field(name='Answer', value=f'*{answer}*', inline=False)
        embed.set_footer(text=f'Asked by {ctx.author.name}', icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name='coinflip', description='Flip a coin')
    async def coinflip(self, ctx):
        result = random.choice(['Heads', 'Tails'])
        embed = discord.Embed(
            title='🪙 Coin Flip',
            description=f'The coin landed on **{result}**!',
            color=discord.Color.gold()
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(name='dice', description='Roll a dice')
    @app_commands.describe(sides='Number of sides (default: 6)')
    async def dice(self, ctx, sides: int = 6):
        if sides < 2:
            return await ctx.send('❌ A dice must have at least 2 sides.')
        if sides > 10000:
            return await ctx.send('❌ Maximum 10,000 sides.')
        result = random.randint(1, sides)
        embed = discord.Embed(
            title='🎲 Dice Roll',
            description=f'You rolled a **{result}** on a d{sides}.',
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(name='rps', description='Play Rock Paper Scissors against the bot')
    @app_commands.describe(choice='Your choice: rock, paper, or scissors')
    async def rps(self, ctx, choice: str):
        choices = ['rock', 'paper', 'scissors']
        user_c = choice.lower()
        if user_c not in choices:
            return await ctx.send('❌ Choose **rock**, **paper**, or **scissors**.')

        bot_c = random.choice(choices)
        emojis = {'rock': '🪨', 'paper': '📄', 'scissors': '✂️'}

        if user_c == bot_c:
            result, color = "It's a tie!", discord.Color.blue()
        elif (user_c, bot_c) in [('rock', 'scissors'), ('paper', 'rock'), ('scissors', 'paper')]:
            result, color = 'You win! 🎉', discord.Color.green()
        else:
            result, color = 'I win! 🤖', discord.Color.red()

        embed = discord.Embed(title='✂️ Rock Paper Scissors', description=result, color=color)
        embed.add_field(name='Your pick', value=f'{emojis[user_c]} {user_c.title()}')
        embed.add_field(name='My pick', value=f'{emojis[bot_c]} {bot_c.title()}')
        await ctx.send(embed=embed)

    @commands.hybrid_command(name='meme', description='Fetch a random meme from Reddit')
    async def meme(self, ctx):
        await ctx.defer()
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get('https://meme-api.com/gimme') as r:
                    if r.status == 200:
                        d = await r.json()
                        embed = discord.Embed(
                            title=d['title'],
                            url=d['postLink'],
                            color=discord.Color.blue()
                        )
                        embed.set_image(url=d['url'])
                        embed.set_footer(text=f"👍 {d['ups']} • r/{d['subreddit']}")
                        return await ctx.send(embed=embed)
        except Exception as e:
            logger.error(f'Meme fetch error: {e}')
        await ctx.send('❌ Could not fetch a meme right now. Try again shortly.')

    @commands.hybrid_command(name='joke', description='Get a random joke')
    async def joke(self, ctx):
        await ctx.defer()
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get('https://v2.jokeapi.dev/joke/Any?type=twopart&safe-mode') as r:
                    if r.status == 200:
                        d = await r.json()
                        embed = discord.Embed(
                            title='😂 Joke',
                            description=d['setup'],
                            color=discord.Color.blue()
                        )
                        embed.add_field(name='Punchline', value=d['delivery'], inline=False)
                        return await ctx.send(embed=embed)
        except Exception as e:
            logger.error(f'Joke fetch error: {e}')
        await ctx.send('❌ Could not fetch a joke right now.')

    @commands.hybrid_command(name='fact', description='Get a random fun fact')
    async def fact(self, ctx):
        await ctx.defer()
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get('https://uselessfacts.jsph.pl/api/v2/facts/random') as r:
                    if r.status == 200:
                        d = await r.json()
                        embed = discord.Embed(
                            title='🤓 Random Fact',
                            description=d['text'],
                            color=discord.Color.blue()
                        )
                        return await ctx.send(embed=embed)
        except Exception as e:
            logger.error(f'Fact fetch error: {e}')
        await ctx.send('❌ Could not fetch a fact right now.')

    @commands.hybrid_command(name='say', description='Make the bot repeat a message')
    @commands.has_permissions(manage_messages=True)
    @app_commands.describe(message='The message to send')
    async def say(self, ctx, *, message: str):
        try:
            await ctx.message.delete()
        except:
            pass
        await ctx.channel.send(message)

    @commands.hybrid_command(name='embed', description='Post a custom embed message')
    @commands.has_permissions(manage_messages=True)
    @app_commands.describe(title='Embed title', description='Embed body text', color='Color: blue/red/green/gold/purple/orange')
    async def embed_cmd(self, ctx, title: str, description: str, color: str = 'blue'):
        color_map = {
            'blue': discord.Color.blue(),
            'red': discord.Color.red(),
            'green': discord.Color.green(),
            'gold': discord.Color.gold(),
            'purple': discord.Color.purple(),
            'orange': discord.Color.orange(),
            'pink': discord.Color.from_rgb(255, 105, 180),
            'white': discord.Color.from_rgb(255, 255, 255),
        }
        embed = discord.Embed(
            title=title,
            description=description,
            color=color_map.get(color.lower(), discord.Color.blue()),
            timestamp=datetime.datetime.utcnow()
        )
        embed.set_footer(text=f'Posted by {ctx.author.name}', icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name='avatar', description="Show a user's avatar")
    @app_commands.describe(member='Member to show avatar for (defaults to yourself)')
    async def avatar(self, ctx, member: Optional[discord.Member] = None):
        member = member or ctx.author
        embed = discord.Embed(
            title=f"{member.display_name}'s Avatar",
            color=member.color if member.color.value else discord.Color.blue()
        )
        embed.set_image(url=member.display_avatar.url)
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label='Open in browser', url=member.display_avatar.url))
        await ctx.send(embed=embed, view=view)

    @commands.hybrid_command(name='banner', description="Show a user's profile banner")
    @app_commands.describe(member='Member to check (defaults to yourself)')
    async def banner(self, ctx, member: Optional[discord.Member] = None):
        member = member or ctx.author
        user = await self.bot.fetch_user(member.id)
        if not user.banner:
            return await ctx.send(f'**{member.name}** does not have a profile banner set.')
        embed = discord.Embed(
            title=f"{member.display_name}'s Banner",
            color=member.color if member.color.value else discord.Color.blue()
        )
        embed.set_image(url=user.banner.url)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name='servericon', description="Show the server's icon")
    async def servericon(self, ctx):
        if not ctx.guild.icon:
            return await ctx.send('This server does not have an icon set.')
        embed = discord.Embed(
            title=f"{ctx.guild.name}'s Icon",
            color=discord.Color.blue()
        )
        embed.set_image(url=ctx.guild.icon.url)
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label='Open in browser', url=ctx.guild.icon.url))
        await ctx.send(embed=embed, view=view)

    @commands.hybrid_command(name='poll', description='Create a reaction poll')
    @app_commands.describe(question='The poll question', options='Options separated by commas (2–10)')
    async def poll(self, ctx, question: str, *, options: str):
        opts = [o.strip() for o in options.split(',') if o.strip()]
        if len(opts) < 2:
            return await ctx.send('❌ You need at least 2 options.')
        if len(opts) > 10:
            return await ctx.send('❌ Maximum 10 options per poll.')

        number_emojis = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']
        desc = '\n\n'.join([f'{number_emojis[i]} {opt}' for i, opt in enumerate(opts)])

        embed = discord.Embed(
            title=f'📊 {question}',
            description=desc,
            color=discord.Color.blue(),
            timestamp=datetime.datetime.utcnow()
        )
        embed.set_footer(text=f'Poll by {ctx.author.name}', icon_url=ctx.author.display_avatar.url)

        msg = await ctx.send(embed=embed)
        for i in range(len(opts)):
            await msg.add_reaction(number_emojis[i])

    @commands.hybrid_command(name='choose', description='Let the bot pick from a list of options')
    @app_commands.describe(options='Options separated by commas')
    async def choose(self, ctx, *, options: str):
        opts = [o.strip() for o in options.split(',') if o.strip()]
        if len(opts) < 2:
            return await ctx.send('❌ Give at least 2 options to choose from.')
        embed = discord.Embed(
            title='🤔 I choose...',
            description=f'**{random.choice(opts)}**',
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Fun(bot))
