# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.


import discord
import logging
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timezone
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID"))

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.messages = True

bot = commands.Bot(command_prefix="!", intents=intents)

class LinkAccessView(discord.ui.View):
    def __init__(self, url: str, creator: discord.User):
        super().__init__(timeout=None)
        self.url = url
        self.creator = creator

    @discord.ui.button(label="Access Link", style=discord.ButtonStyle.green)
    async def access_link(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await interaction.response.send_message(f"Here is the link:\n{self.url}", ephemeral=True)

            log_channel = bot.get_channel(LOG_CHANNEL_ID)

            embed = discord.Embed(
                title="Link Accessed",
                description=f"{interaction.user.mention} (ID: {interaction.user.id}) accessed a link from {self.creator.mention} (ID: {self.creator.id})",
                color=discord.Color.green()
            )
            embed.set_thumbnail(url=interaction.user.avatar.url if interaction.user.avatar else interaction.user.default_avatar.url)
            embed.set_footer(text=f"Message ID: {interaction.message.id}")

            if log_channel:
                await log_channel.send(embed=embed)
        except Exception as e:
            await interaction.response.send_message(f"Error accessing link: {e}", ephemeral=True)
            logging.error(f"Error in LinkAccessView: {e}")

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Bot is ready. Logged in as {bot.user}")

@bot.tree.command(name="link", description="Share a link")
async def link(interaction: discord.Interaction, url: str):
    if interaction.channel.type == discord.ChannelType.private:
        await interaction.response.send_message("This command cannot be used in DMs.", ephemeral=True)
        return

    await interaction.response.send_message("Creating link...", ephemeral=True)

    try:
        embed = discord.Embed(
            title="Link Shared",
            description=f"Click the button to access the link by {interaction.user.mention}",
            color=discord.Color.blue()
        )
        embed.set_footer(text=f"Shared by {interaction.user.name} | {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}")

        view = LinkAccessView(url, interaction.user)
        message = await interaction.channel.send(embed=embed, view=view)

        log_channel = bot.get_channel(LOG_CHANNEL_ID)
        message_link = f"https://discord.com/channels/{interaction.guild.id}/{interaction.channel.id}/{message.id}"

        account_age = (datetime.now(timezone.utc) - interaction.user.created_at).days
        join_age = (datetime.now(timezone.utc) - interaction.user.joined_at).days

        years, rem_days = divmod(account_age, 365)
        months, days = divmod(rem_days, 30)

        account_age_str = f"{years}y {months}m {days}d ago"
        join_age_str = f"{join_age} days ago"

        creation_embed = discord.Embed(
            title="User Created Link",
            description=f"{interaction.user.mention} (ID: {interaction.user.id}) created a link.",
            color=discord.Color.blue()
        )
        creation_embed.set_thumbnail(url=interaction.user.avatar.url if interaction.user.avatar else interaction.user.default_avatar.url)
        creation_embed.add_field(name="Message Link", value=f"[Jump to Message]({message_link})", inline=False)
        creation_embed.add_field(name="Link", value=url, inline=False)
        creation_embed.add_field(name="Account Created", value=account_age_str, inline=True)
        creation_embed.add_field(name="Joined Server", value=join_age_str, inline=True)

        if log_channel:
            await log_channel.send(embed=creation_embed)
    except Exception as e:
        await interaction.followup.send(f"Failed to create link: {e}", ephemeral=True)
        logging.error(f"Error in /link: {e}")

bot.run(TOKEN)
