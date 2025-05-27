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

# Add log channel setup reminder
setup_msg += "\n\n**Önemli:** Lütfen `/logkanal` komutunu kullanarak log kanalını ayarlayınız!" 