import discord
from discord.ext import commands, tasks
import time
import tls_client
import asyncio
from fake_useragent import UserAgent
import json

intents = discord.Intents.default()
intents.messages = True
intents.members = True
client = commands.Bot(command_prefix="!", intents=intents)
BotToken = "DIscord bot token here"
roleping_id = 333  # role ping id here
channel_id = 333 # channel id to send notify here


@client.event
async def on_ready():
    print(f'{client.user} is online!')
    try:
        synced = await client.tree.sync()
        print(f'{len(synced)} commands')
        rain_notifier.start()
        client.start_time = time.time()
    except Exception as e:
        print(e)

@client.tree.command(name="status")
async def ping(interaction: discord.Interaction):
    def uptimes(uptime):
        minutes = int((uptime / 60) % 60)
        hours = int((uptime / (60 * 60)) % 24)
        days = int(uptime / (60 * 60 * 24))
        return f"{days}d {hours}h {minutes}m"
    try:
        uptime = time.time() - client.start_time
        uptimedetial = uptimes(uptime)
        embed = discord.Embed(title="Bot Status",description="Ping  - Uptime",timestamp=discord.utils.utcnow())
        embed.add_field(name="• Ping", value=f"> `🟢` {client.latency * 1000:.2f}ms", inline=False)
        embed.add_field(name="• Uptime",value=f"> `🟢` {uptimedetial}",inline=False)
        await interaction.response.send_message(content="", embed=embed)
    except Exception as e:
        await interaction.response.send_message(content=f"Error!!!!\n```{e}```\nskill issuse for sure")


class tls_clients:
    def __init__(self):
        self.ua = UserAgent()
        session = tls_client.Session(client_identifier="safari_15_6_1")
        self.session = session 
        self.headers = {
            "Referer": "https://bloxgame.com/",
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": self.generate_fake_user_agent(),
            "x-client-version":'1.0.0'
        }
    def generate_fake_user_agent(self):
        return self.ua.random
    def get(self, url):
        response = self.session.get(url, headers=self.headers)
        return response
sessions = tls_clients()
@tasks.loop(seconds=5)
async def rain_notifier():
    channel = client.get_channel(channel_id)
    while True:
        try:
            response = sessions.get("https://api.bloxgame.com/chat/history")
            data = json.loads(response.text)
            rain = data.get('rain', None)
        except (json.JSONDecodeError, Exception) as e:
            print(e)
            rain = None
        
        if rain is not None and rain.get('active', False):
            break
        await asyncio.sleep(5)
    prize = f"{rain['prize']:,}".rstrip('0').rstrip('.')
    host_username = f"{rain['host']}"
    embed = discord.Embed(title="Bloxgame Notifier", description="A rain event has been detected on `bloxgame.com`")
    embed.add_field(name="Hoster", value=host_username, inline=True)
    embed.add_field(name="RainAmount", value=f"{prize}B$", inline=True)
    embed.add_field(name="players", value="1", inline=True)
    embed.add_field(name="CashoutPer", value="Pending...", inline=True)
    embed.add_field(name="Is Finished", value="False", inline=True)
    embed.add_field(name="rainStatus", value="active:true", inline=True)
    message = await channel.send(content=f"<@{roleping_id}>", embed=embed)
    if message is None:
        return
    playercount = {player['playerId'] for player in rain['players']} if 'players' in rain else set()
    playerCheck = playercount.copy()
    rain_active = True
    while rain_active:
        await asyncio.sleep(5)
        try:
            response = sessions.get("https://api.bloxgame.com/chat/history")
            data = json.loads(response.text)
            current_rain = data.get('rain', None)
        except (json.JSONDecodeError, Exception) as e:
            print(e)
            current_rain = None
        if current_rain is None or not current_rain.get('active', False):
            try:
                joined_count = len(playercount)
                prizeforeach = round(rain['prize'] / joined_count, 2) if joined_count > 0 else 0
                prizeforeach = f"{prizeforeach:,}".rstrip('0').rstrip('.')
                embed = discord.Embed(title="Bloxgame Notifier", description="rain event on `bloxgame.com` has ended.")
                embed.add_field(name="Hoster", value=f"{host_username}", inline=True)
                embed.add_field(name="RainAmount", value=f"{prize}B$", inline=True)
                embed.add_field(name="playersJoined", value=f"{joined_count}", inline=True)
                embed.add_field(name="CashoutPer", value=f"{prizeforeach}B$", inline=True)
                embed.add_field(name="Is Finished", value="True", inline=True)
                embed.add_field(name="rainStatus", value="active:False", inline=True)
                await message.edit(embed=embed)
            except Exception as e:
                print(e)
            finally:
                return
        current_players = {player['playerId'] for player in current_rain.get('players', [])}
        newplayers = current_players - playerCheck
        playercount.update(newplayers)
        if len(playercount) > 1:
            embed.set_field_at(index=2, name="players:", value=f"{len(playercount)}", inline=False)
            await message.edit(embed=embed)


client.run(BotToken)


