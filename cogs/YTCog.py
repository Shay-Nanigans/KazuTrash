import asyncio
import discord
import os
import yt_dlp
from moviepy.editor import VideoFileClip,vfx,AudioFileClip
import ytcaptionfinder
import random
import re


from discord.ext import commands
class YTCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None

    @commands.command(name="ytclip")
    async def ytclip(self, ctx, url, *args):
        """Makes clip from youtube video. 
        $ytclip url start end
        -speed [multiplier]: changes clip playback speed
        -audio: mp3 file
        -noaudio: video with no audio
        -cropx [percent of frame] [percent of frame]: crops out everything left of %1 and everyting right of %2
        -cropy [percent of frame] [percent of frame]: crops out everything above of %1 and everyting below of %2
        -name [filename]: changes filename"""
        if "?t=" in url:
            end = args[0]
            url, start = url.split("?t=",1)
        else:
            end = args[1]
            start = args[0]

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

        try:
            audio = re.search(r"-audio", str(' '.join(args))) 
            if audio:
                filetype = "mp3"
                ydl_opts = {
                    'outtmpl': os.path.join(os.getcwd(),'vidclipcogtemp/%(id)s.mp3'),
                    'extract_audio': True,
                    'format': 'bestaudio'
                }

            else:
                filetype = "mp4"
                ydl_opts = {
                    'outtmpl': os.path.join(os.getcwd(),'vidclipcogtemp/%(id)s.%(ext)s'),
                }
        except Exception as e:
            print(e)
            
        async with ctx.channel.typing(): #worse loading bar
            id = yt_dlp.YoutubeDL(ydl_opts).extract_info(url)['id'] #fetch
            if audio:
                clip = AudioFileClip(f"vidclipcogtemp/{id}.mp3").subclip(start, end)
            else:
                clip = VideoFileClip(f"vidclipcogtemp/{id}.mp4").subclip(start, end) #shrink
            #change speed
            # print(str(' '.join(args)))
            try:
                speed = re.search(r"-speed (\d*\.*\d+)", str(' '.join(args))) 
                print(speed)
                namespeed=""
                if speed:
                    speed = float(speed.group(1))
                    print(speed)
                    clip = clip.fx(vfx.speedx, speed)
                    namespeed = f"_x{speed}"
            except Exception as e:
                print(e)
            try:
                noaudio = re.search(r"-noaudio", str(' '.join(args))) 
                if noaudio:
                    clip = clip.without_audio()
            except Exception as e:
                print(e)
                
            try:
                namesize = ""
                if "-cropx" in args or "-cropy" in args:
                    size = clip.size
                    corners = [0,size[0],0,size[1]] # x1 x2 y1 y2

                    cropx = re.search(r"-cropx (\d*\.*\d+) (\d*\.*\d+)", str(' '.join(args))) 
                    print(cropx)
                    if cropx:
                        cropx = (float(cropx.group(1)),float(cropx.group(2)))
                        corners[0] = int(cropx[0]*size[0]/100)
                        corners[1] = int(cropx[1]*size[0]/100)

                    cropy = re.search(r"-cropy (\d*\.*\d+) (\d*\.*\d+)", str(' '.join(args))) 
                    print(cropy)
                    if cropy:
                        cropy = (float(cropy.group(1)),float(cropy.group(2)))
                        corners[3] = int(size[1] - cropy[0]*size[1]/100)
                        corners[2] = int(size[1] - cropy[1]*size[1]/100)
                    print(corners)
                    clip  = vfx.crop(clip, x1=corners[0], x2=corners[1], y1=corners[2], y2=corners[3])
                    namesize = f"_cropped_{corners[0]}-{corners[1]}_{corners[2]}-{corners[3]}"
            except Exception as e:
                print(e)

            try:
                filename = re.search(r"-name (\w*)", str(' '.join(args))) 
                print(filename)
            except Exception as e:
                print(e)

            if not filename:
                clipname = f"vidclipcogtemp/{id}_{start}-{end}{namespeed}{namesize}.{filetype}"
            else:
                clipname = f'{filename.group(1)}.{filetype}'
            if speed:
                vbitrate = f'{56000/((end-start)/speed)}k'
            else:
                vbitrate = f'{56000/(end-start)}k'
            if audio:
                clip.write_audiofile(clipname)
            else:
                clip.write_videofile(clipname, codec="libx264", bitrate = vbitrate, temp_audiofile=f'vidclipcogtemp/{id}temp-audio.m4a', remove_temp=True, audio_codec='aac') #encode

            #too big
            if os.stat(clipname).st_size > 8300000: 
                await ctx.send("Video larger than 8MB!")
                os.remove(clipname)
                clip.close()
                os.remove(f"vidclipcogtemp/{id}.{filetype}")
                return

            await ctx.send(file=discord.File(clipname))

            #cleanup
            os.remove(clipname)
            clip.close()
            os.remove(f"vidclipcogtemp/{id}.{filetype}")


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
                    matches = ytcaptionfinder.toUrls(matches)
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


