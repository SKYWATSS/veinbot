import discord
from discord.ext import commands
from discord import app_commands
import json, random, datetime
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.economy = {}
        self.shop_items = {}
        self.inventories = {}
        self.load_data()

    def load_data(self):
        try:
            with open('database.json', 'r') as f:
                data = json.load(f)
            self.economy = data.get('economy', {})
            self.shop_items = data.get('shop', {})
            self.inventories = data.get('inventory', {})
        except:
            self.economy = {}
            self.shop_items = {}
            self.inventories = {}

    def save_data(self):
        try:
            with open('database.json', 'r') as f:
                data = json.load(f)
        except:
            data = {}
        data['economy'] = self.economy
        data['shop'] = self.shop_items
        data['inventory'] = self.inventories
        with open('database.json', 'w') as f:
            json.dump(data, f, indent=4)

    def get_user(self, user_id: str, guild_id: str) -> Dict:
        key = f'{guild_id}:{user_id}'
        if key not in self.economy:
            self.economy[key] = {
                'wallet': 100, 'bank': 0,
                'bank_max': 5000, 'daily_streak': 0,
                'last_daily': None
            }
        return self.economy[key]

    @commands.hybrid_command(name='balance', aliases=['bal'], description='Check your or another member\'s balance')
    @app_commands.describe(member='Member to check (defaults to yourself)')
    async def balance(self, ctx, member: Optional[discord.Member] = None):
        member = member or ctx.author
        d = self.get_user(str(member.id), str(ctx.guild.id))
        embed = discord.Embed(title=f'💰 Balance — {member.display_name}', color=discord.Color.green())
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name='Wallet', value=f'**${d["wallet"]:,}**', inline=True)
        embed.add_field(name='Bank', value=f'**${d["bank"]:,}** / ${d["bank_max"]:,}', inline=True)
        embed.add_field(name='Total', value=f'**${d["wallet"] + d["bank"]:,}**', inline=True)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name='daily', description='Claim your daily reward')
    @commands.cooldown(1, 86400, commands.BucketType.user)
    async def daily(self, ctx):
        d = self.get_user(str(ctx.author.id), str(ctx.guild.id))
        streak = d.get('daily_streak', 0)
        amount = 100 + min(streak * 10, 400)
        d['wallet'] += amount
        d['daily_streak'] = streak + 1
        d['last_daily'] = str(datetime.datetime.utcnow())
        self.save_data()

        embed = discord.Embed(title='📅 Daily Reward', color=discord.Color.green(), timestamp=datetime.datetime.utcnow())
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)
        embed.add_field(name='Earned', value=f'**${amount:,}**', inline=True)
        embed.add_field(name='Streak', value=f'**{streak + 1}** day(s)', inline=True)
        embed.add_field(name='Wallet', value=f'**${d["wallet"]:,}**', inline=True)
        embed.set_footer(text='Come back tomorrow for your next reward!')
        await ctx.send(embed=embed)

    @daily.error
    async def daily_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            s = int(error.retry_after)
            h, m = divmod(s, 3600)
            m, s = divmod(m, 60)
            await ctx.send(f'⏰ Your daily reward resets in **{h}h {m}m**.')

    @commands.hybrid_command(name='work', description='Work a job to earn money')
    @commands.cooldown(1, 3600, commands.BucketType.user)
    async def work(self, ctx):
        d = self.get_user(str(ctx.author.id), str(ctx.guild.id))
        jobs = [
            ('Software Developer', 250, 450),
            ('Graphic Designer', 200, 380),
            ('Content Writer', 160, 310),
            ('Teacher', 170, 330),
            ('Doctor', 300, 550),
            ('Engineer', 240, 460),
            ('Chef', 150, 290),
            ('Truck Driver', 140, 270),
            ('Lawyer', 280, 500),
            ('Plumber', 180, 350),
        ]
        job, lo, hi = random.choice(jobs)
        earned = random.randint(lo, hi)
        d['wallet'] += earned
        self.save_data()

        embed = discord.Embed(title='💼 Work', color=discord.Color.blue(), timestamp=datetime.datetime.utcnow())
        embed.description = f'You worked as a **{job}** and earned **${earned:,}**!'
        embed.add_field(name='Wallet', value=f'**${d["wallet"]:,}**')
        embed.set_footer(text='Cooldown: 1 hour')
        await ctx.send(embed=embed)

    @work.error
    async def work_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            s = int(error.retry_after)
            m, s = divmod(s, 60)
            await ctx.send(f'⏰ You can work again in **{m}m {s}s**.')

    @commands.hybrid_command(name='gamble', description='Gamble your money')
    @app_commands.describe(amount='Amount to gamble')
    async def gamble(self, ctx, amount: int):
        d = self.get_user(str(ctx.author.id), str(ctx.guild.id))
        if amount <= 0:
            return await ctx.send('❌ Amount must be a positive number.')
        if amount > d['wallet']:
            return await ctx.send(f'❌ You only have **${d["wallet"]:,}** in your wallet.')

        roll = random.randint(1, 100)
        if roll <= 45:
            d['wallet'] -= amount
            result = f'lost **${amount:,}**'
            color = discord.Color.red()
            emoji = '😢'
        elif roll <= 75:
            d['wallet'] += amount
            result = f'won **${amount:,}**'
            color = discord.Color.green()
            emoji = '🎉'
        elif roll <= 95:
            winnings = amount * 2
            d['wallet'] += winnings
            result = f'won **${winnings:,}** (3x)'
            color = discord.Color.gold()
            emoji = '🎊'
        else:
            winnings = amount * 4
            d['wallet'] += winnings
            result = f'won **${winnings:,}** — JACKPOT (5x)!'
            color = discord.Color.purple()
            emoji = '💰'

        self.save_data()
        embed = discord.Embed(title=f'{emoji} Gamble Result', color=color, timestamp=datetime.datetime.utcnow())
        embed.description = f'You {result}!'
        embed.add_field(name='Wallet', value=f'**${d["wallet"]:,}**')
        await ctx.send(embed=embed)

    @commands.hybrid_command(name='deposit', aliases=['dep'], description='Deposit money into your bank')
    @app_commands.describe(amount="Amount to deposit, or 'all'")
    async def deposit(self, ctx, amount: str):
        d = self.get_user(str(ctx.author.id), str(ctx.guild.id))
        amt = d['wallet'] if amount.lower() == 'all' else (int(amount) if amount.isdigit() else None)
        if amt is None:
            return await ctx.send("❌ Enter a number or 'all'.")
        if amt <= 0:
            return await ctx.send('❌ Amount must be positive.')
        if amt > d['wallet']:
            return await ctx.send('❌ Not enough money in your wallet.')
        space = d['bank_max'] - d['bank']
        if space <= 0:
            return await ctx.send(f'❌ Your bank is full (${d["bank_max"]:,} max).')
        amt = min(amt, space)
        d['wallet'] -= amt
        d['bank'] += amt
        self.save_data()
        await ctx.send(f'✅ Deposited **${amt:,}** into your bank.')

    @commands.hybrid_command(name='withdraw', description='Withdraw money from your bank')
    @app_commands.describe(amount="Amount to withdraw, or 'all'")
    async def withdraw(self, ctx, amount: str):
        d = self.get_user(str(ctx.author.id), str(ctx.guild.id))
        amt = d['bank'] if amount.lower() == 'all' else (int(amount) if amount.isdigit() else None)
        if amt is None:
            return await ctx.send("❌ Enter a number or 'all'.")
        if amt <= 0:
            return await ctx.send('❌ Amount must be positive.')
        if amt > d['bank']:
            return await ctx.send('❌ Not enough money in your bank.')
        d['wallet'] += amt
        d['bank'] -= amt
        self.save_data()
        await ctx.send(f'✅ Withdrew **${amt:,}** from your bank.')

    @commands.hybrid_command(name='transfer', description='Transfer money to another member')
    @app_commands.describe(member='Recipient', amount='Amount to transfer')
    async def transfer(self, ctx, member: discord.Member, amount: int):
        if member.bot:
            return await ctx.send("❌ You can't transfer money to bots.")
        if member == ctx.author:
            return await ctx.send("❌ You can't transfer money to yourself.")
        if amount <= 0:
            return await ctx.send('❌ Amount must be positive.')
        src = self.get_user(str(ctx.author.id), str(ctx.guild.id))
        if amount > src['wallet']:
            return await ctx.send('❌ Not enough money in your wallet.')
        tgt = self.get_user(str(member.id), str(ctx.guild.id))
        src['wallet'] -= amount
        tgt['wallet'] += amount
        self.save_data()
        embed = discord.Embed(
            title='💸 Transfer Complete',
            description=f'Sent **${amount:,}** to {member.mention}.',
            color=discord.Color.green()
        )
        embed.add_field(name='Your New Balance', value=f'**${src["wallet"]:,}**')
        await ctx.send(embed=embed)

    @commands.hybrid_group(name='shop', description='Browse the server shop')
    async def shop(self, ctx):
        if ctx.invoked_subcommand is None:
            gid = str(ctx.guild.id)
            items = self.shop_items.get(gid, {})
            if not items:
                return await ctx.send('The shop is empty. An admin can add items with `.shop add`.')
            embed = discord.Embed(title='🛒 Server Shop', color=discord.Color.blue())
            for iid, item in items.items():
                embed.add_field(
                    name=f"{item['name']} — ${item['price']:,}",
                    value=f"{item['description']}\nID: `{iid}`",
                    inline=False
                )
            embed.set_footer(text='Use .buy <id> to purchase an item')
            await ctx.send(embed=embed)

    @shop.command(name='add', description='Add an item to the shop (Admin)')
    @commands.has_permissions(administrator=True)
    @app_commands.describe(name='Item name', price='Item price', description='Item description')
    async def shop_add(self, ctx, name: str, price: int, *, description: str):
        gid = str(ctx.guild.id)
        if gid not in self.shop_items:
            self.shop_items[gid] = {}
        iid = str(len(self.shop_items[gid]) + 1)
        self.shop_items[gid][iid] = {'name': name, 'price': price, 'description': description}
        self.save_data()
        await ctx.send(f'✅ Added **{name}** to the shop (ID: `{iid}`, Price: ${price:,}).')

    @shop.command(name='remove', description='Remove an item from the shop (Admin)')
    @commands.has_permissions(administrator=True)
    @app_commands.describe(item_id='Item ID to remove')
    async def shop_remove(self, ctx, item_id: str):
        gid = str(ctx.guild.id)
        if gid in self.shop_items and item_id in self.shop_items[gid]:
            name = self.shop_items[gid][item_id]['name']
            del self.shop_items[gid][item_id]
            self.save_data()
            await ctx.send(f'✅ Removed **{name}** from the shop.')
        else:
            await ctx.send('❌ Item not found.')

    @commands.hybrid_command(name='buy', description='Buy an item from the shop')
    @app_commands.describe(item_id='ID of the item to buy')
    async def buy(self, ctx, item_id: str):
        gid = str(ctx.guild.id)
        if gid not in self.shop_items or item_id not in self.shop_items[gid]:
            return await ctx.send('❌ Item not found. Use `.shop` to browse.')
        item = self.shop_items[gid][item_id]
        d = self.get_user(str(ctx.author.id), gid)
        if d['wallet'] < item['price']:
            return await ctx.send(f'❌ You need **${item["price"]:,}** to buy this. You have ${d["wallet"]:,}.')
        inv_key = f'{gid}:{ctx.author.id}'
        if inv_key not in self.inventories:
            self.inventories[inv_key] = []
        self.inventories[inv_key].append({
            'item_id': item_id, 'name': item['name'],
            'purchase_date': str(datetime.datetime.utcnow())
        })
        d['wallet'] -= item['price']
        self.save_data()
        embed = discord.Embed(
            title='✅ Purchase Successful',
            description=f'You bought **{item["name"]}** for **${item["price"]:,}**!',
            color=discord.Color.green()
        )
        embed.add_field(name='Remaining Balance', value=f'**${d["wallet"]:,}**')
        await ctx.send(embed=embed)

    @commands.hybrid_command(name='inventory', aliases=['inv'], description='View your inventory')
    async def inventory(self, ctx):
        inv_key = f'{ctx.guild.id}:{ctx.author.id}'
        inv = self.inventories.get(inv_key, [])
        if not inv:
            return await ctx.send('Your inventory is empty.')
        counts = {}
        for item in inv:
            counts[item['name']] = counts.get(item['name'], 0) + 1
        embed = discord.Embed(title=f"🎒 {ctx.author.display_name}'s Inventory", color=discord.Color.blue())
        for name, count in counts.items():
            embed.add_field(name=name, value=f'x{count}', inline=True)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name='rich', description='View the richest members leaderboard')
    async def rich(self, ctx):
        gid = str(ctx.guild.id)
        wealth = [
            (k.split(':')[1], v['wallet'] + v['bank'])
            for k, v in self.economy.items()
            if k.startswith(f'{gid}:')
        ]
        wealth.sort(key=lambda x: x[1], reverse=True)
        embed = discord.Embed(title='💰 Richest Members', color=discord.Color.gold())
        medals = ['🥇', '🥈', '🥉']
        for i, (uid, total) in enumerate(wealth[:10]):
            m = ctx.guild.get_member(int(uid))
            name = m.display_name if m else f'Unknown ({uid})'
            medal = medals[i] if i < 3 else f'{i + 1}.'
            embed.add_field(name=f'{medal} {name}', value=f'**${total:,}**', inline=False)
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Economy(bot))
