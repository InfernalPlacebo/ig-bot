import ast
import asyncio
import logging
import os
import re
from configparser import ConfigParser
from pathlib import Path

import a2s
import discord
import psutil
from discord.ext import commands
from pygtail import Pygtail

import sys

config_object = ConfigParser()
config_file = Path.cwd().joinpath('config', 'config.ini')
config_object.read(config_file)
ror2 = config_object["RoR2"]
general = config_object["General"]

# Config variables
server_address = config_object.get(
    'RoR2', 'server_address'), config_object.getint('RoR2', 'server_port')
steamcmd = Path(ror2["steamcmd"])
ror2ds = Path(ror2["ror2ds"])
BepInEx = Path(ror2["BepInEx"])
role = general["role"]
c_autostart = ror2['auto-start-chat']
s_restart = ror2['auto-server-restart']
hidden_mods = ast.literal_eval(config_object.get('RoR2', 'hidden_mods'))
botcmd = Path.joinpath(BepInEx, 'plugins', 'BotCommands')

# Global variables (yes, I know, not ideal but I'll fix them later)
yes, no = 0, 0
repeat = 0
stagenum = -1

logfile = (BepInEx / "LogOutput.log")

# These get assigned / updated every time server() is called
# Only using string type as a placeholder to avoid exceptions if the server is not online when the bot initializes
server_info = ''
server_players = ''

# Time
run_timer = 0

# Dictionaries used for functions
equip = {
    'CommandMissile': 'Disposable Missile Launcher',
    'Saw': 'Saw',
    'Fruit': 'Foreign Fruit',
    'Meteor': 'Glowing Meteorite',
    'SoulJar': 'Jar of Souls',
    'AffixRed': "Ifrit's Distinction",
    'AffixBlue': 'Silence Between Two Strikes',
    'AffixYellow': '',
    'AffixGold': 'Coven of Gold',
    'AffixWhite': 'Her Biting Embrace',
    'AffixPoison': "N'kuhana's Retort",
    'Blackhole': 'Primordial Cube',
    'GhostGun': "Reaper's Remorse",
    'CritOnUse': 'Ocular HUD',
    'DroneBackup': 'The Back-up',
    'OrbitalLaser': 'EQUIPMENT_ORBITALLASER_NAME',
    'BFG': 'Preon Accumulator',
    'Enigma': 'EQUIPMENT_ENIGMA_NAME',
    'Jetpack': 'Milky Chrysalis',
    'Lightning': 'Royal Capacitor',
    'GoldGat': 'The CrowdFunder',
    'Passive Healing': 'Gnarled Woodsprite',
    'LunarPotion': 'EQUIPMENT_LUNARPOTION_NAME',
    'BurnNearby': 'Hellfire Tincture',
    'SoulCorruptor': 'EQUIPMENT_SOULCORRUPTOR_NAME',
    'Scanner': 'Radar Scanner',
    'CrippleWard': 'Effigy of Grief',
    'Gateway': 'Eccentric Vase',
    'Tonic': 'Spinel Tonic',
    'QuestVolatileBattery': 'Fuel Array',
    'Cleanse': 'Blast Shower',
    'FireBallDash': 'Volcanic Egg',
    'AffixHaunted': 'Spectral Circlet',
    'GainArmor': 'Jade Elephant'
}

