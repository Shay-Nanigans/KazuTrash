import asyncio
import discord
import os
import yt_dlp
import re
import json


from discord.ext import commands





class MusicCog(commands.Cog):
    musicQueue = {}
    config = None


    def __init__(self, bot):
        self.bot = bot
        self._last_member = None
        try:
            self.config =json.load(open('MusicCog/config.json'))

        except:
            self.config = {
                "volume":{}
            }
            
            json.dump(self.config, open('MusicCog/config.json', 'w'))


    async def downloadFile(self, ctx, url):        
        ydl_opts = {
                    'format': 'bestaudio/best',
                    'outtmpl': os.path.join(os.getcwd(),'MusicCog/songs/%(id)s-%(title)s.%(ext)s'),
                    'download_archive':os.path.join(os.getcwd(),'MusicCog/songs.txt'),
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }],
                }

        yt = yt_dlp.YoutubeDL(ydl_opts)
        try:
            info = yt_dlp.YoutubeDL().extract_info(f"ytsearch1:{url}",download=False)['entries'][0]
            id = info['id']
        except Exception as e:
            print(e)
            await ctx.send("Video not found")
            return None

        print (id)
        # await ctx.reply(f"Playing: {info['title']}",mention_author=False)
        for filename in os.listdir("./MusicCog/songs"):
            if re.match(rf'.*{id}.*', filename):
                return filename

        yt.download([id])

        for filename in os.listdir("./MusicCog/songs"):
            if re.match(rf'.*{id}.*', filename):
                return filename
        print("no file")

    async def player(self,ctx:commands.Context, guild):
        try:
            self.musicQueue[ctx.author.guild.id]['mclient']=await ctx.author.voice.channel.connect()
        except:return
        if guild not in self.config['volume']:
            self.config['volume'][guild] = 1.0
        timeout=0
        print(f"INITIALIZING PLAYER: {guild}")
        if self.musicQueue[guild]['mclient'] is None:
            print("NO PLAYER")
            return
        while not self.musicQueue[guild]['mclient'].is_connected():
            print(self.musicQueue[guild]['mclient'].latency)
            await asyncio.sleep(1)
        while len(self.musicQueue[guild]['queue'])>0 and timeout < 300:
            if len(self.musicQueue[guild]['queue'])==0:
                timeout +=1
                await asyncio.sleep(1)
                continue
            else:
                timeout = 0

            song = self.musicQueue[guild]['queue'].pop(0)
            self.musicQueue[guild]['mclient'].play(discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(song), volume=self.config['volume'][guild]))
            while self.musicQueue[guild]['mclient'].is_playing():
                await asyncio.sleep(0.5)

            if self.musicQueue[guild]['loop']==1:
                self.musicQueue[guild]['queue'].append(song)    
            elif self.musicQueue[guild]['loop']==2:
                self.musicQueue[guild]['queue'].insert(0,song)
            
        await self.musicQueue[guild]['mclient'].disconnect()
        self.musicQueue[guild]['mclient']=None
        

    @commands.command()
    async def play(self, ctx:commands.Context, *, url):
        try:
            filename = await self.downloadFile(ctx, url)
            if ctx.author.voice is None:
                await ctx.send("User not in a channel")
                return
            if ctx.author.guild.id not in self.musicQueue:
                    self.musicQueue[ctx.author.guild.id]={'queue':[],'loop': 0, 'last': None, 'mclient':None}
                        

            self.musicQueue[ctx.author.guild.id]['queue'].append(f"./MusicCog/songs/{filename}")

            if self.musicQueue[ctx.author.guild.id]['mclient'] is None:
                asyncio.create_task(self.player(ctx, ctx.author.guild.id))

        except Exception as e:print(e)

    @commands.command(name = 'next')
    async def next(self, ctx:commands.Context):
        if ctx.guild.id in self.musicQueue:
            self.musicQueue[ctx.guild.id]['mclient'].stop()

    @commands.command(name = "songqueue")
    async def songqueue(self, ctx:commands.Context):
        await ctx.send(self.musicQueue)

    @commands.command(name="stop")
    async def stop(self, ctx:commands.Context):
        self.musicQueue[ctx.guild.id]['loop']=0
        self.musicQueue[ctx.guild.id]['queue']=[]
        self.musicQueue[ctx.guild.id]['last']=None
        self.musicQueue[ctx.guild.id]['mclient'].stop()

    @commands.command(name="leave")
    async def leave(self, ctx:commands.Context):
        self.musicQueue[ctx.guild.id]['queue']=[]
        self.musicQueue[ctx.guild.id]['last']=None
        self.musicQueue[ctx.guild.id]['mclient'].stop()
        await self.musicQueue[ctx.guild.id]['mclient'].disconnect()

    @commands.command(name = "volume")
    async def volume(self,ctx, vol:int):
        self.config['volume'][ctx.author.guild.id] = float(vol)/100
        json.dump(self.config, open('MusicCog/config.json', 'w'))

        if ctx.author.guild.id in self.musicQueue:
            self.musicQueue[ctx.author.guild.id]['mclient'].source.volume=self.config['volume'][ctx.author.guild.id]
            # self.musicQueue[ctx.author.guild.id]['mclient'].source = discord.PCMVolumeTransformer(self.musicQueue[ctx.author.guild.id]['mclient'].source, volume=self.config['volume'][ctx.author.guild.id])


    # 0 = off
    # 1 = all
    # 2 = one
    @commands.command(name = 'loop')
    async def loop(self, ctx:commands.Context, set = None, silent = False):
        loopname = ["off", "all", "one"]
        if ctx.author.voice is None:
            if not silent:
                await ctx.send("User not in voice channel")
            return
        elif ctx.guild.id not in self.musicQueue:
            self.musicQueue[ctx.guild.id] = {'queue': [], 'loop': 0, 'last': None}
        
        if set is None:
            self.musicQueue[ctx.guild.id]['loop'] += 1
            if self.musicQueue[ctx.guild.id]['loop']>2:
                self.musicQueue[ctx.guild.id]['loop'] = 0
        elif set.lower() == "off":
            self.musicQueue[ctx.guild.id]['loop'] = 0
        elif set.lower() == "all":
            self.musicQueue[ctx.guild.id]['loop'] = 1
        elif set.lower() == "one":
            self.musicQueue[ctx.guild.id]['loop'] = 2
        
        if not silent:
            await ctx.send(f"Looping: {loopname[self.musicQueue[ctx.guild.id]['loop']]}")

async def setup(bot):
    print(f"BOT VOICE: {bot.intents.voice_states}")
    if not os.path.exists("MusicCog"): os.mkdir("MusicCog")    
    if not os.path.exists("MusicCog/songs"): os.mkdir("MusicCog/songs") 
    await bot.add_cog(MusicCog(bot))


