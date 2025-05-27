import discord
from discord.ext import commands
from discord import app_commands
import os
import json
import asyncio
from datetime import datetime

# Helper function to add the standard footer to all embeds
def add_default_footer(embed):
    embed.set_footer(text="gg/discosoft")
    return embed

# Bot configuration with emojis
TICKET_CATEGORIES = [
    {"name": "Genel Destek", "emoji": "❓"},
    {"name": "Teknik Sorun", "emoji": "🔧"},
    {"name": "Ödeme", "emoji": "💰"},
    {"name": "Diğer", "emoji": "📝"}
]

# Check if config file exists, create one if it doesn't
def load_config():
    if not os.path.exists('config.json'):
        default_config = {
            "token": "YOUR_BOT_TOKEN_HERE",
            "ticket_channel_id": None,
            "ticket_counter": 0,
            "staff_role_id": None,
            "ticket_log_channel_id": None,
            "guild_id": None,
            "archive_category_id": None,
            "category_roles": {},  # Map categories to support team role IDs
            "frozen_tickets": [],   # List of frozen ticket channel IDs
            "ticket_owners": {}     # Map ticket channel IDs to user IDs
        }
        with open('config.json', 'w') as f:
            json.dump(default_config, f, indent=4)
        return default_config
    
    with open('config.json', 'r') as f:
        config = json.load(f)
        
    # Rename closed_category_id to archive_category_id if needed
    if "closed_category_id" in config and "archive_category_id" not in config:
        config["archive_category_id"] = config["closed_category_id"]
        del config["closed_category_id"]
        
    # Add category_roles if it doesn't exist in older configs
    if "category_roles" not in config:
        config["category_roles"] = {}
        
    # Add frozen_tickets if it doesn't exist in older configs
    if "frozen_tickets" not in config:
        config["frozen_tickets"] = []
        
    # Add ticket_owners if it doesn't exist in older configs
    if "ticket_owners" not in config:
        config["ticket_owners"] = {}
        
    with open('config.json', 'w') as f:
        json.dump(config, f, indent=4)
            
    return config

config = load_config()

# Initialize bot with intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Setup process states
setup_states = {}

# Helper function to send DM to user
async def send_dm_to_user(user_id, message):
    try:
        # Get the user
        user = await bot.fetch_user(user_id)
        if user:
            # Send DM
            await user.send(message)
            return True
    except Exception as e:
        print(f"DM gönderme hatası: {e}")
        return False

# Ticket Information Modal
class TicketInfoModal(discord.ui.Modal):
    def __init__(self, category, category_emoji):
        super().__init__(title=f"{category_emoji} {category} Talep Formu")
        self.category = category
        self.category_emoji = category_emoji
        
        # Add form inputs
        self.add_item(discord.ui.TextInput(
            label="Adınız",
            placeholder="Adınızı giriniz",
            custom_id="first_name",
            required=True,
            max_length=50
        ))
        
        self.add_item(discord.ui.TextInput(
            label="Soyadınız",
            placeholder="Soyadınızı giriniz",
            custom_id="last_name",
            required=True,
            max_length=50
        ))
        
        self.add_item(discord.ui.TextInput(
            label="E-posta Adresiniz",
            placeholder="E-posta adresinizi giriniz",
            custom_id="email",
            required=True,
            max_length=100
        ))
        
        self.add_item(discord.ui.TextInput(
            label="Talep Sebebiniz",
            placeholder="Talebi açma sebebinizi detaylı bir şekilde açıklayınız",
            custom_id="reason",
            required=True,
            style=discord.TextStyle.paragraph,
            max_length=1000
        ))
    
    async def on_submit(self, interaction: discord.Interaction):
        # Get form data
        first_name = self.children[0].value
        last_name = self.children[1].value
        email = self.children[2].value
        reason = self.children[3].value
        
        # Create the ticket
        await ticket_manager.create_ticket(
            interaction, 
            self.category, 
            self.category_emoji,
            {
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "reason": reason
            }
        )