item = {
    'Syringe': "Soldier's Syringe",
    'Bear': 'Tougher Times',
    'Behemoth': 'Brilliant Behemoth',
    'Missile': 'ATG Missile Mk. 1',
    'ExplodeOnDeath': "Will-o'-the-wisp",
    'Dagger': 'Ceremonial Dagger',
    'Tooth': 'Monster Tooth',
    'CritGlasses': "Lens-Maker's Glasses",
    'Hoof': "Paul's Goat Hoof",
    'Feather': 'Hopoo Feather',
    'AACannon': 'AA Cannon',
    'ChainLightning': 'Ukulele',
    'PlasmaCore': 'Plasma Core',
    'Seed': 'Leeching Seed',
    'Icicle': 'Frost Relic',
    'GhostOnKill': 'Happiest Mask',
    'Mushroom': 'Bustling Fungus',
    'Crowbar': 'Crowbar',
    'LevelBonus': 'ITEM_LEVELBONUS_NAME',
    'AttackSpeedOnCrit': 'Predatory Instincts',
    'BleedOnHit': 'Tri - Tip Dagger',
    'SprintOutOfCombat': 'Red Whip',
    'FallBoots': 'H3AD - 5T v2',
    'CooldownOnCrit': 'Wicked Ring',
    'WardOnLevel': 'Warbanner',
    'Phasing': 'Old War Stealthkit',
    'HealOnCrit': "Harvester's Scythe",
    'HealWhileSafe': 'Cautious Slug',
    'TempestOnKill': 'ITEM_TEMPESTONKILL_NAME',
    'PersonalShield': 'Personal Shield Generator',
    'EquipmentMagazine': 'Fuel Cell',
    'NovaOnHeal': "N'kuhana's Opinion",
    'ShockNearby': 'Unstable Tesla Coil',
    'Infusion': 'Infusion',
    'WarCryOnCombat': '',
    'Clover': '57 Leaf Clover',
    'Medkit': 'Medkit',
    'Bandolier': 'Bandolier',
    'BounceNearby': 'Sentient Meat Hook',
    'IgniteOnKill': 'Gasoline',
    'PlantOnHit': 'ITEM_PLANTONHIT_NAME',
    'StunChanceOnHit': 'Stun Grenade',
    'Firework': 'Bundle of Fireworks',
    'LunarDagger': 'Shaped Glass',
    'GoldOnHit': 'Brittle Crown',
    'MageAttunement': 'ITEM_MAGEATTUNEMENT_NAME',
    'WarCryOnMultiKill': "Berzerker's Pauldron",
    'BoostHp': 'ITEM_BOOSTHP_NAME',
    'BoostDamage': 'ITEM_BOOSTDAMAGE_NAME',
    'ShieldOnly': 'Transcendence',
    'AlienHead': 'Alien Head',
    'Talisman': 'Soulbound Catalyst',
    'Knurl': 'Titanic Knurl',
    'BeetleGland': "Queen's Gland",
    'BurnNearby': 'ITEM_BURNNEARBY_NAME',
    'CritHeal': 'ITEM_CRITHEAL_NAME',
    'CrippleWardOnLevel': 'ITEM_CRIPPLEWARDONLEVEL_NAME',
    'SprintBonus': 'Energy Drink',
    'SecondarySkillMagazine': 'Backup Magazine',
    'StickyBomb': 'Sticky Bomb',
    'TreasureCache': 'Rusted Key',
    'BossDamageBonus': 'Armor - Piercing Rounds',
    'SprintArmor': 'Rose Buckler',
    'IceRing': "Runald's Band",
    'FireRing': "Kjaro's Band",
    'SlowOnHit': 'Chronobauble',
    'ExtraLife': "Dio's Best Friend",
    'ExtraLifeConsumed': "Dio's Best Friend(Consumed)",
    'UtilitySkillMagazine': 'Hardlight Afterburner',
    'HeadHunter': 'Wake of Vultures',
    'KillEliteFrenzy': 'Brainstalks',
    'RepeatHeal': 'Corpsebloom',
    'Ghost': 'ITEM_GHOST_NAME',
    'HealthDecay': 'ITEM_HEALTHDECAY_NAME',
    'AutoCastEquipment': 'Gesture of the Drowned',
    'IncreaseHealing': 'Rejuvenation Rack',
    'JumpBoost': 'Wax Quail',
    'DrizzlePlayerHelper': 'ITEM_DRIZZLEPLAYERHELPER_NAME',
    'ExecuteLowHealthElite': 'Old Guillotine',
    'EnergizedOnEquipmentUse': 'War Horn',
    'BarrierOnOverHeal': 'Aegis',
    'TonicAffliction': 'Tonic Affliction',
    'TitanGoldDuringTP': 'Halcyon Seed',
    'SprintWisp': 'Little Disciple',
    'BarrierOnKill': 'Topaz Brooch',
    'ArmorReductionOnHit': 'Shattering Justice',
    'TPHealingNova': 'Lepton Daisy',
    'NearbyDamageBonus': 'Focus Crystal',
    'LunarUtilityReplacement': 'Strides of Heresy',
    'MonsoonPlayerHelper': 'ITEM_MONSOONPLAYERHELPER_NAME',
    'Thorns': 'Razorwire',
    'RegenOnKill': 'Fresh Meat',
    'Pearl': 'Pearl',
    'ShinyPearl': 'Irradiant Pearl',
    'BonusGoldPackOnKill': "Ghor's Tome",
    'LaserTurbine': 'Resonance Disc',
    'LunarPrimaryReplacement': 'Visions of Heresy',
    'NovaOnLowHealth': 'Genesis Loop',
    'LunarTrinket': 'Beads of Fealty'
}

