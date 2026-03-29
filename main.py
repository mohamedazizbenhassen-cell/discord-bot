import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os
from datetime import timedelta, datetime

user_messages = {}  # {user_id: [timestamps]}
SPAM_THRESHOLD = 5  # messages
SPAM_INTERVAL = 10  # seconds
MUTE_DURATION = 60  # minutes

load_dotenv()
token = os.getenv("discord_token")

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='a')

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

secret_role = "admin"

@bot.event
async def on_ready():
     print(f"We are ready to go in, {bot.user.name}")

@bot.event
async def on_member_join(member):
     await member.send(f"welcome to the server {member.name}")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    user_id = message.author.id
    now = discord.utils.utcnow()


    timestamps = user_messages.get(user_id, [])
    timestamps = [t for t in timestamps if (now - t).total_seconds() < SPAM_INTERVAL]
    timestamps.append(now)
    user_messages[user_id] = timestamps

    if len(timestamps) >= SPAM_THRESHOLD:
        mute_until = now + timedelta(minutes=MUTE_DURATION)
        try:
            await message.author.timeout(mute_until, reason="Spamming messages")
            await message.channel.send(
                f"{message.author.mention} has been muted for {MUTE_DURATION} minutes for spamming."
            )
            user_messages[user_id] = []
        except Exception as e:
            print(f"Could not mute user: {e}")

    bad_words = ["3asba", "nik omek", "9a7ba"]

    content = message.content.lower()

    if any(word in content for word in bad_words):
        try:
            await message.delete()
            await message.channel.send(
                f"{message.author.mention} - don't use that word!"
            )
        except Exception as e:
            print(f"Could not delete message: {e}")

    await bot.process_commands(message)

@bot.command()
async def hello(ctx):
     await ctx.send(f"Hello {ctx.author.mention}")

@bot.command()
async def assign(ctx):
    if ctx.author.id != 411985462346121216:
        await ctx.send("You are not allowed to use this command.")
        return

    role = discord.utils.get(ctx.guild.roles, name=secret_role)
    if role:
        await ctx.author.add_roles(role)
        await ctx.send(f"{ctx.author.mention} is now assigned to {secret_role}")
    else:
        await ctx.send("Role does not exist.")


@bot.command()
async def remove(ctx):
     role = discord.utils.get(ctx.guild.roles, name=secret_role)
     if role:
          await ctx.author.remove_roles(role)
          await ctx.send(f"{ctx.author.mention} has had the {secret_role} removed")
     else:
          await ctx.send("role does not exist")

@bot.command()
async def dm(ctx, *, msg):
     await ctx.author.send(f"you said {msg}")

@bot.command()
async def reply(ctx):
     await ctx.reply("this is a reply to your message!")

@bot.command()
async def poll(ctx, *, question):
     embed = discord.Embed(title="new poll", description=question)
     poll_message = await ctx.send(embed=embed)
     await poll_message.add_reaction("👍")
     await poll_message.add_reaction("👎")

@bot.command()
@commands.has_role(secret_role)
async def secret(ctx):
     await ctx.send("welcome to the club!")

@secret.error
async def secret_error(ctx, error):
     if isinstance(error, commands.MissingRole):
        await ctx.send("you do not have the permission to do that")

@bot.command()
@commands.has_permissions(manage_roles=True)
async def giverole(ctx, member: discord.Member, *, role_name):
    role_name = role_name.strip()
    role = discord.utils.find(lambda r: r.name.lower() == role_name.lower(), ctx.guild.roles)

    if not role:
        await ctx.send(f"Role `{role_name}` does not exist.")
        return

    if role.position >= ctx.author.top_role.position:
        await ctx.send("You can't assign a role equal or higher than your top role.")
        return

    if role.position >= ctx.guild.me.top_role.position:
        await ctx.send("I can't assign a role higher than my top role.")
        return

    try:
        await member.add_roles(role)
        await ctx.send(f"{member.mention} has been given the role `{role.name}`!")
    except Exception as e:
        await ctx.send("I couldn't assign the role.")
        print(f"Role assignment error: {e}")

