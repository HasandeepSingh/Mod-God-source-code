import os
import discord, os, pymongo, datetime, logging, sys, random
from threading import Timer
from datetime import timedelta
from discord import app_commands
from discord.ext import commands
from configManager import ConfigManager
import time as t

config_commands = app_commands.Group(name="config", description="Configuration commands")
guild_config_commands = app_commands.Group(name="guild", parent=config_commands, description="Guild configuration commands")
# start -
class CustomFormatter(logging.Formatter):

    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    blue = "\x1b[34m"
    reset = "\x1b[0m"
    format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)"
    format2 = format

    FORMATS = {
        logging.DEBUG: grey + format + reset,
        logging.INFO: blue + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        text = formatter.format(record)
        with open('log.txt', 'a') as f:
            unformattedText = text
            for x in self.FORMATS.values():
                unformattedText = unformattedText.replace(x.replace(self.format2, "").replace(self.reset, ""), "")
            f.write(unformattedText.replace(self.reset, ""))
            f.write('\n')
        return text

logger = logging.getLogger()
logger.setLevel(logging.INFO)

for handler in logger.handlers:
    logger.removeHandler(handler)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

ch.setFormatter(CustomFormatter())

logger.addHandler(ch)
logger.handlers[0].stream = sys.stdout

logger.info("====== Starting Mod God bot ======")

clusterConn = pymongo.MongoClient('mongodb+srv://root:root@modgod.utok6cp.mongodb.net/?retryWrites=true&w=majority')
cluster = clusterConn['modgod']
"""
categorize db
example = cluster.example
bans = cluster.bans
"""
guilds = cluster.guilds
users = cluster.users

configManager = ConfigManager(guilds, users)
abuse_words= ["fuck", "Fuck", "FUCK"]

intents = discord.Intents.default()
client = discord.AutoShardedClient(intents=intents)
tree = app_commands.CommandTree(client)

@client.event
async def on_guild_join(guild):
    configManager.upgradeGuildConfig(guild.id, save = True)
    await guild.text_channels[0].send("Hi, thanks for adding `Mod God`!\n\nIt can help you with moderation, and is a replacement for Discord's AutoMod.\nTho the bot won't start working once it's added! You **must** configure it by running `/guild-config`. From there, you can setup the bot how you like! It's your choice how to use it\n\nAgain, thanks for choosing this bot!")

@tree.command(name = "invite", description="Add the bot to your server")
async def invite_bot(interaction: discord.Interaction):
    embed = discord.Embed(title = '[Invite this bot to your server](https://discord.com/api/oauth2/authorize?client_id=978550932117803069&permissions=-1&scope=bot%20applications.commands)', description = '**Ignore that it asks you to provide every permission**\nIt\'s made intentionally, and reserved for new updates so you won\'t have to re-invite the bot\nAnd also we\'re too lazy to select the permissions our bot actually needs')
    await interaction.response.send_message(ephemeral=True, embeds = [embed])

games = app_commands.Group(name="games", description="Games")

@games.command(name="guess-number", description="Guess the number!")
async def number_guess(interaction: discord.Interaction):
    number = random.randint(1, 100)
    attempts = 1
    while True:
        modal = discord.ui.Modal(title="Guess the number!")
        answer = discord.ui.TextInput(label="Your guess from 1 to 100", max_length=3, min_length=1)
        modal.add_item(answer)
        while True:
            await interaction.response.send_modal(modal)
            def c(i):
                try:
                    return i.data and 'custom_id' in i.data and i.data['custom_id'] == modal.custom_id and int(i.data['components'][0]['components'][0]['value'])
                except:
                    return False
            interaction = await client.wait_for('interaction', check=c)
            print("Got an interaction")
            try:
                n = int(interaction.data['components'][0]['components'][0]['value'])
                print("Valid")
                break
            except:
                continue
        await interaction.response.defer(ephemeral=True)
        view = discord.ui.View(timeout=None)
        b = discord.ui.Button(label="Put another guess", style=discord.ButtonStyle.success)
        view.add_item(b)
        if n > number:
            await interaction.followup.send(content="Put a smaller number", ephemeral=True, view=view)
        elif n < number:
            await interaction.followup.send(content="Put a bigger number", ephemeral=True, view=view)
        else:
            await interaction.followup.send(content=f"You guessed the number in {attempts} attempt(s)!", ephemeral=True)
            return
        interaction = await client.wait_for('interaction', check=lambda i: i.data and 'custom_id' in i.data and i.data['custom_id'] == b.custom_id)
        view.stop()
        attempts += 1

@client.event
async def on_member_ban(guild, user):
    channel_id_for_reports = configManager.getGuildConfigValue(guild.id, "modlogs.channel")
    if channel_id_for_reports:
        channel = client.get_channel(channel_id_for_reports)
        embed = discord.Embed(color=0xFF0000, title="Member banned", description=f"Member banned: <@{user.id}> ({user.name}#{user.discriminator})")
        await channel.send(embeds=[embed])

@client.event
async def on_member_join(guild, user):
    channel_id_for_welcome = configManager.getGuildConfigValue(guild.id, "ch.wel-channel")
    if channel_id_for_welcome:
      channel = client.get_channel(channel_id_for_welcome)
      await channel.send(f"**{user.username}** Joined {guild.name}")
    else:
        pass #make a channel and send it there
        

@client.event
async def on_message_delete(msg):
  guild = msg.guild
  user = msg.author
  channel_id_for_logs = configManager.getGuildConfigValue(guild.id, "modlogs.channel")
  if channel_id_for_logs:
    channel = client.get_channel(channel_id_for_logs)
    embed = discord.Embed(title= "Message Deleted", description= f"Author = {user} in <#{msg.channel.id}>")
    await channel.send(embeds = [embed])

@client.event
async def on_member_remove(guild, user):
  channel_id_to_bye = configManager.getGuildConfigValue(guild.id, "ch.lea-channel")
  if channel_id_to_bye:
    channel = client.get_channel(channel_id_to_bye)
    await channel.send(f"**{user}** Left {guild.name}")

@tree.command(name = "delete-bot", description="You want to delete this bot? How sad!")
@commands.has_permissions(kick_members=True)
async def delete_bot(interaction: discord.Interaction):
    await interaction.response.send_message(content="How sad, you're removing this bot! Goodbye, hope you had good time with this bot", ephemeral=True)
    await interaction.guild.leave()

@tree.command(name = "ban", description = "Ban someone!")
@commands.has_permissions(ban_members = True)
@app_commands.describe(member="Who do you want to punish", reason = "(Optional) why?")
async def ban(interaction, member: discord.Member, reason: str = "No reason specified"):
    try:
        await member.ban(reason=reason)
        await interaction.response.send_message(f"Banned!\nUser: {member}\nMod: {interaction.author}\nReason: {reason}")
    except:
        await interaction.response.send_message("Sorry, an error occurred", ephemeral=True)

@tree.command(name="mute", description="Mute someone")
@app_commands.describe(member="Who do you want to punish", seconds = "How many seconds do you want for mute to stay?")
async def mute(interaction, member: discord.Member, seconds: int):
    try:
        await member.timeout(timedelta(seconds=seconds))
        await interaction.response.send_message("Muted!", ephemeral=True)
    except:
        await interaction.response.send_message("Failed to mute", ephemeral=True)

@tree.command(name = "kick", description = "Kick someone!")
@app_commands.describe(member="Who do you want to punish", reason = "(Optional) why?")
@commands.has_permissions(kick_members = True)
async def kick(interaction, member: discord.Member, reason: str = "No reason given"):
    try:
        await member.kick(reason=reason)
        await interaction.response.send_message(f"Kicked!\nUser: {member}\nMod: {interaction.author}\nReason: {reason}")
    except:
        await interaction.response.send_message("Sorry, an error occupated", ephemeral=True) 

@guild_config_commands.command(name="upgrade", description="If a new update released but you didn't got new features, run this command")
@commands.has_permissions(manage_guild=True)
async def upgradeConfig(interaction: discord.Interaction):
    if not interaction.guild:
        await interaction.response.send_message("You're not in a server :/", ephemeral=True)
        return
    await interaction.response.send_message("Upgrading your config, please wait...", ephemeral=True)
    guildConfig = guilds.find_one({
        'guild_id': interaction.guild.id
    })
    try:
        configManager.upgradeGuildConfig(interaction.guild.id, guildConfig, save=True)
    except:
        await interaction.edit_original_response(content="Could not upgrade your config. Most probably it's not corrupted, but even if it's not - contact us on our support server (/support)")
        raise
        return
    await interaction.edit_original_response(content="Done, no errors")

@tree.command(name="clear", description="Clears messages")
@commands.has_permissions(manage_messages=True)
@app_commands.describe(amount="How many messages to purge?")
async def clear(interaction, amount: int):
    await interaction.response.defer(ephemeral=True)
    try:
        await interaction.channel.purge(limit=amount)
        await interaction.followup.send(f"Cleared {amount} message(s)")
        
    except:
        await interaction.followup.send("Sorry, an error occupated", ephemeral=True)

@tree.command(name = "support", description = "Invite to the support server")
async def support(interaction):
  embed = discord.Embed(title="Support server", description="[Join Now](https://discord.gg/rdnqePn4V6)", color=0x00FFFF)
  await interaction.response.send_message(embed=embed, ephemeral=True)

author_msg_times = {} # For anti-spam

@guild_config_commands.command(name = 'edit', description = "Edit server config (You must have Manage Server permission)")
@commands.has_permissions(manage_guild=True)
@app_commands.describe(private="Should your configuration session be visible only to you or to everyone?")
async def guild_config(interaction: discord.Interaction, private: bool):
    await interaction.response.defer(ephemeral=private)
    if not interaction.guild:
        await interaction.followup.send("You're not in a server!")
        return
    del private
    path = ""
    modal = None
    while True:
        guildConfig = configManager.getGuildConfigValue(interaction.guild.id, path)
        if not modal:
            select_menu = edit_button = None
            view = discord.ui.View()
            back_button = discord.ui.Button(style=discord.ButtonStyle.secondary, label="Go back")
            if type(guildConfig) == dict:
                description = guildConfig.get('_comment', 'Edit your config here')
                embed = discord.Embed(title='Config editor', description=description, color=0x00FFFF)
                select_menu = discord.ui.Select(placeholder = "Select config key")
                for x in guildConfig.keys():
                    if x != '_id' and x != 'guild_id' and not x.startswith('_comment'):
                        select_menu.add_option(value=x, label=guildConfig.get('_comment_' + x, x), description=f"Key: {x}")
                view.add_item(select_menu)
                if path:
                    view.add_item(back_button)
                await interaction.edit_original_response(embeds=[embed], view=view)
            else:
                embed = discord.Embed(title='Config editor', description=f'Value of this element is: {guildConfig}', color=0x00FFFF)
                view = discord.ui.View()
                edit_button = discord.ui.Button(label='Edit value', style=discord.ButtonStyle.primary)
                view.add_item(back_button)
                view.add_item(edit_button)
                await interaction.edit_original_response(embeds=[embed], view=view)
        else:
            logger.info("Modal exists, skipping update")
        def check(interaction2):
            if interaction2.user.id != interaction.user.id:
                return False
            try:
                try:
                    element = select_menu.custom_id
                except:
                    element = edit_button.custom_id
                if modal:
                    return interaction2.data['custom_id'] in [back_button.custom_id, element, modal.custom_id]
                else:
                    return interaction2.data['custom_id'] in [back_button.custom_id, element]
            except KeyError:
                return False
        click = await client.wait_for('interaction', check = check)
        logger.info(click.data)
        if modal and click.data['custom_id'] == modal.custom_id:
            await click.response.defer(thinking=True, ephemeral=True)
            try:
                newValueType = type(configManager.getGuildConfigValue(interaction.guild.id, path))
                newValue = newValueType(click.data['components'][0]['components'][0]['value'])
                configManager.setGuildConfigValue(interaction.guild.id, path, newValue=newValue)
                await click.followup.send(content='Updated! (Wait for config editor to update to see the new value)')
            except:
                await click.followup.send(content='Oops, failed to convert the value. Are you sure you inputted it correctly? (Float values must be seperated by a `.` instead of `,`)')
                raise
            modal = None
        elif click.data['component_type'] == 3:
            await click.response.defer()
            value = click.data['values'][0]
            path = path.split('.')
            path.append(value)
            if '' in path:
                path.remove('')
            path = '.'.join(path)
            modal = None
        elif click.data['component_type'] == 2:
            if click.data['custom_id'] == back_button.custom_id:
                await click.response.defer()
                path = path.split('.')
                path.pop(-1)
                path = '.'.join(path)
                modal = None
            elif click.data['custom_id'] == edit_button.custom_id:
                if type(configManager.getGuildConfigValue(interaction.guild.id, path)) == bool:
                    await click.response.defer()
                    configManager.setGuildConfigValue(interaction.guild.id, path, not configManager.getGuildConfigValue(interaction.guild.id, path))
                    continue
                modal = discord.ui.Modal(title = 'Editing value')
                modal.add_item(discord.ui.TextInput(label="Value for this setting", placeholder=f"Type of this value: {type(configManager.getGuildConfigValue(interaction.guild.id, path)).__name__}"))
                await click.response.send_modal(modal)
                
        else:
            break
info = app_commands.Group(name="info", description = "Info about the bot")
@info.command(name = "shards", description="Bot shards info")
async def shards_info(interaction: discord.Interaction):
    await interaction.response.send_message(f"Bot currently has {len(client.shards)} shards", ephemeral=True)
@info.command(name = "bot", description = "Bot info")
async def info(interaction):
    await interaction.response.send_message("**Bot info**\nBot owner: `Coding Way (Official)#4991`\nHelper(s): `GEOEGII555#5854`, the bot owner\nMultiple bot developers are helping to develop this bot, thanks to them!\n**Common problems**:\nInteraction failed - 2 reasons:\n1. The bot didn't responded fast enough, this happens sometimes\n2. You don't have permissions to run that command\nError while banning/kicking/muting: The bot can't punish the user. Either the bot has no permissions to do so, the member has Administrator or Moderate members permissions, the member is the server owner or member's highest role is higher than bot's highest role\nError while purging messages - bot has no permissions to delete messages in that channel or you're trying to delete too old/too many messages\nAlmost nothing is working, only this and /support commands! - If you recently added this bot or a new update got released, try running /upgrade-config. If it didn't worked, contact our support server (I'm sure the /support command will always work if this one does too)", ephemeral=True)

@client.event
async def on_message(interaction):
    global author_msg_times
    
    if configManager.getGuildConfigValue(interaction.guild.id, 'abuse.enable_abuse_protection') == True:
        words = abuse_words
        for word in words:
            if word in interaction.content.lower():
                await interaction.channel.send("Abuse is not released yet")
                break
    if interaction.author == client.user or not interaction.guild: # Stop anti-spam from replying to the bot itself or in DMs
        return

    author_id = interaction.author.id
    if configManager.getGuildConfigValue(interaction.guild.id, 'antispam.enabled_spam_protection') == True:
        time_window_milliseconds = configManager.getGuildConfigValue(interaction.guild.id, 'antispam.TIME_FRAME_BETWEEN_MSGS_MAX_SECONDS') * 1000
        max_msg_per_window = configManager.getGuildConfigValue(interaction.guild.id, 'antispam.MAX_COUNT_IN_TIME_FRAME')
        logging.debug(f"Time window (milliseconds): {time_window_milliseconds}, max messages per window: {max_msg_per_window}")
        curr_time = datetime.datetime.now().timestamp() * 1000
    
        if not author_msg_times.get(author_id, False):
            author_msg_times[author_id] = []
        
        author_msg_times[author_id].append(curr_time)
        
        expr_time = curr_time - time_window_milliseconds
        expired_msgs = [
            msg_time for msg_time in author_msg_times[author_id]
            if msg_time < expr_time
        ]
        for msg_time in expired_msgs:
            author_msg_times[author_id].remove(msg_time)
        # ^ note: we probably need to use a mutex here. Multiple threads
        # might be trying to update this at the same time. Not sure though.
        
        if len(author_msg_times[author_id]) >= max_msg_per_window:
            author_msg_times[author_id] = []
            msg = configManager.getGuildConfigValue(interaction.guild.id, 'antispam.SPAM_MESSAGE')
            if not msg:
                await interaction.reply(f"<@{interaction.author.id}> Stop spamming!")
            else:
                await interaction.reply(msg.replace('%user%', str(interaction.author.id)))
            if configManager.getGuildConfigValue(interaction.message.guild.id, 'antispam.TIMEOUT_TIME'):
                try:
                    await interaction.author.timeout(timedelta(seconds=configManager.getGuildConfigValue(interaction.guild.id, 'antispam.TIMEOUT_TIME')))
                except:
                    await interaction.channel.send(f"Could not timeout <@{interaction.author.id}>")
role = app_commands.Group(name="role", description="Role commands")

@role.command(name = 'give', description = "Gives Role to the member of the server")
@commands.has_permissions(manage_roles=True)
@app_commands.describe(member="Member to give role to", role="Role to give to the member")
async def add_role(interaction, member: discord.Member, *, role: discord.Role):
    try:
        await member.add_roles(role)
        await interaction.response.send_message(f'{member.mention} has been given the {role} role.', ephemeral=True)
    except:
        await interaction.response.send_message("An error occurred while giving the role to the member!", ephemeral=True)

@role.command(name="take", description="Removes the Role from the member of the server")
@commands.has_permissions(manage_roles=True)
@app_commands.describe(member="Member to take role from", role="Role to take from member")
async def remove_role(interaction, member: discord.Member, *, role: discord.Role):
    try:
        await member.remove_roles(role)
        await interaction.response.send_message(f"{role} has been removed from {member.mention}.", ephemeral=True)
    except:
        await interaction.response.send_message("An error occurred while removing the role frim the member!", ephemeral=True)

@role.command(name="create", description="Creates a Role in the server")
@commands.has_permissions(manage_roles=True)
async def create_role(interaction, role_name: str):
	try: #bruh it's interaction not interaction
		guild = interaction.guild
		new_role = await guild.create_role(name=role_name)
		await interaction.response.send_message(f"Role **{new_role.name}** has been created!", ephemeral=True)
	except:
		await interaction.response.send_message("An error has been occurred while creating the role!", ephemeral=True)

@role.command(name="delete", description="Deletes a role from the server")
@app_commands.describe(role="Which role to delete")
@commands.has_permissions(manage_roles=True)
async def delete_role(interaction, role: discord.Role):
	try:
		await role.delete(role)
		await interaction.response.send_message(f"Delete {role} for the server!", ephemeral=True)
	except:
		await interaction.response.send_message("An error has been occurred while deleting the role from the server!", ephemeral=True)


tree.add_command(role)
tree.add_command(config_commands)
tree.add_command(games)
tree.add_command(info)

@role.command(name="info", description="Get info about a role")
@app_commands.describe(role="Role you want to get info about")
async def role_info(interaction: discord.Interaction, role: discord.Role):
    pass # Add later
    embed = discord.Embed(color=0x00FFFF, )



@client.event
async def on_ready():
    await tree.sync()
    logger.info("Ready! Mod God is the best!")
    
    act = discord.Activity(type=discord.ActivityType.listening, name="to /info bot")
    await client.change_presence(activity=act)

try:
    client.run('TOKEN HERE')
except:
    raise