stages = {
    'title': 'Title',  # Time not started (keep stage at 0)
    'lobby': 'Game Lobby',  # Time not started (keep stage at 0)
    'blackbeach': 'Distant Roost',
    'blackbeach2': 'Distant Roost',
    'golemplains': 'Titanic Plains',
    'golemplains2': 'Titanic Plains',
    'foggyswamp': 'Wetland Aspect',
    'goolake': 'Abandoned Aqueduct',
    'frozenwall': 'Rallypoint Delta',
    'wispgraveyard': 'Scorched Acres',
    'dampcave': 'Abyssal Depths',
    'shipgraveyard': "Siren's Call",
    # Time paused, no stage progression on following stage
    'bazaar': 'Hidden Realm: Bazaar Between Time',
    # Time paused, no stage progression on following stage
    'goldshores': 'Hidden Realm: Glided Coast',
    # Time paused, no stage progression on following stage
    'mysteryspace': 'Hidden Realm: A Moment, Fractured',
    # Time paused, no stage progression on following stage
    'limbo': 'Hidden Realm: A Moment, Whole',
    # Time is NOT paused, no stage progression on following stage
    'arena': 'Hidden Realm: Void Fields'
}

async def get_run_time():
    await server()
    global server_info
    global run_timer
    if server_info.map_name in ('lobby', 'title'):
        print('Tried to get run time before a run has started')
        run_timer = 0
    else:
        append = open(botcmd / "botcmd.txt", 'a')
        append.write('fixed_time' + '\n')
        append.close()
        findline = True
        while findline:
            for line in Pygtail(str(logfile)):
                if ('[Info   : Unity Log] Run time is ' in line): # [Info   : Unity Log] Run time is 29.34971
                    line = str(line.replace('[Info   : Unity Log] Run time is ',''))
                    run_timer = float(line)
                    run_timer = int(run_timer)
                    findline = False
                    break

async def get_cleared_stages():
    await server()
    global server_info
    global stagenum
    if server_info.map_name in ('lobby', 'title'):
        print('Tried to get stage number before a run has started')
        stagenum = 0
    else:
        append = open(botcmd / "botcmd.txt", 'a')
        append.write('get_stages_cleared' + '\n')
        append.close()
        findline = True
        while findline:
            for line in Pygtail(str(logfile)):
                if ('[Info   : Unity Log] Stages cleared: ' in line): # [Info   : Unity Log] Stages cleared: 3
                    line = str(line.replace('[Info   : Unity Log] Stages cleared: ',''))
                    stagenum = int(line) + 1
                    findline = False
                    break

async def chat(self):
    """Reads the BepInEx output log to send chat to Discord."""
    channel = config_object.getint('RoR2', 'channel')
    channel = self.bot.get_channel(channel)
    global stagenum
    global run_timer
    if os.path.exists(logfile):
        if os.path.exists(BepInEx / "LogOutput.log.offset"):
            for line in Pygtail(str(logfile)):
                # Player chat
                if "issued: say" in line:
                    line = line.replace('[Info   : Unity Log] ', '**')
                    line = re.sub(r" ?\([^)]+\)", "", line)
                    line = line.replace(' issued:', ':** ')
                    line = line.replace(' say ', '')
                    await channel.send(line)
                # Stage change
                elif "Active scene changed from" in line:
                    for key, value in stages.items():
                        if key in line:
                            devstage = key
                            stage = value
                            break
                    if devstage in ('bazaar', 'goldshores', 'mysteryspace', 'limbo', 'arena'):
                        await channel.send('**Entering Stage - ' + stage + '**')
                    # Won't output if the stage is title, done on purpose
                    elif devstage in ('lobby', 'title'):
                        if devstage == 'lobby':
                            await channel.send('**Entering ' + stage + '**')
                    else:
                        await get_cleared_stages()
                        if stagenum == 1:
                            await channel.send('**Entering Stage ' + str(stagenum) + ' - ' + stage + '**')
                        else:
                            await get_run_time()
                            if (run_timer - (int(run_timer/60))*60) < 10:
                                formattedtime = str(int(run_timer/60)) + ':0' + str(run_timer - (int(run_timer/60))*60)
                            else:
                                formattedtime = str(int(run_timer/60)) + ':' + str(run_timer - (int(run_timer/60))*60)
                            await channel.send('**Entering Stage ' + str(stagenum) + ' - ' + stage + ' [Time - ' + formattedtime + ']**')
                # Player joins
                elif "[Info   :     R2DSE] New player : " in line:
                    line = line.replace(
                        '[Info   :     R2DSE] New player : ', '**Player Joined - ')
                    line = line.replace(' connected. ', '')
                    line = re.sub(r" ?\([^)]+\)", "", line)
                    await channel.send(line + '**')
                # Player leaves
                elif "[Info   :     R2DSE] Ending AuthSession with : " in line:
                    line = line.replace(
                        '[Info   :     R2DSE] Ending AuthSession with : ', '**Player Left - ')
                    line = re.sub(r" ?\([^)]+\)", "", line)
                    await channel.send(line + '**')
        else:
            for line in Pygtail(str(logfile)):
                pass


