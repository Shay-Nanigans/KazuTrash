import asyncio
import discord
import os
import yt_dlp
from moviepy.editor import VideoFileClip
import ytcaptionfinder
import random


from discord.ext import commands
class YTCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None

    @commands.command(name="ytclip", help = "Makes clip from youtube video. $ytclip url start end")
    async def ytclip(self, ctx, url, start:str, end:str):

        #seconds or minutes:seconds or hour:minutes:seconds or something
        if start.count(":") == 2:
            start = float(start.split(":")[0])*3600+float(start.split(":")[1])*60+float(start.split(":")[2])
        elif start.count(":") == 1:
            start = float(start.split(":")[0])*60+float(start.split(":")[1])
        else:
            start = float(start)

        if end.count(":") == 2:
            end = float(end.split(":")[0])*3600+float(end.split(":")[1])*60+float(end.split(":")[2])
        elif end.count(":") == 1:
            end = float(end.split(":")[0])*60+float(end.split(":")[1])
        else:
            end = float(end)

        #check if real
        if start >= end:
            await ctx.send("Invalid length video")
            return

        ydl_opts = {
                    'format': 'mp4',
                    'outtmpl': os.path.join(os.getcwd(),'vidclipcogtemp/%(id)s.%(ext)s'),
                }
        async with ctx.channel.typing(): #worse loading bar
            id = yt_dlp.YoutubeDL(ydl_opts).extract_info(url)['id'] #fetch
            clip = VideoFileClip(f"vidclipcogtemp/{id}.mp4").subclip(start, end) #shrink
            clip.to_videofile(f"vidclipcogtemp/{id}_{start}-{end}.mp4", codec="libx264", temp_audiofile=f'vidclipcogtemp/{id}temp-audio.m4a', remove_temp=True, audio_codec='aac') #encode

            #too big
            if os.stat(f"vidclipcogtemp/{id}_{start}-{end}.mp4").st_size > 8300000: 
                await ctx.send("Video larger than 8MB!")
                os.remove(f"vidclipcogtemp/{id}_{start}-{end}.mp4")
                clip.close()
                os.remove(f"vidclipcogtemp/{id}.mp4")
                return

            await ctx.send(file=discord.File(f"vidclipcogtemp/{id}_{start}-{end}.mp4"))

            #cleanup
            os.remove(f"vidclipcogtemp/{id}_{start}-{end}.mp4")
            clip.close()
            os.remove(f"vidclipcogtemp/{id}.mp4")


    @commands.command(name="ytfind")
    async def ytfind(self, ctx, searchstring, *urls):
        '''Finds phrase in a youtube video/channel/playlist. $ytfind \"thing to find\" channel [channel2 channel3.....]
        -exact (after searchstring) to return exact start and end'''
        try:
            async with ctx.channel.typing():
                urls = list(urls)
                exact = "-exact" in urls
                if exact:
                    urls.remove("-exact")

                matches, errors = await asyncio.to_thread(ytcaptionfinder.findList,searchstring, list(urls))
                if not exact:
                    matches = ytcaptionfinder.toUrl(matches)
                msg = f"{len(matches)} matches to \"{searchstring}\" found\n"
                msgs = [msg]
                msg = ""
                for match in matches:
                    if exact:
                        msg = msg + f"\n<https://youtu.be/{match[0]}> {match[1]} {match[2]}"
                    else:
                        msg = msg + f"\n <{match}>"
                    if len(msg)>1800:
                        msgs.append(msg)
                        msg=""
                if msg != "":
                    msgs.append(msg)
                for msg in msgs:
                    await ctx.send(msg)
        except Exception as e: print(e)

    @commands.command(name="ytfindclip")
    async def ytfindclip(self, ctx, searchstring, *urls):
        '''Finds phrase in a youtube video/channel/playlist, picks a random occurence of that phrase, and returns a clip of it'''
        try:
            async with ctx.channel.typing():
                urls = list(urls)

                matches, errors = await asyncio.to_thread(ytcaptionfinder.findList,searchstring, list(urls))
                if len(matches)==0:
                    await ctx.send("Phrase not found")
                    return
                num = random.randint(0,len(matches)-1)
                match = matches[num]
                await self.ytclip(ctx,f"https://youtu.be/{match[0]}",str(match[1]),str(match[2]))

        except Exception as e: print(e)


async def setup(bot):
    if not os.path.exists("vidclipcogtemp"): os.mkdir("vidclipcogtemp")    
    await bot.add_cog(YTCog(bot))