# Ticket Control Buttons for close/freeze
class TicketControlButtons(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        
        # Add close button
        close_button = discord.ui.Button(
            label="Talebi Kapat", 
            style=discord.ButtonStyle.danger, 
            custom_id="close_ticket"
        )
        self.add_item(close_button)
        
        # Add freeze button
        freeze_button = discord.ui.Button(
            label="Talebi Dondur", 
            style=discord.ButtonStyle.primary, 
            custom_id="freeze_ticket"
        )
        self.add_item(freeze_button)

# Ticket manager class
class TicketManager:
    def __init__(self, bot):
        self.bot = bot
        self.ticket_counter = config["ticket_counter"]
    
    def save_ticket_counter(self):
        config["ticket_counter"] = self.ticket_counter
        with open('config.json', 'w') as f:
            json.dump(config, f, indent=4)
    
    async def create_ticket(self, interaction, category, emoji, user_info=None):
        self.ticket_counter += 1
        self.save_ticket_counter()
        
        guild = interaction.guild
        user = interaction.user
        
        # Get general staff role
        staff_role = None
        if config["staff_role_id"]:
            staff_role = guild.get_role(config["staff_role_id"])
        
        # Get category-specific support team role
        support_team_role = None
        support_team_mention = ""
        if config["category_roles"] and category in config["category_roles"]:
            role_id = config["category_roles"][category]
            support_team_role = guild.get_role(int(role_id))
            if support_team_role:
                support_team_mention = f"\n\n{support_team_role.mention}, yeni bir destek talebi oluşturuldu!"
        
        # Set up permissions
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True,
                                                 manage_channels=True, manage_messages=True)
        }
        
        # Add general staff role permissions if it exists
        if staff_role:
            overwrites[staff_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
        
        # Add category-specific support team permissions if it exists
        if support_team_role and support_team_role != staff_role:
            overwrites[support_team_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
        
        # Create ticket channel
        channel_name = f"talep-{self.ticket_counter}-{user.name}"
        ticket_channel = await guild.create_text_channel(
            name=channel_name,
            overwrites=overwrites,
            reason=f"Talep {user.name} tarafından oluşturuldu"
        )
        
        # Store ticket owner in config
        config["ticket_owners"][str(ticket_channel.id)] = user.id
        with open('config.json', 'w') as f:
            json.dump(config, f, indent=4)
        
        # Create initial embed
        embed = discord.Embed(
            title=f"{emoji} Talep #{self.ticket_counter} - {category}",
            description=f"Talep oluşturduğunuz için teşekkürler, {user.mention}!\nDestek ekibimiz en kısa sürede sizinle ilgilenecektir.{support_team_mention}",
            color=discord.Color.blue()
        )
        # Add the default footer
        add_default_footer(embed)
        
        # Add user info to embed if provided
        if user_info:
            embed.add_field(name="Adı", value=user_info["first_name"], inline=True)
            embed.add_field(name="Soyadı", value=user_info["last_name"], inline=True)
            embed.add_field(name="E-posta", value=user_info["email"], inline=False)
            embed.add_field(name="Talep Sebebi", value=user_info["reason"], inline=False)
        
        # Create view with ticket control buttons
        view = TicketControlButtons()
        
        await ticket_channel.send(embed=embed, view=view)
        
        # Notify user
        await interaction.response.send_message(f"Talep oluşturuldu! {ticket_channel.mention} kanalını kontrol edin", ephemeral=True)
        
        # Send DM to user
        await send_dm_to_user(user.id, f"Merhaba {user.name}, talebiniz şu anda açıktır. Destek ekibimiz en kısa sürede size yardımcı olacaktır.")
        
        # Log ticket creation if log channel is set
        if config["ticket_log_channel_id"]:
            log_channel = guild.get_channel(config["ticket_log_channel_id"])
            if log_channel:
                log_embed = discord.Embed(
                    title=f"{emoji} Talep Oluşturuldu",
                    description=f"Talep #{self.ticket_counter} {user.mention} tarafından oluşturuldu\nKategori: {category}",
                    color=discord.Color.green()
                )
                add_default_footer(log_embed)
                if user_info:
                    log_embed.add_field(name="İletişim", value=f"{user_info['first_name']} {user_info['last_name']} ({user_info['email']})", inline=False)
                
                # Add support team information
                if support_team_role:
                    log_embed.add_field(name="Destek Ekibi", value=support_team_role.mention, inline=False)
                
                await log_channel.send(embed=log_embed)

# Ticket View with category selection dropdown
class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        
        # Add the dropdown to select ticket category
        self.add_item(CategorySelect())

# Category dropdown for ticket creation
class CategorySelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label=category["name"], 
                description=f"{category['name']} talebi oluştur",
                emoji=category["emoji"]
            )
            for category in TICKET_CATEGORIES
        ]
        super().__init__(placeholder="Talep kategorisini seçin...", min_values=1, max_values=1, options=options, custom_id="category_select")
    
    async def callback(self, interaction: discord.Interaction):
        selected_category = self.values[0]
        
        # Find selected category and emoji
        category_info = next((c for c in TICKET_CATEGORIES if c["name"] == selected_category), None)
        
        if category_info:
            # Show modal form for user info
            await interaction.response.send_modal(TicketInfoModal(category_info["name"], category_info["emoji"]))

# Event listeners
@bot.event
async def on_ready():
    print(f"{bot.user.name} hazır!")
    try:
        await bot.tree.sync()
        print("Slash komutları senkronize edildi!")
    except Exception as e:
        print(f"Komutları senkronize ederken hata oluştu: {e}")
    
    # Initialize the ticket manager
    global ticket_manager
    ticket_manager = TicketManager(bot)

# Message handler for setup process
@bot.event
async def on_message(message):
    # Don't respond to bot messages
    if message.author.bot:
        return
    
    # Check if this user is in setup process
    if message.author.id in setup_states and setup_states[message.author.id]["waiting_for_archive_id"]:
        try:
            # Try to parse the category ID
            archive_id = int(message.content.strip())
            
            # Save the archive category ID
            config["archive_category_id"] = archive_id
            with open('config.json', 'w') as f:
                json.dump(config, f, indent=4)
            
            # Get the category and check if it's valid
            archive_category = message.guild.get_channel(archive_id)
            if archive_category and isinstance(archive_category, discord.CategoryChannel):
                # Continue with support team selection process
                setup_data = setup_states[message.author.id]
                setup_data["waiting_for_archive_id"] = False
                
                # Start the support team selection process
                view = SupportTeamSelectionView(bot, setup_data["original_interaction"], archive_category)
                
                # First category to select a role for
                first_category = TICKET_CATEGORIES[0]
                
                embed = discord.Embed(
                    title="Destek Ekibi Seçimi",
                    description=f"{first_category['emoji']} **{first_category['name']}** kategorisi için destek ekibi rolünü seçin veya atlamak için butona tıklayın.",
                    color=discord.Color.blue()
                )
                add_default_footer(embed)
                
                await message.channel.send(embed=embed, view=view)
            else:
                # Invalid category
                await message.channel.send("Geçersiz kategori ID'si! Lütfen geçerli bir Arşiv Kategorisi ID'si girin.")
                return
                
        except ValueError:
            # Not a valid number
            await message.channel.send("Lütfen geçerli bir kategori ID'si girin (sadece sayı).")
            return
    
    # Process commands as usual
    await bot.process_commands(message)

# Button interaction handler
@bot.event
async def on_interaction(interaction):
    if interaction.type == discord.InteractionType.component:
        custom_id = interaction.data.get("custom_id")
        
        if custom_id == "close_ticket":
            # Handle ticket closing
            await handle_close_ticket(interaction)
            
        elif custom_id == "freeze_ticket":
            # Handle ticket freezing/unfreezing
            await handle_freeze_ticket(interaction)