async def server():
    """
    Checks if the server is running or not.

    Returns:
        Boolean: Used by functions calling this to check if running
    """
    global server_info
    global server_players
    try:
        server_info = a2s.info(server_address, 1.0)
        server_players = a2s.players(server_address)
        return True
    except:
#        print("Server error:", sys.exc_info()[0], sys.exc_info()[1]) #  Used for debugging
        return False


async def server_restart():
    """Checks every 120 minutes if no players are active then restarts the server."""
    server_restart = s_restart
    if server_restart == "true":
        print('Auto server restarting enabled')
        while server_restart == "true":
            await asyncio.sleep(7200)
            await server()
            if server_info.player_count == 0:
                await server_stop()
                await asyncio.sleep(10)
                os.startfile(ror2ds / "Risk of Rain 2.exe")
                print('Server restarted')
            elif server_info.player_count > 0:
                print('Players currently in server')
    else:
        print('Not restarting server')


async def chat_autostart(self):
    """Autostarts live chat output if it is enabled."""
    chat_autostart = c_autostart
    if chat_autostart:
        print('Auto chat output enabled')
        global repeat
        repeat = 1
        if os.path.exists(BepInEx / "LogOutput.log.offset"):
            try:
                os.remove(BepInEx / "LogOutput.log.offset")
            except Exception:
                print('Unable to remove offset! Old messages may be displayed.')
        while repeat == 1:
            await chat(self)
            await asyncio.sleep(1)
    else:
        print('Not outputting chat')


async def server_stop():
    """
    Stops the server.

    Returns:
        Boolean: Indicates whether server stopped or not
    """
    for proc in psutil.process_iter():
        exe = Path.cwd().joinpath(ror2ds, 'Risk of Rain 2.exe')
        try:
            processExe = proc.exe()
            if str(exe) == processExe:
                proc.kill()
                return True
        except:
            pass
    return False


async def find_dll():
    """
    Checks to see if the BotCommands plugin is installed on server.

    Returns:
        Boolean: If true it is, otherwise it is not
    """
    plugin_dir = (BepInEx / 'plugins')
    files = [file.name for file in plugin_dir.glob('**/*') if file.is_file()]
    if 'BotCommands.dll' in files:
        return True
    return False


