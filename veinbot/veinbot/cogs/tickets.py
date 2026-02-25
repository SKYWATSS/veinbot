import discord
from discord.ext import commands
from discord import app_commands
import json, datetime, io
import logging

logger = logging.getLogger(__name__)


class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label='Open a Ticket', style=discord.ButtonStyle.green, emoji='🎫', custom_id='open_ticket')
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
            guild_config = config.get(str(interaction.guild.id), {})
        except:
            guild_config = {}

        safe_name = ''.join(c for c in interaction.user.name.lower() if c.isalnum() or c == '_')[:20]
        ch_name = f'ticket-{safe_name}'

        for ch in interaction.guild.text_channels:
            if ch.name == ch_name:
                return await interaction.response.send_message(
                    '❌ You already have an open ticket.',
                    ephemeral=True
                )

        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True),
            interaction.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True)
        }

        staff_id = guild_config.get('staff_role')
        if staff_id:
            role = interaction.guild.get_role(staff_id)
            if role:
                overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        cat_id = guild_config.get('ticket_category')
        category = interaction.guild.get_channel(cat_id) if cat_id else None

        try:
            channel = await interaction.guild.create_text_channel(
                ch_name,
                category=category,
                overwrites=overwrites,
                topic=f'Ticket for {interaction.user.name} ({interaction.user.id})'
            )
        except Exception as e:
            return await interaction.response.send_message(
                f'❌ Could not create ticket channel: {e}',
                ephemeral=True
            )

        embed = discord.Embed(
            title='🎫 Ticket Opened',
            description=(
                f'Welcome {interaction.user.mention}!\n\n'
                f'Please describe your issue in as much detail as possible and a staff member will assist you shortly.'
            ),
            color=discord.Color.green(),
            timestamp=datetime.datetime.utcnow()
        )
        embed.set_footer(text='Click the button below to close this ticket')
        await channel.send(embed=embed, view=TicketControlView())
        await interaction.response.send_message(
            f'✅ Your ticket has been created: {channel.mention}',
            ephemeral=True
        )


class TicketControlView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label='Close Ticket', style=discord.ButtonStyle.danger, emoji='🔒', custom_id='close_ticket')
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        channel = interaction.channel
        messages = []
        async for msg in channel.history(limit=None, oldest_first=True):
            ts = msg.created_at.strftime('%Y-%m-%d %H:%M')
            content = msg.content or '[embed/attachment]'
            messages.append(f'[{ts}] {msg.author}: {content}')

        transcript = '\n'.join(messages)
        file_bytes = io.BytesIO(transcript.encode())
        f = discord.File(file_bytes, filename=f'transcript-{channel.name}.txt')

        try:
            await interaction.user.send(
                f'📝 Here is the transcript for **{channel.name}**:',
                file=f
            )
        except:
            pass

        await channel.delete(reason=f'Ticket closed by {interaction.user}')


class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        bot.add_view(TicketView())
        bot.add_view(TicketControlView())

    @commands.hybrid_command(name='ticketpanel', description='Send the ticket creation panel')
    @commands.has_permissions(administrator=True)
    async def ticket_panel(self, ctx):
        embed = discord.Embed(
            title='🎫 Support Tickets',
            description=(
                'Need help? Click the button below to open a private support ticket.\n'
                'A staff member will assist you as soon as possible.'
            ),
            color=discord.Color.blue()
        )
        embed.add_field(
            name='Guidelines',
            value='• Be respectful to staff\n• Describe your issue clearly\n• Include any relevant screenshots or details',
            inline=False
        )
        embed.set_footer(text=ctx.guild.name, icon_url=ctx.guild.icon.url if ctx.guild.icon else None)
        await ctx.send(embed=embed, view=TicketView())

    @commands.hybrid_command(name='adduser', description='Add a user to the current ticket')
    @commands.has_permissions(manage_channels=True)
    @app_commands.describe(user='User to add')
    async def add_user(self, ctx, user: discord.Member):
        if not ctx.channel.name.startswith('ticket-'):
            return await ctx.send('❌ This command can only be used in ticket channels.')
        await ctx.channel.set_permissions(user, read_messages=True, send_messages=True)
        await ctx.send(f'✅ Added {user.mention} to this ticket.')

    @commands.hybrid_command(name='removeuser', description='Remove a user from the current ticket')
    @commands.has_permissions(manage_channels=True)
    @app_commands.describe(user='User to remove')
    async def remove_user(self, ctx, user: discord.Member):
        if not ctx.channel.name.startswith('ticket-'):
            return await ctx.send('❌ This command can only be used in ticket channels.')
        await ctx.channel.set_permissions(user, overwrite=None)
        await ctx.send(f'✅ Removed {user.mention} from this ticket.')

    @commands.hybrid_command(name='rename', description='Rename the current ticket channel')
    @commands.has_permissions(manage_channels=True)
    @app_commands.describe(name='New channel name')
    async def rename_ticket(self, ctx, *, name: str):
        if not ctx.channel.name.startswith('ticket-'):
            return await ctx.send('❌ This command can only be used in ticket channels.')
        await ctx.channel.edit(name=name)
        await ctx.send(f'✅ Renamed to **{name}**.')

    @commands.hybrid_command(name='transcript', description='Save the current ticket as a transcript')
    @commands.has_permissions(manage_channels=True)
    async def transcript(self, ctx):
        if not ctx.channel.name.startswith('ticket-'):
            return await ctx.send('❌ This command can only be used in ticket channels.')
        await ctx.defer()
        messages = []
        async for msg in ctx.channel.history(limit=None, oldest_first=True):
            ts = msg.created_at.strftime('%Y-%m-%d %H:%M')
            content = msg.content or '[embed/attachment]'
            messages.append(f'[{ts}] {msg.author}: {content}')
        transcript = '\n'.join(messages)
        file_bytes = io.BytesIO(transcript.encode())
        f = discord.File(file_bytes, filename=f'transcript-{ctx.channel.name}.txt')
        await ctx.send('📝 Transcript saved:', file=f)

    @commands.hybrid_group(name='ticketsetup', description='Configure the ticket system')
    @commands.has_permissions(administrator=True)
    async def ticket_setup(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send('Usage: `.ticketsetup category <category>` or `.ticketsetup staffrole <role>`')

    @ticket_setup.command(name='category', description='Set which category ticket channels are created in')
    @app_commands.describe(category='Category channel')
    async def set_category(self, ctx, category: discord.CategoryChannel):
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
        except:
            config = {}
        config.setdefault(str(ctx.guild.id), {})['ticket_category'] = category.id
        with open('config.json', 'w') as f:
            json.dump(config, f, indent=4)
        await ctx.send(f'✅ Tickets will be created in the **{category.name}** category.')

    @ticket_setup.command(name='staffrole', description='Set which role has access to all tickets')
    @app_commands.describe(role='Staff role')
    async def set_staff(self, ctx, role: discord.Role):
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
        except:
            config = {}
        config.setdefault(str(ctx.guild.id), {})['staff_role'] = role.id
        with open('config.json', 'w') as f:
            json.dump(config, f, indent=4)
        await ctx.send(f'✅ {role.mention} will have access to all tickets.')


async def setup(bot):
    await bot.add_cog(Tickets(bot))
