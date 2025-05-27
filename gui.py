import customtkinter as ctk
import json
import os
from PIL import Image
import webbrowser
from datetime import datetime

class DiscosoftBotGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Temel pencere ayarları
        self.title("Discosoft Bot GUI")
        self.geometry("1000x600")
        
        # Tema ayarları
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Config dosyası için varsayılan değerler
        self.default_config = {
            "bot_settings": {
                "token": "",
                "prefix": "!",
                "status": "online",
                "activity": "Discosoft Bot"
            },
            "channels": {
                "log_channel_id": "",
                "welcome_channel_id": "",
                "announcement_channel_id": ""
            },
            "moderation": {
                "enabled": False,
                "warn_threshold": 3,
                "mute_duration": 300,
                "auto_mod": {
                    "spam_protection": False,
                    "link_filter": False,
                    "caps_filter": False,
                    "invite_filter": False,
                    "mass_mention_filter": False
                }
            },
            "welcome_settings": {
                "enabled": False,
                "message": "Hoş geldin {user}!",
                "embed_color": "#00ff00",
                "show_member_count": True
            },
            "autorole": {
                "enabled": False,
                "role_id": "",
                "delay": 0,
                "send_dm": False,
                "dm_message": "Size {role} rolü verildi!",
                "announce_channel_id": "",
                "announce_message": "Yeni üyeye {role} rolü verildi!",
                "embed_color": "#00ff00"
            },
            "logging": {
                "enabled": False,
                "embed_color": "#ff0000",
                "show_timestamp": True,
                "events": {
                    "message_delete": False,
                    "message_edit": False,
                    "member_join": False,
                    "member_leave": False,
                    "member_ban": False,
                    "member_unban": False,
                    "member_kick": False,
                    "member_timeout": False,
                    "channel_create": False,
                    "channel_delete": False,
                    "channel_update": False,
                    "role_create": False,
                    "role_delete": False,
                    "role_update": False,
                    "voice_join": False,
                    "voice_leave": False,
                    "voice_move": False
                }
            },
            "level_system": {
                "enabled": False,
                "xp_per_message": 15,
                "xp_cooldown": 60,
                "level_up_channel_id": "",
                "level_up_message": "Tebrikler {user}! Artık seviye {level}!",
                "level_roles": {}
            },
            "custom_commands": [],
            "reaction_roles": []
        }
        
        # Derin kopya oluştur
        self.config = json.loads(json.dumps(self.default_config))
        
        # Config'i yükle ve varsayılan değerleri ekle
        self.load_config()
        self.create_widgets()

    def load_config(self):
        """Mevcut config dosyasını yükler ve varsayılan değerlerle birleştirir"""
        try:
            if os.path.exists("config.json"):
                with open("config.json", "r", encoding="utf-8") as f:
                    saved_config = json.load(f)
                    # Mevcut config ile varsayılan config'i birleştir
                    self.merge_configs(self.config, saved_config)
        except Exception as e:
            self.show_notification("Hata", f"Config yüklenirken hata oluştu: {e}")

    def merge_configs(self, default_config, saved_config):
        """İki config'i recursive olarak birleştirir"""
        for key, value in saved_config.items():
            if key in default_config:
                if isinstance(value, dict) and isinstance(default_config[key], dict):
                    self.merge_configs(default_config[key], value)
                else:
                    default_config[key] = value

    def save_config(self):
        """Config'i dosyaya kaydeder"""
        try:
            with open("config.json", "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            self.show_notification("Başarılı", "Ayarlar başarıyla kaydedildi!")
        except Exception as e:
            self.show_notification("Hata", f"Ayarlar kaydedilirken hata: {e}")

    def create_widgets(self):
        # Ana frame'ler
        self.sidebar = ctk.CTkFrame(self, width=250, corner_radius=0)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        self.main_frame = ctk.CTkFrame(self, corner_radius=0)
        self.main_frame.pack(side="right", fill="both", expand=True)

        # Logo ve başlık
        logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo_frame.pack(pady=20, padx=20)

        title_label = ctk.CTkLabel(logo_frame, text="Discosoft", font=("Arial", 24, "bold"))
        title_label.pack()
        subtitle_label = ctk.CTkLabel(logo_frame, text="Bot Yönetim Paneli", font=("Arial", 12))
        subtitle_label.pack()

        # Ayarlar kategorileri
        categories_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        categories_frame.pack(fill="x", pady=20)

        self.create_sidebar_buttons()

        # Alt bilgi
        footer_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        footer_frame.pack(side="bottom", pady=10)
        
        version_label = ctk.CTkLabel(footer_frame, text="v1.0.0", font=("Arial", 10))
        version_label.pack()

        # Varsayılan olarak genel ayarları göster
        self.show_general_settings()

    def create_sidebar_buttons(self):
        buttons = [
            ("⚙ Genel Ayarlar", self.show_general_settings),
            ("🛡 Moderasyon", self.show_moderation_settings),
            ("👋 Hoş Geldin Sistemi", self.show_welcome_settings),
            ("🎖 Rol Yönetimi", self.show_autorole_settings),
            ("📝 Kayıt Sistemi", self.show_logging_settings),
            ("⭐ Seviye Sistemi", self.show_level_settings),
            ("🕹 Özel Komutlar", self.show_custom_commands),
            ("🔔 Reaksiyon Rolleri", self.show_reaction_roles),
            ("🔥 Bot Başlat", self.start_bot)
        ]

        for text, command in buttons:
            btn = ctk.CTkButton(
                self.sidebar,
                text=text,
                command=command,
                width=220,
                height=40,
                corner_radius=8,
                fg_color="transparent",
                text_color=("gray10", "gray90"),
                hover_color=("gray70", "gray30"),
                anchor="w",
                font=("Arial", 12)
            )
            btn.pack(pady=2, padx=15)

    def clear_main_frame(self):
        """Ana frame'deki tüm widget'ları temizler"""
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    def show_general_settings(self):
        self.clear_main_frame()
        
        # Başlık
        header_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=30, pady=(20, 10))
        
        title = ctk.CTkLabel(header_frame, text="⚙ Genel Ayarlar", font=("Arial", 24, "bold"))
        title.pack(side="left")

        # Ana ayarlar container
        settings_container = ctk.CTkScrollableFrame(self.main_frame)
        settings_container.pack(fill="both", expand=True, padx=30, pady=(0, 20))

        # Bot Ayarları Bölümü
        bot_section = ctk.CTkFrame(settings_container)
        bot_section.pack(fill="x", pady=10)

        ctk.CTkLabel(bot_section, text="Bot Ayarları", font=("Arial", 16, "bold")).pack(anchor="w", padx=15, pady=5)

        # Token girişi
        token_frame = ctk.CTkFrame(bot_section, fg_color="transparent")
        token_frame.pack(fill="x", padx=15, pady=5)
        
        ctk.CTkLabel(token_frame, text="Bot Token:", font=("Arial", 12)).pack(side="left")
        token_entry = ctk.CTkEntry(token_frame, width=400, show="*")
        token_entry.pack(side="left", padx=10)
        token_entry.insert(0, self.config["bot_settings"]["token"])

        # Prefix girişi
        prefix_frame = ctk.CTkFrame(bot_section, fg_color="transparent")
        prefix_frame.pack(fill="x", padx=15, pady=5)
        
        ctk.CTkLabel(prefix_frame, text="Komut Prefix:", font=("Arial", 12)).pack(side="left")
        prefix_entry = ctk.CTkEntry(prefix_frame, width=100)
        prefix_entry.pack(side="left", padx=10)
        prefix_entry.insert(0, self.config["bot_settings"]["prefix"])

        # Bot durumu
        status_frame = ctk.CTkFrame(bot_section, fg_color="transparent")
        status_frame.pack(fill="x", padx=15, pady=5)
        
        ctk.CTkLabel(status_frame, text="Bot Durumu:", font=("Arial", 12)).pack(side="left")
        status_menu = ctk.CTkOptionMenu(
            status_frame,
            values=["online", "idle", "dnd", "invisible"],
            width=150
        )
        status_menu.pack(side="left", padx=10)
        status_menu.set(self.config["bot_settings"]["status"])

        # Bot aktivitesi
        activity_frame = ctk.CTkFrame(bot_section, fg_color="transparent")
        activity_frame.pack(fill="x", padx=15, pady=5)
        
        ctk.CTkLabel(activity_frame, text="Bot Aktivitesi:", font=("Arial", 12)).pack(side="left")
        activity_entry = ctk.CTkEntry(activity_frame, width=200)
        activity_entry.pack(side="left", padx=10)
        activity_entry.insert(0, self.config["bot_settings"]["activity"])

        # Kanal Ayarları Bölümü
        channels_section = ctk.CTkFrame(settings_container)
        channels_section.pack(fill="x", pady=10)

        ctk.CTkLabel(channels_section, text="Kanal Ayarları", font=("Arial", 16, "bold")).pack(anchor="w", padx=15, pady=5)

        # Log kanalı
        log_frame = ctk.CTkFrame(channels_section, fg_color="transparent")
        log_frame.pack(fill="x", padx=15, pady=5)
        
        ctk.CTkLabel(log_frame, text="Log Kanal ID:", font=("Arial", 12)).pack(side="left")
        log_entry = ctk.CTkEntry(log_frame, width=200)
        log_entry.pack(side="left", padx=10)
        log_entry.insert(0, self.config["channels"]["log_channel_id"])

        # Duyuru kanalı
        announcement_frame = ctk.CTkFrame(channels_section, fg_color="transparent")
        announcement_frame.pack(fill="x", padx=15, pady=5)
        
        ctk.CTkLabel(announcement_frame, text="Duyuru Kanal ID:", font=("Arial", 12)).pack(side="left")
        announcement_entry = ctk.CTkEntry(announcement_frame, width=200)
        announcement_entry.pack(side="left", padx=10)
        announcement_entry.insert(0, self.config["channels"]["announcement_channel_id"])

        # Kaydet butonu
        def save():
            self.config["bot_settings"].update({
                "token": token_entry.get(),
                "prefix": prefix_entry.get(),
                "status": status_menu.get(),
                "activity": activity_entry.get()
            })
            
            self.config["channels"].update({
                "log_channel_id": log_entry.get(),
                "announcement_channel_id": announcement_entry.get()
            })
            
            self.save_config()

        save_btn = ctk.CTkButton(
            self.main_frame,
            text="Ayarları Kaydet",
            command=save,
            width=200,
            height=40,
            corner_radius=8,
            font=("Arial", 14, "bold")
        )
        save_btn.pack(pady=20)

    def show_moderation_settings(self):
        self.clear_main_frame()
        
        header_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=30, pady=(20, 10))
        
        title = ctk.CTkLabel(header_frame, text="🛡 Moderasyon", font=("Arial", 24, "bold"))
        title.pack(side="left")

        settings_container = ctk.CTkScrollableFrame(self.main_frame)
        settings_container.pack(fill="both", expand=True, padx=30, pady=(0, 20))

        # Moderasyon açık/kapalı
        mod_switch = ctk.CTkSwitch(
            settings_container,
            text="Moderasyon Sistemi",
            font=("Arial", 14, "bold"),
            command=lambda: setattr(self.config["moderation"], "enabled", mod_switch.get())
        )
        mod_switch.pack(pady=10)
        mod_switch.select() if self.config["moderation"]["enabled"] else mod_switch.deselect()

        # Auto-mod ayarları
        automod_frame = ctk.CTkFrame(settings_container)
        automod_frame.pack(fill="x", pady=10)

        ctk.CTkLabel(automod_frame, text="Otomatik Moderasyon", font=("Arial", 16, "bold")).pack(anchor="w", padx=15, pady=5)

        switches = [
            ("Spam Koruması", "spam_protection"),
            ("Link Filtresi", "link_filter"),
            ("Büyük Harf Filtresi", "caps_filter"),
            ("Davet Filtresi", "invite_filter"),
            ("Toplu Etiket Filtresi", "mass_mention_filter")
        ]

        for text, key in switches:
            switch_frame = ctk.CTkFrame(automod_frame, fg_color="transparent")
            switch_frame.pack(fill="x", padx=15, pady=2)
            
            switch = ctk.CTkSwitch(
                switch_frame,
                text=text,
                font=("Arial", 12),
                command=lambda k=key, s=None: self.config["moderation"]["auto_mod"].update({k: s.get()})
            )
            switch.pack(side="left")
            switch.select() if self.config["moderation"]["auto_mod"][key] else switch.deselect()
            switch.configure(command=lambda k=key, s=switch: self.config["moderation"]["auto_mod"].update({k: s.get()}))

        # Ceza ayarları
        punishment_frame = ctk.CTkFrame(settings_container)
        punishment_frame.pack(fill="x", pady=10)

        ctk.CTkLabel(punishment_frame, text="Ceza Ayarları", font=("Arial", 16, "bold")).pack(anchor="w", padx=15, pady=5)

        # Uyarı eşiği
        warn_frame = ctk.CTkFrame(punishment_frame, fg_color="transparent")
        warn_frame.pack(fill="x", padx=15, pady=5)
        
        ctk.CTkLabel(warn_frame, text="Uyarı Eşiği:", font=("Arial", 12)).pack(side="left")
        warn_entry = ctk.CTkEntry(warn_frame, width=100)
        warn_entry.pack(side="left", padx=10)
        warn_entry.insert(0, str(self.config["moderation"]["warn_threshold"]))

        # Susturma süresi
        mute_frame = ctk.CTkFrame(punishment_frame, fg_color="transparent")
        mute_frame.pack(fill="x", padx=15, pady=5)
        
        ctk.CTkLabel(mute_frame, text="Susturma Süresi (saniye):", font=("Arial", 12)).pack(side="left")
        mute_entry = ctk.CTkEntry(mute_frame, width=100)
        mute_entry.pack(side="left", padx=10)
        mute_entry.insert(0, str(self.config["moderation"]["mute_duration"]))

        def save():
            try:
                warn_value = int(warn_entry.get())
                mute_value = int(mute_entry.get())
                
                self.config["moderation"].update({
                    "warn_threshold": warn_value,
                    "mute_duration": mute_value
                })
                
                self.save_config()
            except ValueError:
                self.show_notification("Hata", "Uyarı eşiği ve susturma süresi sayısal olmalıdır!")

        save_btn = ctk.CTkButton(
            self.main_frame,
            text="Ayarları Kaydet",
            command=save,
            width=200,
            height=40,
            corner_radius=8,
            font=("Arial", 14, "bold")
        )
        save_btn.pack(pady=20)

    def show_logging_settings(self):
        self.clear_main_frame()
        
        header_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=30, pady=(20, 10))
        
        title = ctk.CTkLabel(header_frame, text="📝 Kayıt Sistemi", font=("Arial", 24, "bold"))
        title.pack(side="left")

        settings_container = ctk.CTkScrollableFrame(self.main_frame)
        settings_container.pack(fill="both", expand=True, padx=30, pady=(0, 20))

        # Ana anahtar
        main_switch = ctk.CTkSwitch(
            settings_container,
            text="Log Sistemi Aktif",
            font=("Arial", 14, "bold"),
            command=lambda: setattr(self.config["logging"], "enabled", main_switch.get())
        )
        main_switch.pack(pady=10)
        main_switch.select() if self.config["logging"]["enabled"] else main_switch.deselect()

        # Kanal ayarları
        channel_frame = ctk.CTkFrame(settings_container)
        channel_frame.pack(fill="x", pady=10)

        ctk.CTkLabel(channel_frame, text="Kanal Ayarları", font=("Arial", 16, "bold")).pack(anchor="w", padx=15, pady=5)

        # Log kanalı ID
        log_frame = ctk.CTkFrame(channel_frame, fg_color="transparent")
        log_frame.pack(fill="x", padx=15, pady=5)
        
        ctk.CTkLabel(log_frame, text="Log Kanal ID:", font=("Arial", 12)).pack(side="left")
        log_entry = ctk.CTkEntry(log_frame, width=200)
        log_entry.pack(side="left", padx=10)
        log_entry.insert(0, self.config["channels"]["log_channel_id"])

        # Log olayları
        events_frame = ctk.CTkFrame(settings_container)
        events_frame.pack(fill="x", pady=10)

        ctk.CTkLabel(events_frame, text="Log Olayları", font=("Arial", 16, "bold")).pack(anchor="w", padx=15, pady=5)

        events = {
            "message_delete": "Mesaj Silme",
            "message_edit": "Mesaj Düzenleme",
            "member_join": "Üye Katılma",
            "member_leave": "Üye Ayrılma",
            "member_ban": "Üye Yasaklama",
            "member_unban": "Yasak Kaldırma",
            "member_kick": "Üye Atma",
            "member_timeout": "Üye Susturma",
            "channel_create": "Kanal Oluşturma",
            "channel_delete": "Kanal Silme",
            "channel_update": "Kanal Güncelleme",
            "role_create": "Rol Oluşturma",
            "role_delete": "Rol Silme",
            "role_update": "Rol Güncelleme",
            "voice_join": "Ses Kanalına Katılma",
            "voice_leave": "Ses Kanalından Ayrılma",
            "voice_move": "Ses Kanalı Değiştirme"
        }

        # Olayları 3 sütuna böl
        columns = 3
        events_per_column = len(events) // columns + (1 if len(events) % columns else 0)

        # Ana frame
        columns_frame = ctk.CTkFrame(events_frame, fg_color="transparent")
        columns_frame.pack(fill="x", padx=15, pady=5)

        # Sütunları oluştur
        column_frames = []
        for i in range(columns):
            frame = ctk.CTkFrame(columns_frame, fg_color="transparent")
            frame.pack(side="left", fill="both", expand=True, padx=5)
            column_frames.append(frame)

        # Olayları sütunlara dağıt
        event_items = list(events.items())
        for i, (key, text) in enumerate(event_items):
            column_index = i // events_per_column
            if column_index >= columns:
                continue

            switch = ctk.CTkSwitch(
                column_frames[column_index],
                text=text,
                font=("Arial", 12)
            )
            switch.pack(anchor="w", pady=2)
            switch.select() if self.config["logging"]["events"].get(key, False) else switch.deselect()
            switch.configure(command=lambda k=key, s=switch: self.config["logging"]["events"].update({k: s.get()}))

        # Embed ayarları
        embed_frame = ctk.CTkFrame(settings_container)
        embed_frame.pack(fill="x", pady=10)

        ctk.CTkLabel(embed_frame, text="Embed Ayarları", font=("Arial", 16, "bold")).pack(anchor="w", padx=15, pady=5)

        # Embed rengi
        color_frame = ctk.CTkFrame(embed_frame, fg_color="transparent")
        color_frame.pack(fill="x", padx=15, pady=5)
        
        ctk.CTkLabel(color_frame, text="Embed Rengi:", font=("Arial", 12)).pack(side="left")
        color_entry = ctk.CTkEntry(color_frame, width=100)
        color_entry.pack(side="left", padx=10)
        color_entry.insert(0, self.config["logging"]["embed_color"])

        # Zaman damgası
        timestamp_switch = ctk.CTkSwitch(
            embed_frame,
            text="Zaman Damgası Göster",
            font=("Arial", 12),
            command=lambda: setattr(self.config["logging"], "show_timestamp", timestamp_switch.get())
        )
        timestamp_switch.pack(anchor="w", padx=15, pady=5)
        timestamp_switch.select() if self.config["logging"]["show_timestamp"] else timestamp_switch.deselect()

        def save():
            self.config["channels"]["log_channel_id"] = log_entry.get()
            self.config["logging"]["embed_color"] = color_entry.get()
            self.save_config()

        save_btn = ctk.CTkButton(
            self.main_frame,
            text="Ayarları Kaydet",
            command=save,
            width=200,
            height=40,
            corner_radius=8,
            font=("Arial", 14, "bold")
        )
        save_btn.pack(pady=20)

    def show_welcome_settings(self):
        self.clear_main_frame()
        
        header_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=30, pady=(20, 10))
        
        title = ctk.CTkLabel(header_frame, text="👋 Hoş Geldin Sistemi", font=("Arial", 24, "bold"))
        title.pack(side="left")

        settings_container = ctk.CTkScrollableFrame(self.main_frame)
        settings_container.pack(fill="both", expand=True, padx=30, pady=(0, 20))

        # Ana anahtar
        main_switch = ctk.CTkSwitch(
            settings_container,
            text="Hoş Geldin Sistemi Aktif",
            font=("Arial", 14, "bold"),
            command=lambda: self.config["welcome_settings"].update({"enabled": main_switch.get()})
        )
        main_switch.pack(pady=10)
        main_switch.select() if self.config["welcome_settings"]["enabled"] else main_switch.deselect()

        # Hoş geldin kanalı
        channel_frame = ctk.CTkFrame(settings_container)
        channel_frame.pack(fill="x", pady=10)

        ctk.CTkLabel(channel_frame, text="Kanal Ayarları", font=("Arial", 16, "bold")).pack(anchor="w", padx=15, pady=5)

        # Hoş geldin kanalı ID
        welcome_frame = ctk.CTkFrame(channel_frame, fg_color="transparent")
        welcome_frame.pack(fill="x", padx=15, pady=5)
        
        ctk.CTkLabel(welcome_frame, text="Hoş Geldin Kanal ID:", font=("Arial", 12)).pack(side="left")
        welcome_entry = ctk.CTkEntry(welcome_frame, width=200)
        welcome_entry.pack(side="left", padx=10)
        welcome_entry.insert(0, self.config["channels"]["welcome_channel_id"])

        # Mesaj ayarları
        message_frame = ctk.CTkFrame(settings_container)
        message_frame.pack(fill="x", pady=10)

        ctk.CTkLabel(message_frame, text="Mesaj Ayarları", font=("Arial", 16, "bold")).pack(anchor="w", padx=15, pady=5)

        # Hoş geldin mesajı
        msg_content_frame = ctk.CTkFrame(message_frame, fg_color="transparent")
        msg_content_frame.pack(fill="x", padx=15, pady=5)
        
        ctk.CTkLabel(msg_content_frame, text="Hoş Geldin Mesajı:", font=("Arial", 12)).pack(anchor="w", pady=(0, 5))
        message_entry = ctk.CTkTextbox(msg_content_frame, height=100)
        message_entry.pack(fill="x", pady=5)
        message_entry.insert("1.0", self.config["welcome_settings"]["message"])

        # Embed rengi
        color_frame = ctk.CTkFrame(message_frame, fg_color="transparent")
        color_frame.pack(fill="x", padx=15, pady=5)
        
        ctk.CTkLabel(color_frame, text="Embed Rengi:", font=("Arial", 12)).pack(side="left")
        color_entry = ctk.CTkEntry(color_frame, width=100)
        color_entry.pack(side="left", padx=10)
        color_entry.insert(0, self.config["welcome_settings"]["embed_color"])

        # Üye sayısı gösterimi
        count_switch = ctk.CTkSwitch(
            message_frame,
            text="Üye Sayısını Göster",
            font=("Arial", 12),
            command=lambda: self.config["welcome_settings"].update({"show_member_count": count_switch.get()})
        )
        count_switch.pack(anchor="w", padx=15, pady=10)
        count_switch.select() if self.config["welcome_settings"]["show_member_count"] else count_switch.deselect()

        def save():
            self.config["channels"]["welcome_channel_id"] = welcome_entry.get()
            self.config["welcome_settings"].update({
                "message": message_entry.get("1.0", "end-1c"),
                "embed_color": color_entry.get()
            })
            self.save_config()
            self.show_notification("Başarılı", "Hoş geldin sistemi ayarları kaydedildi!")

        save_btn = ctk.CTkButton(
            self.main_frame,
            text="Ayarları Kaydet",
            command=save,
            width=200,
            height=40,
            corner_radius=8,
            font=("Arial", 14, "bold")
        )
        save_btn.pack(pady=20)

    def show_autorole_settings(self):
        self.clear_main_frame()
        
        header_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=30, pady=(20, 10))
        
        title = ctk.CTkLabel(header_frame, text="🎖 Rol Yönetimi", font=("Arial", 24, "bold"))
        title.pack(side="left")

        settings_container = ctk.CTkScrollableFrame(self.main_frame)
        settings_container.pack(fill="both", expand=True, padx=30, pady=(0, 20))

        # Ana anahtar
        main_switch = ctk.CTkSwitch(
            settings_container,
            text="Otorol Sistemi Aktif",
            font=("Arial", 14, "bold"),
            command=lambda: self.config["autorole"].update({"enabled": main_switch.get()})
        )
        main_switch.pack(pady=10)
        main_switch.select() if self.config["autorole"]["enabled"] else main_switch.deselect()

        # Rol ayarları
        role_frame = ctk.CTkFrame(settings_container)
        role_frame.pack(fill="x", pady=10)

        ctk.CTkLabel(role_frame, text="Rol Ayarları", font=("Arial", 16, "bold")).pack(anchor="w", padx=15, pady=5)

        # Otorol ID
        role_id_frame = ctk.CTkFrame(role_frame, fg_color="transparent")
        role_id_frame.pack(fill="x", padx=15, pady=5)
        
        ctk.CTkLabel(role_id_frame, text="Otorol ID:", font=("Arial", 12)).pack(side="left")
        role_id_entry = ctk.CTkEntry(role_id_frame, width=200)
        role_id_entry.pack(side="left", padx=10)
        role_id_entry.insert(0, self.config["autorole"]["role_id"])

        # Duyuru ayarları
        announce_frame = ctk.CTkFrame(settings_container)
        announce_frame.pack(fill="x", pady=10)

        ctk.CTkLabel(announce_frame, text="Duyuru Ayarları", font=("Arial", 16, "bold")).pack(anchor="w", padx=15, pady=5)

        # Duyuru kanalı
        channel_frame = ctk.CTkFrame(announce_frame, fg_color="transparent")
        channel_frame.pack(fill="x", padx=15, pady=5)
        
        ctk.CTkLabel(channel_frame, text="Duyuru Kanal ID:", font=("Arial", 12)).pack(side="left")
        channel_entry = ctk.CTkEntry(channel_frame, width=200)
        channel_entry.pack(side="left", padx=10)
        channel_entry.insert(0, self.config["autorole"]["announce_channel_id"])

        # Duyuru mesajı
        message_frame = ctk.CTkFrame(announce_frame, fg_color="transparent")
        message_frame.pack(fill="x", padx=15, pady=5)
        
        ctk.CTkLabel(message_frame, text="Duyuru Mesajı:", font=("Arial", 12)).pack(anchor="w", pady=(0, 5))
        message_entry = ctk.CTkTextbox(message_frame, height=100)
        message_entry.pack(fill="x", pady=5)
        message_entry.insert("1.0", self.config["autorole"]["announce_message"])

        # Embed ayarları
        embed_frame = ctk.CTkFrame(settings_container)
        embed_frame.pack(fill="x", pady=10)

        ctk.CTkLabel(embed_frame, text="Embed Ayarları", font=("Arial", 16, "bold")).pack(anchor="w", padx=15, pady=5)

        # Embed rengi
        color_frame = ctk.CTkFrame(embed_frame, fg_color="transparent")
        color_frame.pack(fill="x", padx=15, pady=5)
        
        ctk.CTkLabel(color_frame, text="Embed Rengi:", font=("Arial", 12)).pack(side="left")
        color_entry = ctk.CTkEntry(color_frame, width=100)
        color_entry.pack(side="left", padx=10)
        color_entry.insert(0, self.config["autorole"].get("embed_color", "#00ff00"))

        def save():
            self.config["autorole"].update({
                "role_id": role_id_entry.get(),
                "announce_channel_id": channel_entry.get(),
                "announce_message": message_entry.get("1.0", "end-1c"),
                "embed_color": color_entry.get()
            })
            self.save_config()
            self.show_notification("Başarılı", "Otorol sistemi ayarları kaydedildi!")

        save_btn = ctk.CTkButton(
            self.main_frame,
            text="Ayarları Kaydet",
            command=save,
            width=200,
            height=40,
            corner_radius=8,
            font=("Arial", 14, "bold")
        )
        save_btn.pack(pady=20)

    def show_custom_commands(self):
        self.clear_main_frame()
        
        header_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=30, pady=(20, 10))
        
        title = ctk.CTkLabel(header_frame, text="🕹 Özel Komutlar", font=("Arial", 24, "bold"))
        title.pack(side="left")

        add_btn = ctk.CTkButton(
            header_frame,
            text="+ Yeni Komut Ekle",
            width=150,
            height=35,
            corner_radius=8
        )
        add_btn.pack(side="right")

        # Komut listesi
        commands_container = ctk.CTkScrollableFrame(self.main_frame)
        commands_container.pack(fill="both", expand=True, padx=30, pady=(0, 20))

        # Komutları göster
        for command in self.config["custom_commands"]:
            command_frame = ctk.CTkFrame(commands_container)
            command_frame.pack(fill="x", pady=5)

            # Komut adı
            name_frame = ctk.CTkFrame(command_frame, fg_color="transparent")
            name_frame.pack(fill="x", padx=15, pady=5)

            ctk.CTkLabel(name_frame, text="Komut:", font=("Arial", 12, "bold")).pack(side="left")
            name_entry = ctk.CTkEntry(name_frame, width=200)
            name_entry.pack(side="left", padx=10)
            name_entry.insert(0, command["name"])

            # Yanıt
            response_frame = ctk.CTkFrame(command_frame, fg_color="transparent")
            response_frame.pack(fill="x", padx=15, pady=5)

            ctk.CTkLabel(response_frame, text="Yanıt:", font=("Arial", 12, "bold")).pack(anchor="w")
            response_entry = ctk.CTkTextbox(response_frame, height=100)
            response_entry.pack(fill="x", pady=5)
            response_entry.insert("1.0", command["response"])

            # Embed rengi
            color_frame = ctk.CTkFrame(command_frame, fg_color="transparent")
            color_frame.pack(fill="x", padx=15, pady=5)

            ctk.CTkLabel(color_frame, text="Embed Rengi:", font=("Arial", 12, "bold")).pack(side="left")
            color_entry = ctk.CTkEntry(color_frame, width=100)
            color_entry.pack(side="left", padx=10)
            color_entry.insert(0, command.get("embed_color", "#00ff00"))

            # Kaydet ve Sil butonları
            button_frame = ctk.CTkFrame(command_frame, fg_color="transparent")
            button_frame.pack(fill="x", padx=15, pady=5)

            save_btn = ctk.CTkButton(
                button_frame,
                text="Kaydet",
                width=100,
                height=30,
                corner_radius=8,
                font=("Arial", 12)
            )
            save_btn.pack(side="left", padx=5)

            delete_btn = ctk.CTkButton(
                button_frame,
                text="Sil",
                width=100,
                height=30,
                corner_radius=8,
                fg_color="#ff0000",
                font=("Arial", 12)
            )
            delete_btn.pack(side="left", padx=5)

    def show_level_settings(self):
        self.clear_main_frame()
        
        header_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=30, pady=(20, 10))
        
        title = ctk.CTkLabel(header_frame, text="⬆️ Seviye Sistemi", font=("Arial", 24, "bold"))
        title.pack(side="left")

        settings_container = ctk.CTkScrollableFrame(self.main_frame)
        settings_container.pack(fill="both", expand=True, padx=30, pady=(0, 20))

        # Ana anahtar
        main_switch = ctk.CTkSwitch(
            settings_container,
            text="Seviye Sistemi Aktif",
            font=("Arial", 14, "bold"),
            command=lambda: self.config["level_system"].update({"enabled": main_switch.get()})
        )
        main_switch.pack(pady=10)
        main_switch.select() if self.config["level_system"]["enabled"] else main_switch.deselect()

        # XP ayarları
        xp_frame = ctk.CTkFrame(settings_container)
        xp_frame.pack(fill="x", pady=10)

        ctk.CTkLabel(xp_frame, text="XP Ayarları", font=("Arial", 16, "bold")).pack(anchor="w", padx=15, pady=5)

        # Mesaj başına XP
        msg_xp_frame = ctk.CTkFrame(xp_frame, fg_color="transparent")
        msg_xp_frame.pack(fill="x", padx=15, pady=5)
        
        ctk.CTkLabel(msg_xp_frame, text="Mesaj Başına XP:", font=("Arial", 12)).pack(side="left")
        msg_xp_entry = ctk.CTkEntry(msg_xp_frame, width=100)
        msg_xp_entry.pack(side="left", padx=10)
        msg_xp_entry.insert(0, str(self.config["level_system"]["xp_per_message"]))

        # XP bekleme süresi
        cooldown_frame = ctk.CTkFrame(xp_frame, fg_color="transparent")
        cooldown_frame.pack(fill="x", padx=15, pady=5)
        
        ctk.CTkLabel(cooldown_frame, text="XP Bekleme Süresi (saniye):", font=("Arial", 12)).pack(side="left")
        cooldown_entry = ctk.CTkEntry(cooldown_frame, width=100)
        cooldown_entry.pack(side="left", padx=10)
        cooldown_entry.insert(0, str(self.config["level_system"]["xp_cooldown"]))

        # Seviye atlama ayarları
        level_up_frame = ctk.CTkFrame(settings_container)
        level_up_frame.pack(fill="x", pady=10)

        ctk.CTkLabel(level_up_frame, text="Seviye Atlama Ayarları", font=("Arial", 16, "bold")).pack(anchor="w", padx=15, pady=5)

        # Duyuru kanalı
        channel_frame = ctk.CTkFrame(level_up_frame, fg_color="transparent")
        channel_frame.pack(fill="x", padx=15, pady=5)
        
        ctk.CTkLabel(channel_frame, text="Duyuru Kanal ID:", font=("Arial", 12)).pack(side="left")
        channel_entry = ctk.CTkEntry(channel_frame, width=200)
        channel_entry.pack(side="left", padx=10)
        channel_entry.insert(0, self.config["level_system"]["level_up_channel_id"])

        # Duyuru mesajı
        message_frame = ctk.CTkFrame(level_up_frame, fg_color="transparent")
        message_frame.pack(fill="x", padx=15, pady=5)
        
        ctk.CTkLabel(message_frame, text="Duyuru Mesajı:", font=("Arial", 12)).pack(anchor="w", pady=(0, 5))
        message_entry = ctk.CTkTextbox(message_frame, height=100)
        message_entry.pack(fill="x", pady=5)
        message_entry.insert("1.0", self.config["level_system"]["level_up_message"])

        # Embed ayarları
        embed_frame = ctk.CTkFrame(settings_container)
        embed_frame.pack(fill="x", pady=10)

        ctk.CTkLabel(embed_frame, text="Embed Ayarları", font=("Arial", 16, "bold")).pack(anchor="w", padx=15, pady=5)

        # Embed rengi
        color_frame = ctk.CTkFrame(embed_frame, fg_color="transparent")
        color_frame.pack(fill="x", padx=15, pady=5)
        
        ctk.CTkLabel(color_frame, text="Embed Rengi:", font=("Arial", 12)).pack(side="left")
        color_entry = ctk.CTkEntry(color_frame, width=100)
        color_entry.pack(side="left", padx=10)
        color_entry.insert(0, self.config["level_system"].get("embed_color", "#00ff00"))

        def save():
            try:
                xp_value = int(msg_xp_entry.get())
                cooldown_value = int(cooldown_entry.get())
                
                if xp_value < 1 or cooldown_value < 0:
                    self.show_notification("Hata", "XP ve bekleme süresi pozitif sayı olmalıdır!")
                    return
                
                self.config["level_system"].update({
                    "xp_per_message": xp_value,
                    "xp_cooldown": cooldown_value,
                    "level_up_channel_id": channel_entry.get(),
                    "level_up_message": message_entry.get("1.0", "end-1c"),
                    "embed_color": color_entry.get()
                })
                
                self.save_config()
                self.show_notification("Başarılı", "Seviye sistemi ayarları kaydedildi!")
            except ValueError:
                self.show_notification("Hata", "XP ve bekleme süresi sayısal olmalıdır!")

        save_btn = ctk.CTkButton(
            self.main_frame,
            text="Ayarları Kaydet",
            command=save,
            width=200,
            height=40,
            corner_radius=8,
            font=("Arial", 14, "bold")
        )
        save_btn.pack(pady=20)

        # Komut listesi
        commands_container = ctk.CTkScrollableFrame(self.main_frame)
        commands_container.pack(fill="both", expand=True, padx=30, pady=(0, 20))

        if not self.config["custom_commands"]:
            ctk.CTkLabel(
                commands_container,
                text="Henüz özel komut eklenmemiş.",
                font=("Arial", 12)
            ).pack(pady=20)

        for cmd in self.config["custom_commands"]:
            cmd_frame = ctk.CTkFrame(commands_container)
            cmd_frame.pack(fill="x", pady=5)

            ctk.CTkLabel(cmd_frame, text=f"!{cmd['name']}", font=("Arial", 14, "bold")).pack(anchor="w", padx=15, pady=5)
            ctk.CTkLabel(cmd_frame, text=cmd["response"]).pack(anchor="w", padx=15)

    def show_reaction_roles(self):
        self.clear_main_frame()
        
        header_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=30, pady=(20, 10))
        
        title = ctk.CTkLabel(header_frame, text="🔔 Reaksiyon Rolleri", font=("Arial", 24, "bold"))
        title.pack(side="left")

        add_btn = ctk.CTkButton(
            header_frame,
            text="+ Yeni Reaksiyon Rolü",
            width=150,
            height=35,
            corner_radius=8
        )
        add_btn.pack(side="right")

        # Rol listesi
        roles_container = ctk.CTkScrollableFrame(self.main_frame)
        roles_container.pack(fill="both", expand=True, padx=30, pady=(0, 20))

        if not self.config["reaction_roles"]:
            ctk.CTkLabel(
                roles_container,
                text="Henüz reaksiyon rolü eklenmemiş.",
                font=("Arial", 12)
            ).pack(pady=20)

        for role in self.config["reaction_roles"]:
            role_frame = ctk.CTkFrame(roles_container)
            role_frame.pack(fill="x", pady=5)

            ctk.CTkLabel(role_frame, text=f"Emoji: {role['emoji']} → Rol: {role['role_name']}", font=("Arial", 12)).pack(padx=15, pady=5)

    def show_notification(self, title, message):
        """Bildirim penceresi gösterir"""
        dialog = ctk.CTkToplevel(self)
        dialog.title(title)
        dialog.geometry("300x150")
        
        ctk.CTkLabel(dialog, text=message, font=("Arial", 12)).pack(pady=20)
        ctk.CTkButton(
            dialog,
            text="Tamam",
            command=dialog.destroy,
            width=100,
            height=35,
            corner_radius=8
        ).pack()

    def start_bot(self):
        """Bot'u başlatır"""
        if not self.config["bot_settings"]["token"]:
            self.show_notification("Hata", "Lütfen önce bot token'ını ayarlayın!")
            return
            
        # Bot başlatma işlemi burada yapılacak
        self.show_notification("Bilgi", "Bot başlatılıyor...")

if __name__ == "__main__":
    app = DiscosoftBotGUI()
    app.mainloop()