async def handle_close_ticket(interaction):
    channel = interaction.channel
    
    # Check if this is a ticket channel
    if channel.name.startswith("talep-"):
        # Check if archive category is set
        if not config["archive_category_id"]:
            await interaction.response.send_message(
                "Arşiv kategorisi ayarlanmamış! Lütfen bir yöneticiden `/arşivkategorisi` komutunu kullanmasını isteyin.",
                ephemeral=True
            )
            return
        
        embed = discord.Embed(
            title="Talep Kapatılıyor",
            description="Bu talep 5 saniye içinde kapatılacak ve arşive taşınacak...",
            color=discord.Color.red()
        )
        add_default_footer(embed)
        await interaction.response.send_message(embed=embed)
        
        # Wait 5 seconds then move the channel to archive category
        await asyncio.sleep(5)
        
        try:
            # Get ticket owner ID
            owner_id = None
            if str(channel.id) in config["ticket_owners"]:
                owner_id = config["ticket_owners"][str(channel.id)]
            
            # Get archive category from config
            archive_category = interaction.guild.get_channel(config["archive_category_id"])
            
            if archive_category and isinstance(archive_category, discord.CategoryChannel):
                # Move channel to archive category
                await channel.edit(category=archive_category, reason=f"Talep {interaction.user.name} tarafından kapatıldı")
                
                # Disable sending messages for everyone except staff
                for target, overwrite in channel.overwrites.items():
                    if isinstance(target, discord.Member) and target.id != bot.user.id:
                        overwrite.send_messages = False
                        await channel.set_permissions(target, overwrite=overwrite)
                
                # Add kapali prefix to channel name
                await channel.edit(name=f"kapali-{channel.name[6:]}")
                
                # Send closed message
                closed_embed = discord.Embed(
                    title="Talep Kapatıldı",
                    description=f"Bu talep {interaction.user.mention} tarafından kapatıldı.",
                    color=discord.Color.red()
                )
                add_default_footer(closed_embed)
                await channel.send(embed=closed_embed)
                
                # Send DM to user if we have their ID
                if owner_id:
                    # Get username if possible
                    try:
                        owner = await bot.fetch_user(owner_id)
                        owner_name = owner.name
                    except:
                        owner_name = "Kullanıcı"
                        
                    await send_dm_to_user(owner_id, f"Merhaba {owner_name}, talebiniz kapatılmıştır. Teşekkür ederiz.")
                
                # If ticket was frozen, remove it from frozen tickets list
                if channel.id in config["frozen_tickets"]:
                    config["frozen_tickets"].remove(channel.id)
                    with open('config.json', 'w') as f:
                        json.dump(config, f, indent=4)
            else:
                # If category isn't found, notify and delete the channel
                error_embed = discord.Embed(
                    title="Hata",
                    description="Arşiv kategorisi bulunamadı! Talep kanalı siliniyor...",
                    color=discord.Color.red()
                )
                add_default_footer(error_embed)
                await channel.send(embed=error_embed)
                await asyncio.sleep(3)
                await channel.delete(reason=f"Talep {interaction.user.name} tarafından kapatıldı (Arşiv kategorisi bulunamadı)")
        except Exception as e:
            # Log the error and delete the channel
            print(f"Talep kapatma hatası: {e}")
            await channel.delete(reason=f"Talep {interaction.user.name} tarafından kapatıldı (Hata: {e})")
        
        # Log ticket closing if log channel is set
        if config["ticket_log_channel_id"]:
            log_channel = interaction.guild.get_channel(config["ticket_log_channel_id"])
            if log_channel:
                log_embed = discord.Embed(
                    title="Talep Kapatıldı",
                    description=f"Talep {channel.name} {interaction.user.mention} tarafından kapatıldı",
                    color=discord.Color.red()
                )
                add_default_footer(log_embed)
                await log_channel.send(embed=log_embed)

async def handle_freeze_ticket(interaction):
    channel = interaction.channel
    
    # Check if this is a ticket channel
    if channel.name.startswith("talep-"):
        # Check if user has permission (staff or support team)
        has_permission = False
        
        # Check if user is admin
        if interaction.user.guild_permissions.administrator:
            has_permission = True
            
        # Check if user has staff role
        if not has_permission and config["staff_role_id"]:
            staff_role = interaction.guild.get_role(config["staff_role_id"])
            if staff_role and staff_role in interaction.user.roles:
                has_permission = True
                
        # Check if user has any of the support team roles
        if not has_permission:
            for category, role_id in config["category_roles"].items():
                role = interaction.guild.get_role(int(role_id))
                if role and role in interaction.user.roles:
                    has_permission = True
                    break
        
        if not has_permission:
            await interaction.response.send_message("Bu işlemi yapmak için yetkiniz yok!", ephemeral=True)
            return
        
        # Check if channel is already frozen or not
        is_frozen = channel.id in config["frozen_tickets"]
        
        # Get ticket owner ID
        owner_id = None
        if str(channel.id) in config["ticket_owners"]:
            owner_id = config["ticket_owners"][str(channel.id)]
        
        # Toggle frozen state
        if is_frozen:
            # Unfreeze the ticket
            config["frozen_tickets"].remove(channel.id)
            
            # Update permissions to allow messages again
            for target, overwrite in channel.overwrites.items():
                if isinstance(target, discord.Member) and target.id != bot.user.id and target.id != interaction.guild.me.id:
                    # Restore original permissions (allow regular users to send messages)
                    if not target.guild_permissions.administrator and not any(role.id == config["staff_role_id"] for role in target.roles):
                        # Check if user is not staff/admin, enable messaging
                        overwrite.send_messages = True
                        await channel.set_permissions(target, overwrite=overwrite)
            
            # Send notification
            embed = discord.Embed(
                title="Talep Açıldı",
                description=f"Bu talep {interaction.user.mention} tarafından açıldı. Artık mesaj gönderebilirsiniz.",
                color=discord.Color.green()
            )
            add_default_footer(embed)
            await interaction.response.send_message(embed=embed)
            
            # Send DM to user if we have their ID
            if owner_id:
                # Get username if possible
                try:
                    owner = await bot.fetch_user(owner_id)
                    owner_name = owner.name
                except:
                    owner_name = "Kullanıcı"
                    
                await send_dm_to_user(owner_id, f"Merhaba {owner_name}, talebiniz şu anda açıktır. Artık mesaj gönderebilirsiniz.")
            
            # Update button to show "Talebi Dondur"
            view = TicketControlButtons()
            await interaction.message.edit(view=view)
            
        else:
            # Freeze the ticket
            config["frozen_tickets"].append(channel.id)
            
            # Update permissions to prevent regular users from sending messages
            for target, overwrite in channel.overwrites.items():
                if isinstance(target, discord.Member) and target.id != bot.user.id and target.id != interaction.guild.me.id:
                    # If member is not staff/admin, disable messaging
                    if not target.guild_permissions.administrator and not any(role.id == config["staff_role_id"] for role in target.roles):
                        overwrite.send_messages = False
                        await channel.set_permissions(target, overwrite=overwrite)
            
            # Send notification
            embed = discord.Embed(
                title="Talep Donduruldu",
                description=f"Bu talep {interaction.user.mention} tarafından donduruldu. Şu anda mesaj gönderemezsiniz.",
                color=discord.Color.yellow()
            )
            add_default_footer(embed)
            await interaction.response.send_message(embed=embed)
            
            # Send DM to user if we have their ID
            if owner_id:
                # Get username if possible
                try:
                    owner = await bot.fetch_user(owner_id)
                    owner_name = owner.name
                except:
                    owner_name = "Kullanıcı"
                    
                await send_dm_to_user(owner_id, f"Merhaba {owner_name}, talebiniz şu anda dondurulmuştur. Geçici olarak mesaj gönderemezsiniz.")
            
            # Update button to show "Talebi Aç"
            unfreeze_view = discord.ui.View(timeout=None)
            unfreeze_button = discord.ui.Button(
                label="Talebi Aç", 
                style=discord.ButtonStyle.success, 
                custom_id="freeze_ticket"
            )
            close_button = discord.ui.Button(
                label="Talebi Kapat", 
                style=discord.ButtonStyle.danger, 
                custom_id="close_ticket"
            )
            unfreeze_view.add_item(close_button)
            unfreeze_view.add_item(unfreeze_button)
            
        # Save frozen state
        with open('config.json', 'w') as f:
            json.dump(config, f, indent=4)
        
        # Log ticket freezing if log channel is set
        if config["ticket_log_channel_id"]:
            log_channel = interaction.guild.get_channel(config["ticket_log_channel_id"])
            if log_channel:
                action = "açıldı" if is_frozen else "donduruldu"
                log_embed = discord.Embed(
                    title=f"Talep {action.capitalize()}",
                    description=f"Talep {channel.name} {interaction.user.mention} tarafından {action}",
                    color=discord.Color.yellow()
                )
                add_default_footer(log_embed)
                await log_channel.send(embed=log_embed)

