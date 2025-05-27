# Discord Ticket Bot

A Discord bot that allows users to create support tickets with category selection.

## Features

- Create tickets with category selection and emojis
- User information form (name, surname, email, reason)
- Automatic ticket channel creation
- Staff role access to all tickets
- Category-specific support team roles
- Support team tagging in new tickets
- Ticket closing button
- Ticket freezing functionality - pause and resume user messaging
- Closed tickets are moved to a dedicated archive category
- Ticket logs in a designated channel
- Direct message notifications to users about ticket status changes

## Setup

1. Install Python 3.8 or higher
2. Install required packages: `pip install discord.py`
3. Create a Discord bot on the [Discord Developer Portal](https://discord.com/developers/applications)
4. Enable all Privileged Gateway Intents (SERVER MEMBERS INTENT, MESSAGE CONTENT INTENT)
5. Invite the bot to your server with the correct permissions (Administrator is recommended)
6. Replace `YOUR_BOT_TOKEN_HERE` in the `config.json` file with your bot's token (it will be created automatically on first run)
7. Create a category for archived tickets in your Discord server
8. Create support team roles for each ticket category (optional)

## Usage

1. Run the bot: `python bot.py`
2. Use the `/kurulum` command in the channel where you want to set up the ticket creation
   - The bot will ask you to enter the Archive Category ID
   - After entering the ID, you'll be prompted to select support team roles for each ticket category
   - You can skip assigning a role to any category
3. Use the `/yetkilirol` command to set which role has access to all tickets (general staff role)
4. Use the `/logkanal` command to set a channel for ticket logs
5. Use the `/arşivkategorisi` command to change the archive category later if needed
6. Use the `/destekekibi` command to change support team roles for specific categories later if needed

## Commands

- `/kurulum` - Creates the ticket panel and guides you through the setup process
- `/yetkilirol` - Sets which role has access to all tickets as general staff
- `/logkanal` - Sets a channel for ticket logs
- `/arşivkategorisi` - Sets the category for archived tickets
- `/destekekibi` - Sets the support team role for a specific ticket category

## Ticket Controls

Each ticket has two control buttons:

1. **Talebi Kapat** (Close Ticket) - Red button that closes the ticket and moves it to the archive category
2. **Talebi Dondur** (Freeze Ticket) - Blue button that toggles whether users can send messages in the ticket
   - When a ticket is frozen, regular users cannot send messages
   - Staff and support team members can still send messages
   - Pressing the button again unfreezes the ticket
   - The button changes to "Talebi Aç" (Unfreeze Ticket) when frozen

Only staff members and support teams can use the freeze button.

## Direct Message Notifications

The bot sends personalized direct messages to users when their ticket status changes:

1. **When a ticket is created**: "Merhaba [username], talebiniz şu anda açıktır. Destek ekibimiz en kısa sürede size yardımcı olacaktır."
2. **When a ticket is frozen**: "Merhaba [username], talebiniz şu anda dondurulmuştur. Geçici olarak mesaj gönderemezsiniz."
3. **When a ticket is unfrozen**: "Merhaba [username], talebiniz şu anda açıktır. Artık mesaj gönderebilirsiniz."
4. **When a ticket is closed**: "Merhaba [username], talebiniz kapatılmıştır. Teşekkür ederiz."

These notifications ensure users are always informed about the status of their tickets, even when they're not actively monitoring the server.

## Support Team Assignment

During setup, you'll be asked to assign a support team role to each ticket category. When a user creates a ticket:

1. The ticket will automatically tag the relevant support team role in the initial message
2. The support team role will be given access to the ticket channel
3. This enables different teams to handle different types of tickets

## Turkish Command Translations

| English | Turkish |
|---------|---------|
| setup | kurulum |
| setstaffrole | yetkilirol |
| setlogchannel | logkanal |
| setarchivecategory | arşivkategorisi |
| setsupportteam | destekekibi |
| Support Tickets | Destek Talepleri |
| Close Ticket | Talebi Kapat |
| Freeze Ticket | Talebi Dondur |
| Unfreeze Ticket | Talebi Aç |
| General Support | Genel Destek |
| Technical Issue | Teknik Sorun |
| Billing | Ödeme |
| Other | Diğer |
| First Name | Adınız |
| Last Name | Soyadınız |
| Email | E-posta Adresiniz |
| Reason | Talep Sebebiniz |
| Support Team | Destek Ekibi |
| Archive Category | Arşiv Kategorisi |

## How it Works

1. Users select a category from the dropdown menu with emojis
2. A form appears asking for their name, surname, email, and reason for opening the ticket
3. A new ticket channel is created with the user's information
4. The appropriate support team is tagged in the initial message
5. The user and support team can communicate in the ticket channel
6. Staff can freeze the ticket to prevent users from sending messages temporarily
7. When resolved, anyone can close the ticket using the "Talebi Kapat" button
8. Closed tickets are moved to the designated archive category
9. Users receive direct message notifications about all ticket status changes

## Category Emojis

- ❓ Genel Destek (General Support)
- 🔧 Teknik Sorun (Technical Issue)
- 💰 Ödeme (Billing)
- 📝 Diğer (Other)

## Customization

You can modify the ticket categories and their emojis by editing the `TICKET_CATEGORIES` list in the `bot.py` file. 