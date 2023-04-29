import discord
from discord.ext import commands
import urllib.request
import json



class CryptoCog(commands.Cog):
    binanceFetchLimit = 1000  
    etherscanToken = None
    wallet = {}

    def __init__(self, bot):
        self.bot = bot
        config =json.load(open('config.json'))
        self.etherscanToken = config["etherscanToken"]

        #Ethereum wallet cache
        try:
            self.wallet =json.load(open('wallet.json'))
            print("wallet loaded")
        except:
            self.wallet = {}
            self.wallet["users"]=[]
            json.dump(self.wallet, open('wallet.json', 'w'))
            print("new wallet made")
        print(self.wallet)


    class URLopener(urllib.request.FancyURLopener):
        version = "Mozilla/5.0"
    opener = URLopener()
    def aquireJson(self, url):
        response = self.opener.open(url)
        data = json.loads(response.read())
        return data

    #returns the USD-CAD exchangerate (#of CAD per USD)
    def USDfetch(self):
        data=self.aquireJson("https://www.bankofcanada.ca/valet/observations/FXUSDCAD?recent=1")
        return data["observations"][0]["FXUSDCAD"]["v"]
        
        
    #fetches price of crypto vs BUSD
    def cryptofetch(self,crypto):
        data=self.aquireJson('https://api.binance.com/api/v3/klines?symbol='+crypto+'BUSD&limit=1&interval=1m')
        return float(data[0][4])
        
    #fetches price of crypto vs USDT and returns all time high
    def cryptohigh(self,crypto):
        data=self.aquireJson('https://api.binance.com/api/v3/klines?symbol='+crypto+'USDT&limit='+str(self.binanceFetchLimit)+'&interval=1M')
        alltimehigh=0
        for thing in data:
            if float(thing[2])>alltimehigh:
                alltimehigh=float(thing[2])
        return alltimehigh
        
        
    #returns the worth of an ETH wallet
    def walletWorth(self,wallet):
        content=self.aquireJson("https://api.etherscan.io/api?module=account&action=balance&address=" + wallet + "&tag=latest&apikey="+ self.etherscanToken)
        return float(content["result"])/1000000000000000000




    @commands.command(name = 'ath', help = 'returns all time high')
    async def ath(self,ctx, coin, *args):
        coin=coin.upper()
        coinprice = self.cryptofetch(coin)
        coinhighprice = self.cryptohigh(coin)
        usdprice = self.USDfetch()
        #print(usdprice)
        response = "The all time high price of "+coin+" is " + str(round(float(coinhighprice) * float(usdprice),2)) + " CAD or " + str(coinhighprice) + " USD"+"\n"
        if len(args)>0:
            if args[0]=="fomo":
                response = response + "The current price of "+coin+" is " + str(round(float(coinprice) * float(usdprice),2)) + " CAD or " + str(coinprice) + " USD" +"\n"
                response = response + "It's currently " + str(round(float(100*coinprice/coinhighprice),1)) +"% of the highest price."
        await ctx.send(response)

    # @commands.command(name='estimate', help = 'estimates days required to mine an amount of money based on hashrate and current balance')
    # async def estimate(self,ctx, amount, *args):
    #     amount=float(amount)
    #     bal = ""
    #     bal2 = ""
    #     saved =""
    #     profit = self.aquireJson("https://api.nanopool.org/v1/eth/approximated_earnings/1")
    #     cad = float(self.USDfetch())
    #     eth = float(self.cryptofetch('ETH'))
    #     flag= False
    #     if len(args)>0:
    #         if (args[0] == "us" or args[0] == "usd" or args[0] == "US" or args[0] == "USD"):
    #             amount = float(amount) * cad
    #     for i in self.wallet["users"]: 
    #         if str(i["discID"])==str(ctx.message.author.id):
    #             bal=float(self.walletWorth(i["ETHwallet"]))
    #             hashrate = self.aquireJson("https://api.nanopool.org/v1/eth/avghashratelimited/" + i["ETHwallet"] + "/24")
    #             bal2 = float(self.aquireJson("https://api.nanopool.org/v1/eth/balance/" + i["ETHwallet"] + "/")["data"])
    #             flag= True
    #             daily=hashrate["data"] * profit["data"]["day"]["dollars"]*cad
    #             saved=bal+bal2
    #     saved=saved*eth*cad
    #     days=round((amount-saved)/daily,1)
        # await ctx.send("About " + str(days) + " days")

    @commands.command(name='balance', help = 'returns balance in the Ethereum wallet of the associated user')
    async def balance(self,ctx):
        eth= float(self.cryptofetch('ETH'))
        cad= float(self.USDfetch())
        response="No associated wallet"
        for i in self.wallet["users"]: 
            if str(i["discID"])==str(ctx.message.author.id):
                bal=float(self.walletWorth(i["ETHwallet"]))
                response= "Wallet " + i["ETHwallet"]+ " contains" + "\n"
                response = response + str(bal) + "ETH" + "\n"
                response = response + "Valued at " + str(round(eth*bal,2)) + "USD or " + str(round(eth*bal*cad,2)) + "CAD"
        await ctx.send(response)
        
    # @commands.command(name='profit', help = 'returns an estimate of the profitability based on nanopool hashrate')
    # async def profit(self,ctx):
    #     profit = self.aquireJson("https://api.nanopool.org/v1/eth/approximated_earnings/1")
    #     cad = float(self.USDfetch())
    #     response="No associated wallet"
    #     for i in self.wallet["users"]: 
    #         if str(i["discID"])==str(ctx.message.author.id):
    #             hashrate = self.aquireJson("https://api.nanopool.org/v1/eth/avghashratelimited/" + i["ETHwallet"] + "/24")
    #             response= "For wallet " + i["ETHwallet"]+"\n"
    #             response= response+ "with a hashrate of " + str(round(hashrate["data"],2)) + "MH/s" +"\n"
    #             response= response+ "Daily profit: " + str(round(hashrate["data"] * profit["data"]["day"]["dollars"], 2)) + "USD or " + str(round(hashrate["data"] * profit["data"]["day"]["dollars"] * cad, 2)) + "CAD" + "\n"
    #             response= response+ "Weekly profit: " + str(round(hashrate["data"] * profit["data"]["week"]["dollars"], 2)) + "USD or " + str(round(hashrate["data"] * profit["data"]["week"]["dollars"] * cad, 2)) + "CAD" + "\n"
    #             response= response+ "Monthly profit: " + str(round(hashrate["data"] * profit["data"]["month"]["dollars"], 2)) + "USD or " + str(round(hashrate["data"] * profit["data"]["month"]["dollars"] * cad, 2)) + "CAD"
    #     await ctx.send(response) 

    @commands.command(name='setwallet', help = 'sets ethereum wallet')
    async def setwallet(self,ctx, walletaddress):
        
        output = {"discID": str(ctx.message.author.id), "ETHwallet": walletaddress}
        for i in self.wallet["users"]:
            print("----------------")
            print(i["discID"] + " " + i["ETHwallet"])
            if str(i["discID"])==str(ctx.message.author.id):
                print("deleting....")
                self.wallet["users"].remove(i)
        self.wallet["users"].append(output)
        json.dump(self.wallet, open('wallet.json', 'w'))
        await ctx.send("Wallet set")

    @commands.command(name='usd', help = 'Returns the USD-CAD exchange rate.')
    async def usd(self,ctx):
        
        await ctx.send("The exchange rate is currently " + str(self.USDfetch()) + "CAD to 1 USD" )


    @commands.command(name='crypto', help = 'Returns the price of given cryptocurrency')
    async def crypto(self,ctx, coin, *args):
        coin=coin.upper()
        coinprice = self.cryptofetch(coin)
        usdprice = self.USDfetch()
        #print(usdprice)
        response = "1 "+coin+" = " + str(round(float(coinprice) * float(usdprice),2)) + " CAD = " + str(coinprice) + " USD"
        if(len(args)>0):
            response = response + '\n'
            response = response + str(float(args[0]))+" "+coin+" = " + str(round(float(coinprice) * float(usdprice)*float(args[0]),2)) + " CAD = " + str(round(coinprice*float(args[0]),2)) + " USD"
        await ctx.send(response) 

    @commands.command(name='eth', help = 'Returns the price of Ethereum')
    async def eth(self,ctx, *args):
        ethprice = self.cryptofetch('ETH')
        usdprice = self.USDfetch()
        #print(usdprice)
        response = "1 ETH = " + str(round(float(ethprice) * float(usdprice),2)) + " CAD = " + str(ethprice) + " USD"
        if(len(args)>0):
            response = response + '\n'
            response = response + str(float(args[0]))+" ETH = " + str(round(float(ethprice) * float(usdprice)*float(args[0]),2)) + " CAD = " + str(round(ethprice*float(args[0]),2)) + " USD"
        await ctx.send(response) 

    @commands.command(name='doge', help = 'Returns the price of Dogecoin')
    async def doge(self,ctx, *args):
        dogeprice = float(self.cryptofetch('DOGE'))
        usdprice = self.USDfetch()
        #print(usdprice)
        response = "1 DOGE = " + str(round(float(dogeprice) * float(usdprice),2)) + " CAD = " + str(dogeprice) + " USD" + '\n'
        if(len(args)>0):
            response = response + str(float(args[0]))+" DOGE = " + str(round(float(dogeprice) * float(usdprice)*float(args[0]),2)) + " CAD = " + str(round(dogeprice*float(args[0]),2)) + " USD" + '\n'
        response = response + 'such profit'
        await ctx.send(response) 
        
async def setup(bot):
    await bot.add_cog(CryptoCog(bot))