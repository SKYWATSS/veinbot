import discord
from discord.ext import commands
from discord import app_commands
import asyncio, datetime
import logging

logger = logging.getLogger(__name__)

try:
    import wavelink
    WAVELINK_AVAILABLE = True
except ImportError:
    WAVELINK_AVAILABLE = False
    logger.warning('wavelink not installed — music commands disabled. Install with: pip install wavelink>=3.0.0')


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        if WAVELINK_AVAILABLE:
            asyncio.get_event_loop().create_task(self._connect_nodes())

    async def _connect_nodes(self):
        await self.bot.wait_until_ready()
        try:
            node = wavelink.Node(uri='http://localhost:2333', password='youshallnotpass')
            await wavelink.Pool.connect(client=self.bot, nodes=[node])
            logger.info('Connected to Lavalink node.')
        except Exception as e:
            logger.error(f'Failed to connect to Lavalink: {e}')

    @commands.Cog.listener()
    async def on_wavelink_track_start(self, payload):
        if not WAVELINK_AVAILABLE:
            return
        player = payload.player
        track = payload.track
        embed = discord.Embed(
            title='🎵 Now Playing',
            description=f'[{track.title}]({track.uri})',
            color=discord.Color.blue()
        )
        embed.add_field(name='Artist', value=track.author or 'Unknown', inline=True)
        dur = str(datetime.timedelta(milliseconds=track.length))
        embed.add_field(name='Duration', value=dur, inline=True)
        if hasattr(player, 'home') and player.home:
            try:
                await player.home.send(embed=embed)
            except:
                pass

    @commands.hybrid_command(name='play', description='Play a song or add it to the queue')
    @app_commands.describe(query='Song name or URL')
    async def play(self, ctx, *, query: str):
        if not WAVELINK_AVAILABLE:
            return await ctx.send('❌ Music is currently unavailable. Lavalink is not installed or running.')
        if not ctx.author.voice:
            return await ctx.send('❌ You need to be in a voice channel to use this.')

        await ctx.defer()
        player = ctx.voice_client
        if not player:
            try:
                player = await ctx.author.voice.channel.connect(cls=wavelink.Player)
                player.home = ctx.channel
            except Exception as e:
                return await ctx.send(f'❌ Could not join your voice channel: {e}')

        try:
            tracks = await wavelink.Playable.search(query)
        except Exception as e:
            return await ctx.send(f'❌ Search failed: {e}')

        if not tracks:
            return await ctx.send('❌ No results found.')

        if isinstance(tracks, wavelink.Playlist):
            for t in tracks.tracks:
                await player.queue.put_wait(t)
            await ctx.send(f'✅ Added **{len(tracks.tracks)}** tracks from **{tracks.name}** to the queue.')
        else:
            track = tracks[0]
            await player.queue.put_wait(track)
            await ctx.send(f'✅ Added **{track.title}** to the queue.')

        if not player.playing:
            await player.play(player.queue.get())

    @commands.hybrid_command(name='pause', description='Pause music playback')
    async def pause(self, ctx):
        if not WAVELINK_AVAILABLE:
            return await ctx.send('❌ Music is unavailable.')
        p = ctx.voice_client
        if not p or not p.playing:
            return await ctx.send('❌ Nothing is playing.')
        await p.pause(True)
        await ctx.send('⏸️ Paused.')

    @commands.hybrid_command(name='resume', description='Resume music playback')
    async def resume(self, ctx):
        if not WAVELINK_AVAILABLE:
            return await ctx.send('❌ Music is unavailable.')
        p = ctx.voice_client
        if not p:
            return await ctx.send('❌ Not connected to a voice channel.')
        await p.pause(False)
        await ctx.send('▶️ Resumed.')

    @commands.hybrid_command(name='skip', description='Skip the current track')
    async def skip(self, ctx):
        if not WAVELINK_AVAILABLE:
            return await ctx.send('❌ Music is unavailable.')
        p = ctx.voice_client
        if not p or not p.playing:
            return await ctx.send('❌ Nothing is playing.')
        await p.stop()
        await ctx.send('⏭️ Skipped.')

    @commands.hybrid_command(name='stop', description='Stop music and disconnect from voice')
    async def stop(self, ctx):
        if not WAVELINK_AVAILABLE:
            return await ctx.send('❌ Music is unavailable.')
        p = ctx.voice_client
        if not p:
            return await ctx.send('❌ Not connected.')
        p.queue.clear()
        await p.stop()
        await p.disconnect()
        await ctx.send('⏹️ Stopped and disconnected.')

    @commands.hybrid_command(name='queue', description='View the music queue')
    async def queue(self, ctx):
        if not WAVELINK_AVAILABLE:
            return await ctx.send('❌ Music is unavailable.')
        p = ctx.voice_client
        if not p:
            return await ctx.send('❌ Not connected to a voice channel.')
        if p.queue.is_empty and not p.current:
            return await ctx.send('📭 The queue is empty.')
        embed = discord.Embed(title='🎵 Queue', color=discord.Color.blue())
        if p.current:
            embed.add_field(name='Now Playing', value=f'[{p.current.title}]({p.current.uri})', inline=False)
        if not p.queue.is_empty:
            ql = list(p.queue)
            entries = '\n'.join([f'`{i}.` {t.title}' for i, t in enumerate(ql[:10], 1)])
            if len(ql) > 10:
                entries += f'\n*...and {len(ql) - 10} more*'
            embed.add_field(name='Up Next', value=entries, inline=False)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name='nowplaying', aliases=['np'], description='Show the currently playing track')
    async def nowplaying(self, ctx):
        if not WAVELINK_AVAILABLE:
            return await ctx.send('❌ Music is unavailable.')
        p = ctx.voice_client
        if not p or not p.current:
            return await ctx.send('❌ Nothing is playing right now.')
        t = p.current
        pos = datetime.timedelta(milliseconds=p.position)
        dur = datetime.timedelta(milliseconds=t.length)
        prog = int((p.position / t.length) * 20) if t.length else 0
        bar = '█' * prog + '░' * (20 - prog)
        embed = discord.Embed(
            title='🎵 Now Playing',
            description=f'[{t.title}]({t.uri})',
            color=discord.Color.blue()
        )
        embed.add_field(name='Artist', value=t.author or 'Unknown', inline=True)
        embed.add_field(name='Progress', value=f'`{pos}` / `{dur}`\n`{bar}`', inline=False)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name='volume', description='Set the playback volume (0–100)')
    @app_commands.describe(volume='Volume level (0–100)')
    async def volume(self, ctx, volume: int):
        if not WAVELINK_AVAILABLE:
            return await ctx.send('❌ Music is unavailable.')
        p = ctx.voice_client
        if not p:
            return await ctx.send('❌ Not connected.')
        if not 0 <= volume <= 100:
            return await ctx.send('❌ Volume must be between 0 and 100.')
        await p.set_volume(volume)
        await ctx.send(f'🔊 Volume set to **{volume}%**.')

    @commands.hybrid_command(name='loop', description='Toggle track looping')
    async def loop(self, ctx):
        if not WAVELINK_AVAILABLE:
            return await ctx.send('❌ Music is unavailable.')
        p = ctx.voice_client
        if not p:
            return await ctx.send('❌ Not connected.')
        if p.queue.mode == wavelink.QueueMode.loop:
            p.queue.mode = wavelink.QueueMode.normal
            await ctx.send('🔁 Loop **disabled**.')
        else:
            p.queue.mode = wavelink.QueueMode.loop
            await ctx.send('🔁 Loop **enabled** — current track will repeat.')

    @commands.hybrid_command(name='shuffle', description='Shuffle the queue')
    async def shuffle(self, ctx):
        if not WAVELINK_AVAILABLE:
            return await ctx.send('❌ Music is unavailable.')
        p = ctx.voice_client
        if not p or p.queue.is_empty:
            return await ctx.send('❌ The queue is empty.')
        p.queue.shuffle()
        await ctx.send('🔀 Queue shuffled.')

    @commands.hybrid_command(name='clearqueue', description='Clear all tracks from the queue')
    async def clearqueue(self, ctx):
        if not WAVELINK_AVAILABLE:
            return await ctx.send('❌ Music is unavailable.')
        p = ctx.voice_client
        if not p:
            return await ctx.send('❌ Not connected.')
        p.queue.clear()
        await ctx.send('✅ Queue cleared.')

    @commands.hybrid_command(name='disconnect', aliases=['dc', 'leave'], description='Disconnect the bot from voice')
    async def disconnect(self, ctx):
        if not WAVELINK_AVAILABLE:
            return await ctx.send('❌ Music is unavailable.')
        p = ctx.voice_client
        if not p:
            return await ctx.send('❌ Not connected.')
        await p.disconnect()
        await ctx.send('👋 Disconnected.')


async def setup(bot):
    await bot.add_cog(Music(bot))