# Support Team Selection View for setup
class SupportTeamSelectionView(discord.ui.View):
    def __init__(self, bot, interaction, archive_category):
        super().__init__(timeout=300)  # 5 minute timeout
        self.bot = bot
        self.original_interaction = interaction
        self.archive_category = archive_category
        self.category_roles = {}
        self.current_category_index = 0
        self.setup_complete = False
        # Add the first dropdown to select support team for first category
        self.update_view()

    def update_view(self):
        # Clear existing items
        self.clear_items()
        
        # If we've gone through all categories, we're done
        if self.current_category_index >= len(TICKET_CATEGORIES):
            self.setup_complete = True
            return
        
        # Get current category
        category = TICKET_CATEGORIES[self.current_category_index]
        
        # Add role selection dropdown for the current category
        self.add_item(RoleSelect(category["name"], category["emoji"]))
        
        # Add a skip button
        skip_button = discord.ui.Button(
            label="Bu kategori için ekip atama", 
            style=discord.ButtonStyle.secondary,
            custom_id=f"skip_{category['name']}"
        )
        skip_button.callback = self.skip_category
        self.add_item(skip_button)
    
    async def skip_category(self, interaction):
        # Move to the next category
        self.current_category_index += 1
        
        if self.current_category_index >= len(TICKET_CATEGORIES):
            # All categories processed
            await self.finish_setup(interaction)
        else:
            # Update the view for the next category
            self.update_view()
            
            # Show the next category's selection
            category = TICKET_CATEGORIES[self.current_category_index]
            embed = discord.Embed(
                title="Destek Ekibi Seçimi",
                description=f"{category['emoji']} **{category['name']}** kategorisi için destek ekibi rolünü seçin veya atlamak için butona tıklayın.",
                color=discord.Color.blue()
            )
            add_default_footer(embed)
            await interaction.response.edit_message(embed=embed, view=self)
    
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
        add_default_footer(embed)
        
        # Create and send the view with the category dropdown
        view = TicketView()
        
        await interaction.response.edit_message(content="Kurulum tamamlanıyor...", embed=None, view=None)
        message = await self.original_interaction.channel.send(embed=embed, view=view)
        
        # Save the ticket channel ID
        config["ticket_channel_id"] = self.original_interaction.channel.id
        with open('config.json', 'w') as f:
            json.dump(config, f, indent=4)
        
        # Build the completion message
        setup_msg = f"Talep sistemi bu kanalda kuruldu! Kapatılan talepler {self.archive_category.mention} kategorisine taşınacak.\n\n"
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
        
        # Add log channel setup reminder
        setup_msg += "\n\n**Önemli:** Lütfen `/logkanal` komutunu kullanarak log kanalını ayarlayınız!"
        
        # Send the setup message privately to the user who did the setup - try multiple methods
        sent_successfully = False
        
        # Method 1: Try direct DM to user
        try:
            await self.original_interaction.user.send(setup_msg)
            sent_successfully = True
            print("Sent setup info via DM")
        except Exception as e:
            print(f"DM sending error: {e}")
        
        # Method 2: Try interaction followup with ephemeral=True
        if not sent_successfully:
            try:
                await interaction.followup.send(setup_msg, ephemeral=True)
                sent_successfully = True
                print("Sent setup info via interaction followup")
            except Exception as e:
                print(f"Interaction followup error: {e}")
        
        # Method 3: Try original interaction followup
        if not sent_successfully:
            try:
                await self.original_interaction.followup.send(setup_msg, ephemeral=True)
                sent_successfully = True
                print("Sent setup info via original interaction followup")
            except Exception as e:
                print(f"Original interaction followup error: {e}")
        
        # Method 4: Last resort - send in channel but delete after a few seconds
        if not sent_successfully:
            try:
                temp_msg = await self.original_interaction.channel.send(
                    f"{self.original_interaction.user.mention} Kurulum bilgileri (10 saniye sonra silinecek):\n\n{setup_msg}"
                )
                await asyncio.sleep(10)
                try:
                    await temp_msg.delete()
                except:
                    pass
                print("Sent setup info via temporary channel message")
            except Exception as e:
                print(f"Channel message error: {e}")
        
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