class RoR2(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        asyncio.gather(chat_autostart(self), server_restart())

    # Counts reactions of commands with votes
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        global yes, no
        if payload.emoji.name == "✅":
            yes = yes + 1
        elif payload.emoji.name == "❌":
            no = no + 1
        else:
            pass

    # Start the RoR2 server
    @commands.command(name='start', help='Starts the server if it is not running')
    @commands.has_role(role)
    async def start(self, ctx):
        logging.info(f'{ctx.message.author.name} used {ctx.command.name}')
        # Checks to make sure the server is not running before starting it
        if await server():
            await ctx.send('Server is already running!')
        else:
            started = 1
            # Path of log file, removes before starting
            if os.path.exists(BepInEx / "LogOutput.log"):
                try:
                    os.remove(BepInEx / "LogOutput.log")
                except Exception:
                    print('Unable to remove log file')

            # Starts the server
            os.startfile(ror2ds / "Risk of Rain 2.exe")
            await ctx.send('Starting Risk of Rain 2 Server, please wait...')
            await asyncio.sleep(15)

            # After 15 seconds checks logs to see if server started
            while started == 1:
                with open(BepInEx / "LogOutput.log") as f:
                    for line in f:
                        if "Loaded scene lobby" in line:
                            await ctx.send('Server started successfully...')
                            started = 2
                            break
            
    # Exits the server
    @commands.command(name='stop', help='Stops the server if currently running')
    @commands.has_role(role)
    async def stop(self, ctx):
        logging.info(f'{ctx.message.author.name} used {ctx.command.name}')
        if await server():
            stopped = await server_stop()
            if stopped is True:
                await ctx.send('Risk of Rain 2 server shut down...')
            else:
                await ctx.send('Unable to stop server!')
        else:
            await ctx.send('Server is not running!')

    # Runs the update bat file, updates server via SteamCMD
    @commands.command(
        name='update',
        help='Updates the server, must be off before running this'
    )
    @commands.has_role(role)
    async def update(self, ctx):
        logging.info(f'{ctx.message.author.name} used {ctx.command.name}')
        # Checks to make sure the server is not running before updating it
        if await server() is False:
            await ctx.send('Updating server, please wait...')
            updated = 1
            # Path of log file, removes before starting
            if os.path.exists(steamcmd / "logs/content_log.txt"):
                try:
                    os.remove(steamcmd / "logs/content_log.txt")
                except Exception:
                    print('Unable to remove log file')
                await asyncio.sleep(2)
            os.startfile(steamcmd / "RoR2DSUpdate.bat")
            await asyncio.sleep(15)

            # After 15 seconds checks logs to see if server updated
            while updated == 1:
                with open(steamcmd / "logs/content_log.txt") as f:
                    for line in f:
                        if "AppID 1180760 scheduler finished" in line:
                            await ctx.send('Server updated...')
                            updated = 2
                            break
        else:
            await ctx.send('You must stop the server prior to updating!')

    # Restart the server with votes
    @commands.command(
        name='restart',
        help='Initializes a vote to restart the RoR2 server',
        usage='time'
    )
    async def restart(self, ctx, time=15):
        logging.info(f'{ctx.message.author.name} used {ctx.command.name}')
        if await server():
            global yes, no
            yes, no = 0, 0
            author = ctx.author
            message = await ctx.send('A restart vote has been initiated by '
                                     + f'{author.mention}. Please react to this message'
                                     + ' with your vote!')
            for emoji in ('✅', '❌'):
                await message.add_reaction(emoji)
            await asyncio.sleep(time)
            # Counts vote, if tie does nothing
            if yes == no:
                await ctx.send('It was a tie! There must be a majority to restart the '
                               + 'server!')
            # If 75% of player count wants to restart it will
            elif (yes - 1) >= (server_info.player_count * 0.75):
                started = 1
                stopped = await server_stop()
                if stopped is True:
                    await ctx.send('Risk of Rain 2 server shut down...')
                elif stopped is False:
                    await ctx.send('Unable to stop server!')
                await asyncio.sleep(5)

                # Path of log file, removes before starting
                if os.path.exists(BepInEx / "LogOutput.log"):
                    try:
                        os.remove(BepInEx / "LogOutput.log")
                    except Exception:
                        print('Unable to remove log file')

                # Starts the server
                os.startfile(ror2ds / "Risk of Rain 2.exe")
                await ctx.send('Starting Risk of Rain 2 Server, please wait...')
                await asyncio.sleep(15)

                # After 15 seconds checks logs to see if server started
                while started == 1:
                    with open(BepInEx / "LogOutput.log") as f:
                        for line in f:
                            if "Loaded scene lobby" in line:
                                await ctx.send('Server started successfully...')
                                started = 2
                                break
                # All other options
            else:
                await ctx.send('Restart vote failed!')
        else:
            await ctx.send('Server is not running, unable to restart...')

    # Kick a player with a majority vote
    # TODO: Add the ability to call this command with in-game chat by adding a
    # conditional to the chat command, so players can do it while in-game too.
    # Would have to add functionality for votes to count with in-game chat
    # though. (or not, if I want to leave that to the discord).
    @commands.command(
        name='votekick',
        help='Begins a vote to kick a player from the game',
        usage='playername'
    )
    async def votekick(self, ctx, *, kick_player):
        logging.info(f'{ctx.message.author.name} used {ctx.command.name}')
        if await server() and await find_dll() is True:
            global yes, no
            yes, no = 0, 0
            author = ctx.author
            time = 30
            containskickplayer = 0
            for player in server_players:
                if kick_player.upper() in player.name.upper():
                    containskickplayer = 1
                    kick_player = player.name
                    break
            if containskickplayer == 1:
                message = await ctx.send('A vote to kick ' + kick_player
                                         + f' has been initiated by {author.mention}. '
                                         + 'Please react to this message with your '
                                         + 'vote!')
                for emoji in ('✅', '❌'):
                    await message.add_reaction(emoji)
                await asyncio.sleep(time)
                # Counts vote, if tie does nothing
                if yes == no:
                    await ctx.send(
                        'It was a tie! There must be a majority to kick '
                        + kick_player
                    )
                # If 75% of player count wants to kick it will
                elif (yes - 1) >= (server_info.player_count * 0.75):
                    append = open(botcmd / "botcmd.txt", 'a')
                    append.write('kick "' + kick_player + '"\n')
                    append.close()
                    await ctx.send('Kicked player ' + kick_player)
                # If vote fails
                else:
                    await ctx.send('Vote failed. There must be a majority to kick '
                                   + kick_player
                                   )
            else:
                await ctx.send(kick_player + ' is not playing on the server')
        elif await server() is False:
            await ctx.send('Server is not running...')
        elif await find_dll() is False:
            await ctx.send('BotCommands plugin is not loaded on the server!')

    @votekick.error
    async def votekick_handler(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            if error.param.name == 'kick_player':
                await ctx.send('Please insert a partial or complete player name')

    # Ends the run with a majority vote
    # TODO: Add the ability to call this command with in-game chat by adding a
    # conditional to the chat command, so players can do it while in-game too.
    # Would have to add functionality for votes to count with in-game chat
    # though. (or not, if I want to leave that to the discord).
    @commands.command(
        name='endrun',
        help='Begins a vote to end the current run',
    )
    async def endrun(self, ctx):
        logging.info(f'{ctx.message.author.name} used {ctx.command.name}')
        if await server() and await find_dll() is True:
            global server_info
            if server_info.map_name in ('lobby', 'title'):
                await ctx.send('No run in progress.')
            else:
                global yes, no
                yes, no = 0, 0
                author = ctx.author
                time = 30
                message = await ctx.send('A vote to end the run has been initiated by '
                                         + f'{author.mention}. Please react to this message'
                                         + ' with your vote!')
                for emoji in ('✅', '❌'):
                    await message.add_reaction(emoji)
                await asyncio.sleep(time)
                # If 75% of player count wants to end the run it will
                if (yes - 1) >= (server_info.player_count * 0.75):
                    append = open(botcmd / "botcmd.txt", 'a')
                    append.write('run_end' + '\n')
                    append.close()
                    await ctx.send('Run ended, all players have been returned to the lobby')
                # If vote fails
                else:
                    await ctx.send('Vote failed. There must be a majority to end the run')
        elif await server() is False:
            await ctx.send('Server is not running...')
        elif await find_dll() is False:
            await ctx.send('BotCommands plugin is not loaded on the server!')

    # Executes say on the server
    @commands.command(
        name='say',
        help='Sends a message from the server',
        usage='message'
    )
    @commands.has_role(role)
    async def serversay(self, ctx, *, message):
        logging.info(f'{ctx.message.author.name} used {ctx.command.name}')
        if await server() and await find_dll() is True:
            append = open(botcmd / "botcmd.txt", 'a')
            append.write('say "' + message + '"\n')
            append.close()
        elif await server() is False:
            await ctx.send('Server is not running...')
        elif await find_dll() is False:
            await ctx.send('BotCommands plugin is not loaded on the server!')

    # EXPERIMENTAL - Use with caution
    # Passes on a command to be interpreted directly by the console
    # TODO: Test this when there's a lot of output, i.e. many players at once
    @commands.command(
        name='cmd',
        help='Passes on a command to be interpreted directly by the console',
        usage='command'
    )
    @commands.has_role(role)
    async def customcmd(self, ctx, *, cmd_with_args):
        logging.info(f'{ctx.message.author.name} used {ctx.command.name}')
        if await server() and await find_dll() is True:
            global server_info
            if server_info.map_name in ('lobby', 'title'):
                await ctx.send('No run in progress. Use >say if you want to send a message to the lobby.')
            else:
                append = open(botcmd / "botcmd.txt", 'a')
                append.write(cmd_with_args + '\n')
                append.close()
                findline = True
                consoleout = ''
                tempreader = Pygtail(str(logfile))
                while findline:
                    for line in tempreader:
    #                    print('line -' + str(line))  # DEBUG
                        if ('Server(0) issued' in line):
                            continue
                        elif ('is not a recognized ConCommand or ConVar.' in line):
                            await ctx.send(cmd_with_args + ' is not a valid command')
                            findline = False
                            break
                        elif ('[Info   : Unity Log]' in line):  # There's an \n in every line
                            consoleout = str(line.replace('[Info   : Unity Log] ',''))
                            findline = False
                            continue
                        elif ('[Error  : Unity Log]' in line):  # There's an \n in every line
                            consoleout = str(line.replace('[Error  : Unity Log] ','Error - '))
                            findline = False
                            continue
                        elif str(line) != '\n':
    #                        print('not newline')  # Debug
                            consoleout += str(line)
                            findline = False #  This was the trick, keep going through the lines until there are none left, and then the encompassing while loop will break
                            continue
                        else:
    #                        print('newline')  # Debug
                            findline = False
                            continue
                await ctx.send('**Server: **' + consoleout)
        elif await server() is False:
            await ctx.send('Server is not running...')
        elif await find_dll() is False:
            await ctx.send('BotCommands plugin is not loaded on the server!')

    # Executes give_item on the server
    @commands.command(
        name='giveitem',
        help='Gives a player a specified quantity of an item',
        usage='playername itemname qty'
    )
    @commands.has_role(role)
    async def giveitem(self, ctx, playername, itemname, qty="1"):
        logging.info(f'{ctx.message.author.name} used {ctx.command.name}')
        if await server() and await find_dll() is True:
            global server_info
            if server_info.map_name in ('lobby', 'title'):
                await ctx.send('No run in progress')
            else:
                containsplayer = False
                for player in server_players:
                    if playername.upper() in player.name.upper():
                        playername = player.name
                        containsplayer = True
                        break
                if containsplayer is True:
                    append = open(botcmd / "botcmd.txt", 'a')
                    append.write('give_item "' + itemname + '" '
                                 + qty + ' "' + playername + '"\n')
                    append.close()
                    findline = True
                    tempreader = Pygtail(str(logfile))
                    while findline:
                        for line in tempreader:
                            if ('[Info   : Unity Log] The requested object could not be '
                                    + 'found' in line):
                                await ctx.send(itemname + ' is not a valid item name')
                                findline = False
                                break
                            elif "[Info   : Unity Log] Gave" in line:
                                if "None" in line:
                                    pass
                                else:
                                    for key, value in item.items():
                                        if key in line:
                                            itemname = value
                                            break
                                    await ctx.send('Gave ' + qty + ' ' + itemname + ' to '
                                                   + playername)
                                    findline = False
                                    break
                elif containsplayer is False:
                    await ctx.send(playername + ' is not playing on the server')
        elif await server() is False:
            await ctx.send('Server is not running...')
        elif await find_dll() is False:
            await ctx.send('BotCommands plugin is not loaded on the server!')

    @giveitem.error
    async def giveitem_handler(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            if error.param.name == 'playername':
                logging.warning(
                    f'{ctx.message.author.name} caused an error with '
                    + f'{ctx.command.name} | Message: {ctx.message.content} | '
                    + f'Error: {error}')
                await ctx.send('Please enter a partial or complete player name')
            if error.param.name == 'itemname':
                logging.warning(
                    f'{ctx.message.author.name} caused an error with '
                    + f'{ctx.command.name} | Message: {ctx.message.content} | '
                    + f'Error: {error}')
                await ctx.send('Please enter a valid item name')

    # Executes give_equip on the server
    @commands.command(
        name='giveequip',
        help='Gives a player a specified equipment',
        usage='playername equipname'
    )
    @commands.has_role(role)
    async def giveequip(self, ctx, playername, equipname):
        logging.info(f'{ctx.message.author.name} used {ctx.command.name}')
        if await server() and await find_dll() is True:
            global server_info
            if server_info.map_name in ('lobby', 'title'):
                await ctx.send('No run in progress')
            else:
                containsplayer = False
                for player in server_players:
                    if playername.upper() in player.name.upper():
                        playername = player.name
                        containsplayer = True
                        break
                if containsplayer is True:
                    append = open(botcmd / "botcmd.txt", 'a')
                    append.write('give_equip "' + equipname + '" "'
                                 + playername + '"\n')
                    append.close()
                    findline = True
                    tempreader = Pygtail(str(logfile))
                    while findline:
                        for line in tempreader:
                            if ('[Info   : Unity Log] The requested object could not be '
                                    + 'found' in line):
                                await ctx.send(equipname + ' is not a valid equipment name')
                                findline = False
                                break
                            elif "[Info   : Unity Log] Gave" in line:
                                if "None" in line:
                                    pass
                                else:
                                    for key, value in equip.items():
                                        if key in line:
                                            equipname = value
                                            break
                                    await ctx.send('Gave ' + equipname + ' to '
                                                   + playername)
                                    findline = False
                                    break
                elif containsplayer is False:
                    await ctx.send(playername + ' is not playing on the server')
        elif await server() is False:
            await ctx.send('Server is not running...')
        elif await find_dll() is False:
            await ctx.send('BotCommands plugin is not loaded on the server!')

    @giveequip.error
    async def giveequip_handler(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            if error.param.name == 'playername':
                logging.warning(
                    f'{ctx.message.author.name} caused an error with '
                    + f'{ctx.command.name} | Message: {ctx.message.content} | '
                    + f'Error: {error}')
                await ctx.send('Please enter a partial or complete player name')
            if error.param.name == 'equipname':
                logging.warning(
                    f'{ctx.message.author.name} caused an error with '
                    + f'{ctx.command.name} | Message: {ctx.message.content} | '
                    + f'Error: {error}')
                await ctx.send('Please enter a valid equipment name')

    # Displays the status of the server
    @commands.command(
        name='status',
        help='Displays the status of the Risk of Rain 2 server'
    )
    async def status(self, ctx):
        logging.info(f'{ctx.message.author.name} used {ctx.command.name}')
        if await server():
            # Create embed
            embed = discord.Embed(
                title='Server Information',
                colour=discord.Colour.blue()
            )

            # Creates the string of player names used in the embed
            player_names = []
            for player in server_players:
                player_names.append(player.name)
            player_names = ("\n".join(map(str, player_names)))

            # Convert Steam map name to game name
            for key, value in stages.items():
                if key in server_info.map_name:
                    stage = value
                    break

            # Embed information
            embed.set_footer(
                text=f'Requested by {ctx.message.author.name}',
                icon_url=self.bot.user.avatar_url
            )
            embed.set_thumbnail(url=self.bot.user.avatar_url)
            embed.set_author(name=self.bot.guilds[0])
            embed.add_field(name='Server Name',
                            value=f'{server_info.server_name}', inline=False)
            embed.add_field(name='Current Stage', value=f'{stage}', inline=False)
            embed.add_field(
                name='Player Count',
                value=f'{server_info.player_count}/{server_info.max_players}', inline=False)
            if server_info.player_count == 0:
                pass
            else:
                embed.add_field(
                    name='Players', value=player_names, inline=False)
            embed.add_field(name='Server Ping',
                            value=int(server_info.ping * 1000), inline=False)

            # Send embed
            await ctx.send(embed=embed)
        else:
            await ctx.send('Server is currently offline.')

    # Send modlist to chat
    @commands.command(
        name='mods',
        help='Lists all the mods currently running on the server'
    )
    async def mods(self, ctx):
        logging.info(f'{ctx.message.author.name} used {ctx.command.name}')
        mods = []
        with open(BepInEx / "LogOutput.log") as f:
            for line in f:
                if "[Info   :   BepInEx] Loading" in line:
                    line = line[30:]
                    head, sep, tail = line.partition(' ')
                    if head in hidden_mods:
                        pass
                    else:
                        mods.append(head)
        mods = ("\n".join(map(str, mods)))
        mod_embed = discord.Embed(colour=discord.Colour.blue())
        mod_embed.set_footer(
            text=f'Requested by {ctx.message.author.name}',
            icon_url=self.bot.user.avatar_url
        )
        mod_embed.add_field(name='Mods', value=mods, inline=False)
        await ctx.send(embed=mod_embed)

    # Output RoR server chat to Discord
    @commands.command(
        name='start_chat',
        help='Displays live chat from the server to the specified channel in Discord'
    )
    @commands.has_role(role)
    async def start_chat(self, ctx):
        logging.info(f'{ctx.message.author.name} used {ctx.command.name}')
        await ctx.send('Displaying chat messages from the server!')
        global repeat
        repeat = 1
        if os.path.exists(BepInEx / "LogOutput.log.offset"):
            try:
                os.remove(BepInEx / "LogOutput.log.offset")
            except Exception:
                print('Unable to remove offset! Old messages may be displayed.')
        while repeat == 1:
            await chat(self)
#            await asyncio.sleep(1)

    # Stop outputting live server chat to Discord
    @commands.command(
        name='stop_chat',
        help='Stops outputting live chat from the server'
    )
    @commands.has_role(role)
    async def stop_chat(self, ctx):
        logging.info(f'{ctx.message.author.name} used {ctx.command.name}')
        global repeat
        if repeat == 0:
            await ctx.send('Not outputting chat to Discord!')
        else:
            repeat = 0
            await ctx.send('Stopping outputting live chat to the server...')

    # Print server configuration
    @commands.command(name='config', help='Prints the server configuration')
    @commands.has_role(role)
    async def config(self, ctx):
        await ctx.send('Coming soon!')


def setup(bot):
    """Loads the cog into bot.py."""
    bot.add_cog(RoR2(bot))
    print('Loaded cog: RoR2.py')


def teardown(bot):
    """Prints to termianl when cog is unloaded."""
    print('Unloaded cog: RoR2.py')
