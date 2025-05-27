import json
import asyncio
import discord
from discord.ext import commands

class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__()

    @discord.ui.select(custom_id="category_select", placeholder="Kategori seçin", options=[discord.SelectOption(label=cat['name'], emoji=cat['emoji']) for cat in TICKET_CATEGORIES])
    async def category_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        await interaction.response.defer()
        category = next((cat for cat in TICKET_CATEGORIES if cat['name'] == select.values[0]), None)
        if category:
            await interaction.followup.send(f"Seçilen kategori: {category['name']}", ephemeral=True)
        else:
            await interaction.followup.send("Geçersiz kategori seçildi.", ephemeral=True)

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        await interaction.response.send_message("Bir hata oluştu, lütfen daha sonra tekrar deneyin.", ephemeral=True)

class TicketBot(commands.Bot):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.category_roles = {}
        self.original_interaction = None

    async def finish_setup(self, interaction):
        # Save the category roles to config
        config["category_roles"] = self.category_roles
        with open('config.json', 'w') as f:
            json.dump(config, f, indent=4)
        
        # Continue with the rest of the setup
        # Create ticket message with button
        embed = discord.Embed(
            title="🎫 Destek Talepleri",
            description="Yardıma mı ihtiyacınız var? Aşağıdan bir kategori seçerek talep oluşturun!",
            color=discord.Color.blue()
        )
        
        # Show available categories with emojis
        categories_text = "\n".join([f"{cat['emoji']} **{cat['name']}**" for cat in TICKET_CATEGORIES])
        embed.add_field(name="Mevcut Kategoriler", value=categories_text, inline=False)
        
        # Add credit line in footer
        embed.set_footer(text="gg/discosoft")
        
        # Create and send the view with the category dropdown
        view = TicketView()
        
        await interaction.response.edit_message(content="Kurulum tamamlanıyor...", embed=None, view=None)
        message = await self.original_interaction.channel.send(embed=embed, view=view)
        
        # Save the ticket channel ID
        config["ticket_channel_id"] = self.original_interaction.channel.id
        with open('config.json', 'w') as f:
            json.dump(config, f, indent=4)
        
        # Build the completion message
        setup_msg = f"Talep sistemi kuruldu! Kapatılan talepler {self.archive_category.mention} kategorisine taşınacak.\n\n"
        setup_msg += "**Destek Ekipleri:**\n"
        for cat in TICKET_CATEGORIES:
            cat_name = cat["name"]
            if cat_name in self.category_roles:
                role = self.original_interaction.guild.get_role(int(self.category_roles[cat_name]))
                if role:
                    setup_msg += f"{cat['emoji']} {cat_name}: {role.mention}\n"
                else:
                    setup_msg += f"{cat['emoji']} {cat_name}: Rol bulunamadı\n"
            else:
                setup_msg += f"{cat['emoji']} {cat_name}: Atanmamış\n"
        
        # Send the setup message privately to the user who did the setup - try multiple methods
        try:
            # First try sending directly to the user who started the setup
            await self.original_interaction.user.send(setup_msg)
        except Exception as e:
            print(f"DM sending error: {e}")
            # If DM fails, try using followup with ephemeral=True
            try:
                await interaction.followup.send(setup_msg, ephemeral=True)
            except Exception as e:
                print(f"Followup sending error: {e}")
                # If that fails too, try using the original interaction
                try:
                    await self.original_interaction.followup.send(setup_msg, ephemeral=True)
                except Exception as e:
                    print(f"Original interaction followup error: {e}")
                    # Last resort - send in channel but delete after 10 seconds
                    temp_msg = await self.original_interaction.channel.send(f"{self.original_interaction.user.mention} Kurulum bilgileri (10 saniye sonra silinecek):\n\n{setup_msg}")
                    await asyncio.sleep(10)
                    try:
                        await temp_msg.delete()
                    except:
                        pass
        
        # Mark view as complete so it stops listening
        self.stop()
        
        # Clean up setup state
        if self.original_interaction.user.id in setup_states:
            del setup_states[self.original_interaction.user.id]
            
        # Wait 3 seconds, then ask for log channel setup
        await asyncio.sleep(3)
        await self.original_interaction.channel.send(
            f"{self.original_interaction.user.mention}, şimdi logların gönderileceği kanalı ayarlamak için lütfen `/logkanal #kanal-adı` komutunu kullanın.",
            delete_after=30
        )
        
        # Continue with the rest of the setup
        # Create ticket message with button
        embed = discord.Embed(
            title="🎫 Destek Talepleri",
            description="Yardıma mı ihtiyacınız var? Aşağıdan bir kategori seçerek talep oluşturun!",
            color=discord.Color.blue()
        )
        
        # Show available categories with emojis
        categories_text = "\n".join([f"{cat['emoji']} **{cat['name']}**" for cat in TICKET_CATEGORIES])
        embed.add_field(name="Mevcut Kategoriler", value=categories_text, inline=False)
        
        # Add credit line in footer
        embed.set_footer(text="gg/discosoft")
        
        # Create and send the view with the category dropdown
        view = TicketView()
        
        await interaction.response.edit_message(content="Kurulum tamamlanıyor...", embed=None, view=None)
        message = await self.original_interaction.channel.send(embed=embed, view=view)
        
        # Save the ticket channel ID
        config["ticket_channel_id"] = self.original_interaction.channel.id
        with open('config.json', 'w') as f:
            json.dump(config, f, indent=4)
        
        # Build the completion message
        setup_msg = f"Talep sistemi kuruldu! Kapatılan talepler {self.archive_category.mention} kategorisine taşınacak.\n\n"
        setup_msg += "**Destek Ekipleri:**\n"
        for cat in TICKET_CATEGORIES:
            cat_name = cat["name"]
            if cat_name in self.category_roles:
                role = self.original_interaction.guild.get_role(int(self.category_roles[cat_name]))
                if role:
                    setup_msg += f"{cat['emoji']} {cat_name}: {role.mention}\n"
                else:
                    setup_msg += f"{cat['emoji']} {cat_name}: Rol bulunamadı\n"
            else:
                setup_msg += f"{cat['emoji']} {cat_name}: Atanmamış\n"
        
        # Send the setup message privately to the user who did the setup - try multiple methods
        try:
            # First try sending directly to the user who started the setup
            await self.original_interaction.user.send(setup_msg)
        except Exception as e:
            print(f"DM sending error: {e}")
            # If DM fails, try using followup with ephemeral=True
            try:
                await interaction.followup.send(setup_msg, ephemeral=True)
            except Exception as e:
                print(f"Followup sending error: {e}")
                # If that fails too, try using the original interaction
                try:
                    await self.original_interaction.followup.send(setup_msg, ephemeral=True)
                except Exception as e:
                    print(f"Original interaction followup error: {e}")
                    # Last resort - send in channel but delete after 10 seconds
                    temp_msg = await self.original_interaction.channel.send(f"{self.original_interaction.user.mention} Kurulum bilgileri (10 saniye sonra silinecek):\n\n{setup_msg}")
                    await asyncio.sleep(10)
                    try:
                        await temp_msg.delete()
                    except:
                        pass
        
        # Mark view as complete so it stops listening
        self.stop()
        
        # Clean up setup state
        if self.original_interaction.user.id in setup_states:
            del setup_states[self.original_interaction.user.id] 