# Role selection dropdown for support team setup
class RoleSelect(discord.ui.RoleSelect):
    def __init__(self, category_name, category_emoji):
        super().__init__(
            placeholder=f"{category_emoji} {category_name} için destek ekibi rolünü seçin",
            min_values=1,
            max_values=1
        )
        self.category_name = category_name
        self.category_emoji = category_emoji
    
    async def callback(self, interaction: discord.Interaction):
        # Store the selected role for this category
        view = self.view
        view.category_roles[self.category_name] = str(self.values[0].id)
        
        # Move to the next category
        view.current_category_index += 1
        
        if view.current_category_index >= len(TICKET_CATEGORIES):
            # All categories processed
            await view.finish_setup(interaction)
        else:
            # Update the view for the next category
            view.update_view()
            
            # Show the next category's selection
            category = TICKET_CATEGORIES[view.current_category_index]
            embed = discord.Embed(
                title="Destek Ekibi Seçimi",
                description=f"{category['emoji']} **{category['name']}** kategorisi için destek ekibi rolünü seçin veya atlamak için butona tıklayın.",
                color=discord.Color.blue()
            )
            add_default_footer(embed)
            await interaction.response.edit_message(embed=embed, view=view)

# Commands
@bot.tree.command(name="kurulum", description="Talep sistemini kur")
@app_commands.default_permissions(administrator=True)
async def setup(interaction: discord.Interaction):
    # Save guild ID for future reference
    config["guild_id"] = interaction.guild.id
    
    # Store setup state for this user
    setup_states[interaction.user.id] = {
        "waiting_for_archive_id": True,
        "original_interaction": interaction
    }
    
    # Ask for archive category ID
    await interaction.response.send_message("Lütfen arşivlenecek kategorinin ID bilgisini yazınız.")

@bot.tree.command(name="yetkilirol", description="Taleplere erişebilecek genel yetkili rolünü ayarla")
@app_commands.describe(role="Tüm taleplere erişimi olacak rol")
@app_commands.default_permissions(administrator=True)
async def setstaffrole(interaction: discord.Interaction, role: discord.Role):
    config["staff_role_id"] = role.id
    with open('config.json', 'w') as f:
        json.dump(config, f, indent=4)
    
    embed = discord.Embed(
        title="Yetkili Rolü Ayarlandı",
        description=f"Genel yetkili rolü {role.mention} olarak ayarlandı! Bu rol tüm talep türlerine erişebilecek.",
        color=discord.Color.blue()
    )
    add_default_footer(embed)
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="logkanal", description="Talep loglarının gönderileceği kanalı ayarla")
@app_commands.describe(channel="Talep loglarının gönderileceği kanal")
@app_commands.default_permissions(administrator=True)
async def setlogchannel(interaction: discord.Interaction, channel: discord.TextChannel):
    config["ticket_log_channel_id"] = channel.id
    with open('config.json', 'w') as f:
        json.dump(config, f, indent=4)
    
    embed = discord.Embed(
        title="Log Kanalı Ayarlandı",
        description=f"Log kanalı {channel.mention} olarak ayarlandı!",
        color=discord.Color.blue()
    )
    add_default_footer(embed)
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="arşivkategorisi", description="Arşivlenecek taleplerin taşınacağı kategoriyi ayarla")
@app_commands.describe(category="Arşivlenecek taleplerin taşınacağı kategori")
@app_commands.default_permissions(administrator=True)
async def setarchivecategory(interaction: discord.Interaction, category: discord.CategoryChannel):
    config["archive_category_id"] = category.id
    with open('config.json', 'w') as f:
        json.dump(config, f, indent=4)
    
    embed = discord.Embed(
        title="Arşiv Kategorisi Ayarlandı",
        description=f"Arşiv kategorisi {category.mention} olarak ayarlandı!",
        color=discord.Color.green()
    )
    add_default_footer(embed)
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="destekekibi", description="Belirli bir talep kategorisi için destek ekibi rolünü ayarla")
@app_commands.choices(category=[
    app_commands.Choice(name=cat["name"], value=cat["name"]) 
    for cat in TICKET_CATEGORIES
])
@app_commands.describe(
    category="Destek ekibi atanacak talep kategorisi",
    role="Bu kategori için atanacak destek ekibi rolü"
)
@app_commands.default_permissions(administrator=True)
async def setsupportteam(
    interaction: discord.Interaction, 
    category: str,
    role: discord.Role
):
    # Save the support team role for this category
    if "category_roles" not in config:
        config["category_roles"] = {}
    
    config["category_roles"][category] = str(role.id)
    with open('config.json', 'w') as f:
        json.dump(config, f, indent=4)
    
    # Find the category emoji
    category_info = next((c for c in TICKET_CATEGORIES if c["name"] == category), None)
    emoji = category_info["emoji"] if category_info else "🎫"
    
    embed = discord.Embed(
        title="Destek Ekibi Ayarlandı",
        description=f"{emoji} **{category}** kategorisi için destek ekibi rolü {role.mention} olarak ayarlandı!",
        color=discord.Color.blue()
    )
    add_default_footer(embed)
    await interaction.response.send_message(embed=embed, ephemeral=True)

# Yönetim Kategorileri
YONETIM_CATEGORIES = [
    {"name": "Destek Sistemi", "emoji": "🎫", "description": "Talep/destek sistemi yönetimi"},
    {"name": "Moderasyon Komutları", "emoji": "🔨", "description": "Sunucu moderasyon komutları"}
]

# Yönetim Kategori Seçimi Dropdown
class YonetimCategorySelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label=category["name"],
                description=category["description"],
                emoji=category["emoji"]
            )
            for category in YONETIM_CATEGORIES
        ]
        super().__init__(placeholder="Yönetim kategorisini seçin...", min_values=1, max_values=1, options=options)
    
    async def callback(self, interaction: discord.Interaction):
        selected_category = self.values[0]
        
        if selected_category == "Destek Sistemi":
            await handle_destek_sistemi(interaction)
        elif selected_category == "Moderasyon Komutları":
            await handle_moderasyon_komutlari(interaction)
        else:
            await interaction.response.send_message("Geçersiz kategori seçildi.", ephemeral=True)