@bot.command()
@commands.has_permissions(manage_roles=True)
async def removerole(ctx, member: discord.Member, *, role_name):
    role_name = role_name.strip()
    role = discord.utils.find(lambda r: r.name.lower() == role_name.lower(), ctx.guild.roles)

    if not role:
        await ctx.send(f"Role `{role_name}` does not exist.")
        return

    if role.position >= ctx.author.top_role.position:
        await ctx.send("You can't remove a role equal or higher than your top role.")
        return

    if role.position >= ctx.guild.me.top_role.position:
        await ctx.send("I can't remove a role higher than my top role.")
        return

    try:
        await member.remove_roles(role)
        await ctx.send(f"{member.mention} has had the role `{role.name}` removed!")
    except Exception as e:
        await ctx.send("I couldn't remove the role.")
        print(f"Role removal error: {e}")


@bot.command()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason=None):
     if member == ctx.author:
          await ctx.send("You can't target yourself.")
          return

     if member == bot.user:
          await ctx.send("You can't target me.")
          return

     if member.top_role >= ctx.author.top_role:
          await ctx.send("You can't target someone with equal or higher role.")
          return

     reason = reason or "No reason provided"
     try:
          await member.ban(reason=reason)
          await ctx.send(f"{member.mention} has been banned. Reason: {reason}")
     except:
          await ctx.send("I couldn't ban this user.")

@ban.error
async def ban_error(ctx, error):
     if isinstance(error, commands.MissingPermissions):
          await ctx.send("You don't have permission to use this command.")
     elif isinstance(error, commands.BotMissingPermissions):
          await ctx.send("I don't have permission to ban members.")
     elif isinstance(error, commands.MemberNotFound):
          await ctx.send("User not found.")

@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int):
    if amount <= 0:
        await ctx.send("You must delete at least 1 message.")
        return
    deleted = await ctx.channel.purge(limit=amount+1)
    await ctx.send(f"Deleted {len(deleted)-1} messages.", delete_after=5)

@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason=None):
     if member == ctx.author:
          await ctx.send("You can't target yourself.")
          return

     if member == bot.user:
          await ctx.send("You can't target me.")
          return

     if member.top_role >= ctx.author.top_role:
          await ctx.send("You can't target someone with equal or higher role.")
          return

     reason = reason or "No reason provided"
     try:
          await member.kick(reason=reason)
          await ctx.send(f"{member.mention} has been kicked. Reason: {reason}")
     except:
          await ctx.send("I couldn't kick this user.")

@kick.error
async def kick_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("You don't have permission to use this command.")
    elif isinstance(error, commands.BotMissingPermissions):
        await ctx.send("I don't have permission to kick members.")
    elif isinstance(error, commands.MemberNotFound):
        await ctx.send("User not found.")

@bot.command()
@commands.has_permissions(moderate_members=True)
async def timeout(ctx, member: discord.Member, time: int, *, reason=None):
     if member == ctx.author:
          await ctx.send("You can't target yourself.")
          return

     if member == bot.user:
          await ctx.send("You can't target me.")
          return

     if member.top_role >= ctx.author.top_role:
          await ctx.send("You can't target someone with equal or higher role.")
          return

     reason = reason or "No reason provided"
     try:
          await member.timeout(discord.utils.utcnow() + timedelta(minutes=time), reason=reason)
          await ctx.send(f"{member.mention} has been timed out for {time} minutes. Reason: {reason}")
     except:
          await ctx.send("I couldn't timeout this user.")

@timeout.error
async def timeout_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("You don't have permission to use this command.")
    elif isinstance(error, commands.BotMissingPermissions):
        await ctx.send("I don't have permission to timeout members.")
    elif isinstance(error, commands.MemberNotFound):
        await ctx.send("User not found.")

bot.run(token,log_handler=handler,log_level=logging.DEBUG)