# Yönetim View
class YonetimView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=180)  # 3 dakika timeout
        self.add_item(YonetimCategorySelect())

# Destek Sistemi Handler
async def handle_destek_sistemi(interaction: discord.Interaction):
    # Destek sistemi yönetim seçenekleri
    embed = discord.Embed(
        title="🎫 Destek Sistemi Yönetimi",
        description="Destek sistemi ile ilgili komutlar:",
        color=discord.Color.blue()
    )
    
    commands = [
        {"name": "/kurulum", "description": "Talep sistemini kurma"},
        {"name": "/yetkilirol", "description": "Yetkili rolünü ayarlama"},
        {"name": "/logkanal", "description": "Log kanalını ayarlama"},
        {"name": "/arşivkategorisi", "description": "Arşiv kategorisini ayarlama"},
        {"name": "/destekekibi", "description": "Kategori bazlı destek ekibi atama"}
    ]
    
    for cmd in commands:
        embed.add_field(name=cmd["name"], value=cmd["description"], inline=False)
    
    add_default_footer(embed)
    await interaction.response.send_message(embed=embed, ephemeral=True)

# Moderasyon Komutları Handler
async def handle_moderasyon_komutlari(interaction: discord.Interaction):
    # Moderasyon komutları seçenekleri
    embed = discord.Embed(
        title="🔨 Moderasyon Komutları",
        description="Aşağıdaki moderasyon komutlarını kullanabilirsiniz:",
        color=discord.Color.red()
    )
    
    commands = [
        {"name": "/at", "description": "Kullanıcıyı sunucudan at (kick)"},
        {"name": "/yasakla", "description": "Kullanıcıyı sunucudan yasakla (ban)"},
        {"name": "/sustur", "description": "Kullanıcıyı belirli bir süre sustur"},
        {"name": "/temizle", "description": "Belirli sayıda mesajı sil"},
        {"name": "/uyarı", "description": "Kullanıcıya uyarı ver"}
    ]
    
    for cmd in commands:
        embed.add_field(name=cmd["name"], value=cmd["description"], inline=False)
    
    add_default_footer(embed)
    await interaction.response.send_message(embed=embed, ephemeral=True)

# Yönetim Komutu
@bot.tree.command(name="yonetim", description="Sunucu yönetim paneline erişin")
@app_commands.default_permissions(administrator=True)
async def yonetim(interaction: discord.Interaction):
    view = YonetimView()
    
    embed = discord.Embed(
        title="⚙️ Sunucu Yönetim Paneli",
        description="Aşağıdaki kategorilerden birini seçerek ilgili yönetim komutlarına erişebilirsiniz.",
        color=discord.Color.gold()
    )
    
    # Kategorileri listele
    categories_text = "\n".join([f"{cat['emoji']} **{cat['name']}**: {cat['description']}" for cat in YONETIM_CATEGORIES])
    embed.add_field(name="Mevcut Kategoriler", value=categories_text, inline=False)
    
    add_default_footer(embed)
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

# Kullanıcı at (kick) komutu
@bot.tree.command(name="at", description="Bir kullanıcıyı sunucudan at")
@app_commands.describe(
    kullanici="Atılacak kullanıcı",
    sebep="Atılma sebebi (isteğe bağlı)"
)
@app_commands.default_permissions(kick_members=True)
async def kick(interaction: discord.Interaction, kullanici: discord.Member, sebep: str = None):
    # Kendini veya botları atamaz
    if kullanici == interaction.user:
        await interaction.response.send_message("Kendinizi atamazsınız!", ephemeral=True)
        return
    
    if kullanici.bot:
        await interaction.response.send_message("Botları atamazsınız!", ephemeral=True)
        return
    
    # Yetkili kontrolü
    if kullanici.top_role >= interaction.user.top_role and interaction.user.id != interaction.guild.owner_id:
        await interaction.response.send_message("Bu kullanıcıyı atmak için yetkiniz yok! Sizden daha yüksek ya da aynı yetkide.", ephemeral=True)
        return
    
    # Kullanıcıyı at
    reason = f"{interaction.user} tarafından atıldı: {sebep}" if sebep else f"{interaction.user} tarafından atıldı"
    
    try:
        await kullanici.kick(reason=reason)
        
        # Başarılı kick mesajı
        embed = discord.Embed(
            title="👢 Kullanıcı Atıldı",
            description=f"{kullanici.mention} sunucudan atıldı.",
            color=discord.Color.orange()
        )
        embed.add_field(name="Sebep", value=sebep or "Sebep belirtilmedi", inline=False)
        embed.set_footer(text=f"{interaction.user} tarafından atıldı")
        add_default_footer(embed)
        
        await interaction.response.send_message(embed=embed, ephemeral=False)
        
        # DM olarak bildirim göndermeye çalış
        try:
            dm_embed = discord.Embed(
                title=f"👢 {interaction.guild.name} sunucusundan atıldınız",
                description=f"Yetkili: {interaction.user.mention}",
                color=discord.Color.red()
            )
            dm_embed.add_field(name="Sebep", value=sebep or "Sebep belirtilmedi", inline=False)
            add_default_footer(dm_embed)
            
            await kullanici.send(embed=dm_embed)
        except:
            pass
        
    except discord.Forbidden:
        await interaction.response.send_message("Bu kullanıcıyı atmak için yeterli yetkiye sahip değilim!", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"Bir hata oluştu: {e}", ephemeral=True)

# Kullanıcı yasakla (ban) komutu
@bot.tree.command(name="yasakla", description="Bir kullanıcıyı sunucudan yasakla")
@app_commands.describe(
    kullanici="Yasaklanacak kullanıcı",
    sebep="Yasaklanma sebebi (isteğe bağlı)",
    mesaj_sil="Son X gün içindeki mesajları sil (0-7 gün)"
)
@app_commands.choices(mesaj_sil=[
    app_commands.Choice(name="Silme", value=0),
    app_commands.Choice(name="Son 1 gün", value=1),
    app_commands.Choice(name="Son 3 gün", value=3),
    app_commands.Choice(name="Son 7 gün", value=7)
])
@app_commands.default_permissions(ban_members=True)
async def ban(interaction: discord.Interaction, kullanici: discord.Member, sebep: str = None, mesaj_sil: int = 0):
    # Kendini veya botları yasaklayamaz
    if kullanici == interaction.user:
        await interaction.response.send_message("Kendinizi yasaklayamazsınız!", ephemeral=True)
        return
    
    if kullanici.bot:
        await interaction.response.send_message("Botları yasaklayamazsınız!", ephemeral=True)
        return
    
    # Yetkili kontrolü
    if kullanici.top_role >= interaction.user.top_role and interaction.user.id != interaction.guild.owner_id:
        await interaction.response.send_message("Bu kullanıcıyı yasaklamak için yetkiniz yok! Sizden daha yüksek ya da aynı yetkide.", ephemeral=True)
        return
    
    # Kullanıcıyı yasakla
    reason = f"{interaction.user} tarafından yasaklandı: {sebep}" if sebep else f"{interaction.user} tarafından yasaklandı"
    
    try:
        # DM olarak bildirim göndermeye çalış
        try:
            dm_embed = discord.Embed(
                title=f"🚫 {interaction.guild.name} sunucusundan yasaklandınız",
                description=f"Yetkili: {interaction.user.mention}",
                color=discord.Color.red()
            )
            dm_embed.add_field(name="Sebep", value=sebep or "Sebep belirtilmedi", inline=False)
            add_default_footer(dm_embed)
            
            await kullanici.send(embed=dm_embed)
        except:
            pass
        
        # Kullanıcıyı yasakla
        await kullanici.ban(reason=reason, delete_message_days=mesaj_sil)
        
        # Başarılı ban mesajı
        embed = discord.Embed(
            title="🚫 Kullanıcı Yasaklandı",
            description=f"{kullanici.mention} sunucudan yasaklandı.",
            color=discord.Color.red()
        )
        embed.add_field(name="Sebep", value=sebep or "Sebep belirtilmedi", inline=False)
        embed.add_field(name="Silinen Mesajlar", value=f"Son {mesaj_sil} gün" if mesaj_sil > 0 else "Mesaj silinmedi", inline=False)
        embed.set_footer(text=f"{interaction.user} tarafından yasaklandı")
        add_default_footer(embed)
        
        await interaction.response.send_message(embed=embed, ephemeral=False)
        
    except discord.Forbidden:
        await interaction.response.send_message("Bu kullanıcıyı yasaklamak için yeterli yetkiye sahip değilim!", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"Bir hata oluştu: {e}", ephemeral=True)

# Susturma (timeout) komutu
@bot.tree.command(name="sustur", description="Bir kullanıcıyı belirli bir süre için sustur")
@app_commands.describe(
    kullanici="Susturulacak kullanıcı",
    sure="Susturma süresi (dakika)",
    sebep="Susturulma sebebi (isteğe bağlı)"
)
@app_commands.default_permissions(moderate_members=True)
async def timeout(interaction: discord.Interaction, kullanici: discord.Member, sure: int, sebep: str = None):
    # Kendini veya botları susturamaz
    if kullanici == interaction.user:
        await interaction.response.send_message("Kendinizi susturamazsınız!", ephemeral=True)
        return
    
    if kullanici.bot:
        await interaction.response.send_message("Botları susturamazsınız!", ephemeral=True)
        return
    
    # Yetkili kontrolü
    if kullanici.top_role >= interaction.user.top_role and interaction.user.id != interaction.guild.owner_id:
        await interaction.response.send_message("Bu kullanıcıyı susturmak için yetkiniz yok! Sizden daha yüksek ya da aynı yetkide.", ephemeral=True)
        return
    
    # Süre kontrolü (maksimum 28 gün)
    if sure <= 0:
        await interaction.response.send_message("Geçerli bir süre girmelisiniz!", ephemeral=True)
        return
    
    if sure > 40320:  # 28 gün (dakika olarak)
        await interaction.response.send_message("Maksimum susturma süresi 28 gündür!", ephemeral=True)
        return
    
    # Kullanıcıyı sustur
    reason = f"{interaction.user} tarafından susturuldu: {sebep}" if sebep else f"{interaction.user} tarafından susturuldu"
    
    try:
        # Timeout süresi hesapla
        timeout_duration = datetime.timedelta(minutes=sure)
        await kullanici.timeout_for(timeout_duration, reason=reason)
        
        # Bitiş zamanını hesapla
        end_time = discord.utils.utcnow() + timeout_duration
        
        # Başarılı timeout mesajı
        embed = discord.Embed(
            title="🔇 Kullanıcı Susturuldu",
            description=f"{kullanici.mention} {sure} dakika boyunca susturuldu.",
            color=discord.Color.orange()
        )
        embed.add_field(name="Sebep", value=sebep or "Sebep belirtilmedi", inline=False)
        embed.add_field(name="Bitiş Zamanı", value=f"<t:{int(end_time.timestamp())}:R>", inline=False)
        embed.set_footer(text=f"{interaction.user} tarafından susturuldu")
        add_default_footer(embed)
        
        await interaction.response.send_message(embed=embed, ephemeral=False)
        
        # DM olarak bildirim göndermeye çalış
        try:
            dm_embed = discord.Embed(
                title=f"🔇 {interaction.guild.name} sunucusunda susturuldunuz",
                description=f"Yetkili: {interaction.user.mention}",
                color=discord.Color.orange()
            )
            dm_embed.add_field(name="Sebep", value=sebep or "Sebep belirtilmedi", inline=False)
            dm_embed.add_field(name="Süre", value=f"{sure} dakika", inline=False)
            dm_embed.add_field(name="Bitiş Zamanı", value=f"<t:{int(end_time.timestamp())}:R>", inline=False)
            add_default_footer(dm_embed)
            
            await kullanici.send(embed=dm_embed)
        except:
            pass
        
    except discord.Forbidden:
        await interaction.response.send_message("Bu kullanıcıyı susturmak için yeterli yetkiye sahip değilim!", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"Bir hata oluştu: {e}", ephemeral=True)

# Susturmayı kaldırma komutu
@bot.tree.command(name="susturma_kaldir", description="Bir kullanıcının susturmasını kaldır")
@app_commands.describe(
    kullanici="Susturması kaldırılacak kullanıcı",
    sebep="Susturma kaldırma sebebi (isteğe bağlı)"
)
@app_commands.default_permissions(moderate_members=True)
async def remove_timeout(interaction: discord.Interaction, kullanici: discord.Member, sebep: str = None):
    # Yetkili kontrolü
    if kullanici.top_role >= interaction.user.top_role and interaction.user.id != interaction.guild.owner_id:
        await interaction.response.send_message("Bu kullanıcının susturmasını kaldırmak için yetkiniz yok! Sizden daha yüksek ya da aynı yetkide.", ephemeral=True)
        return
    
    # Susturmayı kaldır
    reason = f"{interaction.user} tarafından susturma kaldırıldı: {sebep}" if sebep else f"{interaction.user} tarafından susturma kaldırıldı"
    
    try:
        # Şu anki susturması var mı kontrol et
        if kullanici.is_timed_out():
            await kullanici.timeout(None, reason=reason)
            
            # Başarılı mesajı
            embed = discord.Embed(
                title="🔊 Susturma Kaldırıldı",
                description=f"{kullanici.mention} kullanıcısının susturması kaldırıldı.",
                color=discord.Color.green()
            )
            embed.add_field(name="Sebep", value=sebep or "Sebep belirtilmedi", inline=False)
            embed.set_footer(text=f"{interaction.user} tarafından kaldırıldı")
            add_default_footer(embed)
            
            await interaction.response.send_message(embed=embed, ephemeral=False)
            
            # DM olarak bildirim göndermeye çalış
            try:
                dm_embed = discord.Embed(
                    title=f"🔊 {interaction.guild.name} sunucusundaki susturmanız kaldırıldı",
                    description=f"Yetkili: {interaction.user.mention}",
                    color=discord.Color.green()
                )
                dm_embed.add_field(name="Sebep", value=sebep or "Sebep belirtilmedi", inline=False)
                add_default_footer(dm_embed)
                
                await kullanici.send(embed=dm_embed)
            except:
                pass
            
        else:
            await interaction.response.send_message(f"{kullanici.mention} şu anda susturulmamış.", ephemeral=True)
        
    except discord.Forbidden:
        await interaction.response.send_message("Bu kullanıcının susturmasını kaldırmak için yeterli yetkiye sahip değilim!", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"Bir hata oluştu: {e}", ephemeral=True)

# Mesaj silme komutu
@bot.tree.command(name="temizle", description="Belirli sayıda mesajı sil")
@app_commands.describe(
    adet="Silinecek mesaj adedi (1-100)",
    kullanici="Sadece belirli bir kullanıcının mesajlarını sil (isteğe bağlı)"
)
@app_commands.default_permissions(manage_messages=True)
async def clear(interaction: discord.Interaction, adet: int, kullanici: discord.Member = None):
    # Adet kontrolü
    if adet < 1 or adet > 100:
        await interaction.response.send_message("Lütfen 1 ile 100 arasında bir değer girin.", ephemeral=True)
        return
    
    # Mesajları silme
    try:
        await interaction.response.defer(ephemeral=True)
        
        if kullanici:
            # Belirli bir kullanıcının mesajlarını sil
            def check(message):
                return message.author == kullanici
            
            deleted = await interaction.channel.purge(limit=adet, check=check)
            await interaction.followup.send(f"{len(deleted)} adet {kullanici.mention} tarafından gönderilen mesaj silindi.", ephemeral=True)
        else:
            # Tüm mesajları sil
            deleted = await interaction.channel.purge(limit=adet)
            await interaction.followup.send(f"{len(deleted)} adet mesaj silindi.", ephemeral=True)
        
    except discord.Forbidden:
        await interaction.followup.send("Mesajları silmek için yeterli yetkiye sahip değilim!", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"Bir hata oluştu: {e}", ephemeral=True)

# Uyarı komutu
@bot.tree.command(name="uyarı", description="Bir kullanıcıya uyarı ver")
@app_commands.describe(
    kullanici="Uyarılacak kullanıcı",
    sebep="Uyarı sebebi"
)
@app_commands.default_permissions(kick_members=True)
async def warn(interaction: discord.Interaction, kullanici: discord.Member, sebep: str):
    # Kendine uyarı veremez
    if kullanici == interaction.user:
        await interaction.response.send_message("Kendinize uyarı veremezsiniz!", ephemeral=True)
        return
    
    if kullanici.bot:
        await interaction.response.send_message("Botlara uyarı veremezsiniz!", ephemeral=True)
        return
    
    # Yetkili kontrolü
    if kullanici.top_role >= interaction.user.top_role and interaction.user.id != interaction.guild.owner_id:
        await interaction.response.send_message("Bu kullanıcıya uyarı vermek için yetkiniz yok! Sizden daha yüksek ya da aynı yetkide.", ephemeral=True)
        return
    
    # Uyarı mesajları
    embed = discord.Embed(
        title="⚠️ Kullanıcı Uyarıldı",
        description=f"{kullanici.mention} kullanıcısı uyarıldı.",
        color=discord.Color.yellow()
    )
    embed.add_field(name="Sebep", value=sebep, inline=False)
    embed.set_footer(text=f"{interaction.user} tarafından uyarıldı")
    add_default_footer(embed)
    
    await interaction.response.send_message(embed=embed, ephemeral=False)
    
    # DM olarak bildirim göndermeye çalış
    try:
        dm_embed = discord.Embed(
            title=f"⚠️ {interaction.guild.name} sunucusunda uyarı aldınız",
            description=f"Yetkili: {interaction.user.mention}",
            color=discord.Color.yellow()
        )
        dm_embed.add_field(name="Sebep", value=sebep, inline=False)
        add_default_footer(dm_embed)
        
        await kullanici.send(embed=dm_embed)
    except:
        await interaction.followup.send(f"{kullanici.mention} kullanıcısına DM gönderilemedi, mesajları kapalı olabilir.", ephemeral=True)

# Start the bot
if __name__ == "__main__":
    bot.run(config["token"]) 