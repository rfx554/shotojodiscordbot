import os
import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import random

# ── Configuration ──────────────────────────────────────────────
PREFIX = "&"

SYS_PLUS = {
    1419320803199029402,
    1514099294611701842,
}

# ── Stockage en mémoire ────────────────────────────────────────
private_vocs = {}        # channel_id -> owner_id
private_voc_access = {}  # channel_id -> set of user_ids autorisés
follow_active = {}       # follower_id -> target_id
laisse_active = {}       # {user_id: [(cible_id, nouveau_pseudo, ancien_pseudo)]}
wakeup_active = set()    # user_ids en cours de wakeup
wakeup_cooldowns = {}    # user_id -> timestamp dernier wakeup

# ── Whitelist stockage ─────────────────────────────────────────
whitelisted = {}  # user_id -> list of wl types ("voicevip", "server", "privilege")

# ───────────────────────────────────────────────────────────────

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)
tree = bot.tree


# ── Helpers ────────────────────────────────────────────────────
def is_sys_plus_user(user_id):
    return user_id in SYS_PLUS

def is_sys_user(user_id):
    return user_id in whitelisted or user_id in SYS_PLUS

def has_wl(user_id, wl_type):
    return user_id in SYS_PLUS or wl_type in whitelisted.get(user_id, [])

def sys_plus_check():
    async def predicate(ctx):
        if not is_sys_plus_user(ctx.author.id):
            await ctx.send(embed=discord.Embed(
                description="❌ Réservé aux **Sys+**.", color=0xFF0000))
            return False
        return True
    return commands.check(predicate)

def sys_check():
    async def predicate(ctx):
        if not is_sys_user(ctx.author.id):
            await ctx.send(embed=discord.Embed(
                description="❌ Réservé aux **Sys**.", color=0xFF0000))
            return False
        return True
    return commands.check(predicate)

def voicevip_check():
    async def predicate(ctx):
        if not has_wl(ctx.author.id, "voicevip"):
            await ctx.send(embed=discord.Embed(
                description="❌ Tu n'as pas la **VoiceVIP**.", color=0xFF0000))
            return False
        return True
    return commands.check(predicate)


# ── on_ready ───────────────────────────────────────────────────
@bot.event
async def on_ready():
    await tree.sync()
    print(f"✅ Bot connecté : {bot.user} (ID: {bot.user.id})")
    await bot.change_presence(activity=discord.Activity(
        type=discord.ActivityType.watching, name="Sys+ | &help"))


# ════════════════════════════════════════════════════════════════
#  &wl — WHITELIST PANEL (Sys+ uniquement)
# ════════════════════════════════════════════════════════════════

class WLView(discord.ui.View):
    def __init__(self, target: discord.Member, invoker_id: int):
        super().__init__(timeout=60)
        self.target = target
        self.invoker_id = invoker_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.invoker_id:
            await interaction.response.send_message(
                "❌ Seul le Sys+ qui a lancé la commande peut interagir.", ephemeral=True)
            return False
        return True

    async def give_wl(self, interaction: discord.Interaction, wl_type: str, label: str):
        uid = self.target.id
        if uid not in whitelisted:
            whitelisted[uid] = []
        if wl_type in whitelisted[uid]:
            await interaction.response.send_message(
                f"⚠️ {self.target.mention} a déjà la **{label}**.", ephemeral=True)
            return
        whitelisted[uid].append(wl_type)
        embed = discord.Embed(
            title=f"✅ Whitelist accordée",
            description=f"{self.target.mention} a reçu la **{label}**.",
            color=0x00FF7F)
        embed.set_footer(text=f"Par {interaction.user} • {interaction.guild.name}")
        await interaction.response.send_message(embed=embed)
        try:
            dm = discord.Embed(
                title="🎉 Tu as reçu une Whitelist !",
                description=f"Tu as reçu la **{label}** sur **{interaction.guild.name}**.",
                color=0x5865F2)
            await self.target.send(embed=dm)
        except:
            pass

    @discord.ui.button(label="🎤 VoiceVIP", style=discord.ButtonStyle.blurple, custom_id="wl_voicevip")
    async def voicevip(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.give_wl(interaction, "voicevip", "VoiceVIP")

    @discord.ui.button(label="🌐 Server", style=discord.ButtonStyle.green, custom_id="wl_server")
    async def server(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.give_wl(interaction, "server", "Server")

    @discord.ui.button(label="👑 Privilege", style=discord.ButtonStyle.red, custom_id="wl_privilege")
    async def privilege(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.give_wl(interaction, "privilege", "Privilege")


@bot.command(name="wl")
@sys_plus_check()
async def wl_cmd(ctx, member: discord.Member = None):
    if member is None:
        return await ctx.send(embed=discord.Embed(
            description="❌ Utilisation : `&wl @membre`", color=0xFF0000))
    wls = whitelisted.get(member.id, [])
    embed = discord.Embed(
        title=f"📋 Whitelist — {member.display_name}",
        description=f"Choisis la whitelist à accorder à {member.mention}.",
        color=0x5865F2)
    embed.add_field(name="WL actuelles", value=", ".join(wls) if wls else "Aucune", inline=False)
    embed.set_thumbnail(url=member.display_avatar.url)
    await ctx.send(embed=embed, view=WLView(member, ctx.author.id))


# ════════════════════════════════════════════════════════════════
#  &voicevip — PANEL DE GESTION (Sys+ uniquement)
# ════════════════════════════════════════════════════════════════

class VoiceVIPPanel(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=120)

    @discord.ui.button(label="🔒 Supprimer une VocPrivée", style=discord.ButtonStyle.red)
    async def remove_pv(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_sys_plus_user(interaction.user.id):
            return await interaction.response.send_message("❌ Réservé aux Sys+.", ephemeral=True)
        if not private_vocs:
            return await interaction.response.send_message("Aucune voc privée active.", ephemeral=True)
        options = []
        for ch_id, owner_id in list(private_vocs.items()):
            ch = interaction.guild.get_channel(ch_id)
            owner = interaction.guild.get_member(owner_id)
            if ch:
                options.append(discord.SelectOption(
                    label=f"#{ch.name} (owner: {owner.display_name if owner else owner_id})",
                    value=str(ch_id)))
        if not options:
            return await interaction.response.send_message("Aucune voc privée trouvable.", ephemeral=True)
        select = RemovePVSelect(options)
        v = discord.ui.View()
        v.add_item(select)
        await interaction.response.send_message("Choisis la voc à déprivatiser :", view=v, ephemeral=True)

    @discord.ui.button(label="🐕 Supprimer un Laisse", style=discord.ButtonStyle.red)
    async def remove_laisse(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_sys_plus_user(interaction.user.id):
            return await interaction.response.send_message("❌ Réservé aux Sys+.", ephemeral=True)
        if not laisse_active:
            return await interaction.response.send_message("Aucun laisse actif.", ephemeral=True)
        lines = []
        for owner_id, entries in laisse_active.items():
            owner = interaction.guild.get_member(owner_id)
            for (cible_id, new_pseudo, old_pseudo) in entries:
                cible = interaction.guild.get_member(cible_id)
                lines.append(f"**{owner.display_name if owner else owner_id}** → {cible.display_name if cible else cible_id} (pseudo: `{new_pseudo}`)")
        await interaction.response.send_message("**Laisses actifs :**\n" + "\n".join(lines), ephemeral=True)

    @discord.ui.button(label="👥 Voir les WL", style=discord.ButtonStyle.blurple)
    async def see_wl(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_sys_plus_user(interaction.user.id):
            return await interaction.response.send_message("❌ Réservé aux Sys+.", ephemeral=True)
        if not whitelisted:
            return await interaction.response.send_message("Aucune whitelist active.", ephemeral=True)
        lines = []
        for uid, wls in whitelisted.items():
            m = interaction.guild.get_member(uid)
            name = m.display_name if m else str(uid)
            lines.append(f"**{name}** : {', '.join(wls)}")
        await interaction.response.send_message("**Whitelists :**\n" + "\n".join(lines), ephemeral=True)

    @discord.ui.button(label="🏃 Voir les Follow", style=discord.ButtonStyle.grey)
    async def see_follow(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not is_sys_plus_user(interaction.user.id):
            return await interaction.response.send_message("❌ Réservé aux Sys+.", ephemeral=True)
        if not follow_active:
            return await interaction.response.send_message("Aucun follow actif.", ephemeral=True)
        lines = []
        for follower_id, target_id in follow_active.items():
            f = interaction.guild.get_member(follower_id)
            t = interaction.guild.get_member(target_id)
            lines.append(f"**{f.display_name if f else follower_id}** suit **{t.display_name if t else target_id}**")
        await interaction.response.send_message("**Follows actifs :**\n" + "\n".join(lines), ephemeral=True)


class RemovePVSelect(discord.ui.Select):
    def __init__(self, options):
        super().__init__(placeholder="Choisis une voc...", options=options)

    async def callback(self, interaction: discord.Interaction):
        ch_id = int(self.values[0])
        private_vocs.pop(ch_id, None)
        private_voc_access.pop(ch_id, None)
        ch = interaction.guild.get_channel(ch_id)
        await interaction.response.send_message(
            f"✅ Voc **{ch.name if ch else ch_id}** déprivatisée.", ephemeral=True)


@bot.command(name="voicevip")
@sys_plus_check()
async def voicevip_panel(ctx):
    embed = discord.Embed(
        title="🎛️ Panel VoiceVIP — Sys+",
        description="Gère toutes les fonctionnalités VoiceVIP actives.",
        color=0x5865F2)
    embed.add_field(name="🔒 Vocs privées", value=str(len(private_vocs)), inline=True)
    embed.add_field(name="🐕 Laisses", value=str(sum(len(v) for v in laisse_active.values())), inline=True)
    embed.add_field(name="🏃 Follows", value=str(len(follow_active)), inline=True)
    embed.add_field(name="👥 Whitelists", value=str(len(whitelisted)), inline=True)
    await ctx.send(embed=embed, view=VoiceVIPPanel())


# ════════════════════════════════════════════════════════════════
#  =laisse — VOICEVIP
# ════════════════════════════════════════════════════════════════

@bot.command(name="laisse")
@voicevip_check()
async def laisse_cmd(ctx, member: discord.Member = None):
    if member is None:
        return await ctx.send(embed=discord.Embed(
            description="❌ Utilisation : `=laisse @membre`", color=0xFF0000))
    owner_id = ctx.author.id
    entries = laisse_active.get(owner_id, [])
    if len(entries) >= 2:
        return await ctx.send(embed=discord.Embed(
            description="❌ Tu as déjà **2 laisses** actifs (maximum).", color=0xFF0000))
    # Vérif déjà laissé
    if any(e[0] == member.id for e in entries):
        return await ctx.send(embed=discord.Embed(
            description=f"⚠️ {member.mention} est déjà sous laisse.", color=0xFFA500))
    old_pseudo = member.display_name
    new_pseudo = f"{old_pseudo}(🐕de {ctx.author.display_name})"
    try:
        await member.edit(nick=new_pseudo)
    except discord.Forbidden:
        return await ctx.send(embed=discord.Embed(
            description="❌ Impossible de changer le pseudo (permissions insuffisantes).", color=0xFF0000))
    if owner_id not in laisse_active:
        laisse_active[owner_id] = []
    laisse_active[owner_id].append((member.id, new_pseudo, old_pseudo))
    await ctx.send(embed=discord.Embed(
        description=f"🐕 {member.mention} est maintenant sous laisse de {ctx.author.mention}.",
        color=0x00FF7F))


# ════════════════════════════════════════════════════════════════
#  /wakeup — VOICEVIP (slash command)
# ════════════════════════════════════════════════════════════════

class WakeupMessageSelect(discord.ui.Select):
    def __init__(self, target_id: int, invoker: discord.Member):
        self.target_id = target_id
        self.invoker = invoker
        options = [
            discord.SelectOption(label="Réveille toi !", value="Réveille toi !"),
            discord.SelectOption(label="T'es AFK ?", value="T'es AFK ?"),
            discord.SelectOption(label="On t'attend !", value="On t'attend !"),
            discord.SelectOption(label="Urgence !", value="Urgence !"),
            discord.SelectOption(label="Connecte toi vite !", value="Connecte toi vite !"),
        ]
        super().__init__(placeholder="Choisis le message...", options=options)

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.invoker.id:
            return await interaction.response.send_message("❌ Ce n'est pas ton panel.", ephemeral=True)
        msg = self.values[0]
        full_msg = f"{msg}\n— c'est {self.invoker.mention} qui te l'ordonne !"
        target = interaction.guild.get_member(self.target_id)
        if not target:
            return await interaction.response.send_message("❌ Membre introuvable.", ephemeral=True)

        # Cooldown check
        import time
        now = time.time()
        last = wakeup_cooldowns.get(self.invoker.id, 0)
        if now - last < 300:
            remaining = int(300 - (now - last))
            return await interaction.response.send_message(
                f"⏳ Cooldown wakeup : encore **{remaining}s** à attendre.", ephemeral=True)

        if self.target_id in wakeup_active:
            return await interaction.response.send_message("❌ Ce membre est déjà en wakeup.", ephemeral=True)

        wakeup_active.add(self.target_id)
        wakeup_cooldowns[self.invoker.id] = now
        await interaction.response.send_message(
            f"✅ Wakeup lancé sur {target.mention} pendant 30 secondes !", ephemeral=True)

        async def do_wakeup():
            end_time = asyncio.get_event_loop().time() + 30
            # Spam MP en parallèle
            async def spam_dm():
                for _ in range(15):
                    try:
                        await target.send(full_msg)
                    except:
                        pass
                    await asyncio.sleep(2)
            asyncio.create_task(spam_dm())
            # Move aléatoire dans les vocs
            while asyncio.get_event_loop().time() < end_time:
                voice_channels = [ch for ch in interaction.guild.voice_channels if ch.members or True]
                if voice_channels and target.voice:
                    random_vc = random.choice(voice_channels)
                    try:
                        await target.move_to(random_vc)
                    except:
                        pass
                await asyncio.sleep(1.5)
            # Déco finale
            try:
                await target.move_to(None)
            except:
                pass
            wakeup_active.discard(self.target_id)

        asyncio.create_task(do_wakeup())


class WakeupView(discord.ui.View):
    def __init__(self, target_id: int, invoker: discord.Member):
        super().__init__(timeout=60)
        self.add_item(WakeupMessageSelect(target_id, invoker))


@tree.command(name="wakeup", description="Wakeup un membre (VoiceVIP)")
@app_commands.describe(membre="L'ID ou la mention du membre à wakeup")
async def wakeup_slash(interaction: discord.Interaction, membre: discord.Member):
    if not has_wl(interaction.user.id, "voicevip"):
        return await interaction.response.send_message("❌ Tu n'as pas la **VoiceVIP**.", ephemeral=True)
    embed = discord.Embed(
        title="⏰ Wakeup",
        description=f"Choisis le message à envoyer à {membre.mention}.",
        color=0xFF4500)
    await interaction.response.send_message(embed=embed, view=WakeupView(membre.id, interaction.user), ephemeral=True)


# ════════════════════════════════════════════════════════════════
#  =follow — VOICEVIP
# ════════════════════════════════════════════════════════════════

@bot.command(name="follow")
@voicevip_check()
async def follow_cmd(ctx, member: discord.Member = None):
    if member is None:
        return await ctx.send(embed=discord.Embed(
            description="❌ Utilisation : `=follow @membre`", color=0xFF0000))
    if ctx.author.id in follow_active:
        old_target = ctx.guild.get_member(follow_active[ctx.author.id])
        del follow_active[ctx.author.id]
        await ctx.send(embed=discord.Embed(
            description=f"🚫 Follow sur **{old_target.display_name if old_target else '?'}** retiré.", color=0xFFA500))
    follow_active[ctx.author.id] = member.id
    await ctx.send(embed=discord.Embed(
        description=f"🏃 Tu suis maintenant **{member.display_name}** dans toutes ses vocs.",
        color=0x00FF7F))


@bot.event
async def on_voice_state_update(member, before, after):
    # Follow
    for follower_id, target_id in list(follow_active.items()):
        if member.id == target_id and after.channel is not None:
            follower = member.guild.get_member(follower_id)
            if follower and follower.voice:
                try:
                    await follower.move_to(after.channel)
                except:
                    pass

    # Voc privée : kick les non-autorisés
    if after.channel and after.channel.id in private_vocs:
        ch_id = after.channel.id
        owner_id = private_vocs[ch_id]
        allowed = private_voc_access.get(ch_id, set()) | {owner_id}
        if member.id not in allowed and member.id not in SYS_PLUS:
            try:
                await member.move_to(None)
                dm = discord.Embed(
                    title="🔒 Vocal privée",
                    description="Cette vocal est privée. Tu as été expulsé.",
                    color=0xFF0000)
                await member.send(embed=dm)
            except:
                pass

    # Si owner quitte sa voc privée → déprivatiser
    if before.channel and before.channel.id in private_vocs:
        ch_id = before.channel.id
        if private_vocs[ch_id] == member.id:
            del private_vocs[ch_id]
            private_voc_access.pop(ch_id, None)


# ════════════════════════════════════════════════════════════════
#  =pv — VOICEVIP
# ════════════════════════════════════════════════════════════════

@bot.command(name="pv")
@voicevip_check()
async def pv_cmd(ctx):
    if not ctx.author.voice:
        return await ctx.send(embed=discord.Embed(
            description="❌ Tu n'es pas dans une vocal.", color=0xFF0000))
    ch_id = ctx.author.voice.channel.id
    if ch_id in private_vocs:
        # Toggle off
        del private_vocs[ch_id]
        private_voc_access.pop(ch_id, None)
        return await ctx.send(embed=discord.Embed(
            description="🔓 Ta vocal est maintenant **publique**.", color=0x00FF7F))
    # Check 1 pv max par personne
    for cid, oid in private_vocs.items():
        if oid == ctx.author.id:
            return await ctx.send(embed=discord.Embed(
                description="❌ Tu as déjà une vocal privée. Fais `=pv` dedans pour la retirer d'abord.",
                color=0xFF0000))
    private_vocs[ch_id] = ctx.author.id
    private_voc_access[ch_id] = set()
    await ctx.send(embed=discord.Embed(
        description=f"🔒 Ta vocal **{ctx.author.voice.channel.name}** est maintenant **privée**.",
        color=0x5865F2))


# ════════════════════════════════════════════════════════════════
#  =acces — VOICEVIP
# ════════════════════════════════════════════════════════════════

@bot.command(name="acces")
@voicevip_check()
async def acces_cmd(ctx, member: discord.Member = None):
    if member is None:
        return await ctx.send(embed=discord.Embed(
            description="❌ Utilisation : `=acces @membre`", color=0xFF0000))
    if not ctx.author.voice:
        return await ctx.send(embed=discord.Embed(
            description="❌ Tu n'es pas dans une vocal.", color=0xFF0000))
    ch_id = ctx.author.voice.channel.id
    if ch_id not in private_vocs or private_vocs[ch_id] != ctx.author.id:
        return await ctx.send(embed=discord.Embed(
            description="❌ Cette vocal n'est pas ta vocal privée.", color=0xFF0000))
    if ch_id not in private_voc_access:
        private_voc_access[ch_id] = set()
    private_voc_access[ch_id].add(member.id)
    await ctx.send(embed=discord.Embed(
        description=f"✅ **{member.display_name}** peut maintenant rejoindre ta vocal privée.",
        color=0x00FF7F))


# ════════════════════════════════════════════════════════════════
#  =mv — VOICEVIP
# ════════════════════════════════════════════════════════════════

@bot.command(name="mv")
@voicevip_check()
async def mv_cmd(ctx, member: discord.Member = None, channel: discord.VoiceChannel = None):
    if member is None or channel is None:
        return await ctx.send(embed=discord.Embed(
            description="❌ Utilisation : `=mv @membre #vocal`", color=0xFF0000))
    try:
        await member.move_to(channel)
        await ctx.send(embed=discord.Embed(
            description=f"✅ **{member.display_name}** déplacé dans **{channel.name}**.",
            color=0x00FF7F))
    except discord.Forbidden:
        await ctx.send(embed=discord.Embed(
            description="❌ Impossible de déplacer ce membre.", color=0xFF0000))


# ════════════════════════════════════════════════════════════════
#  =pvlist — VOICEVIP
# ════════════════════════════════════════════════════════════════

@bot.command(name="pvlist")
@voicevip_check()
async def pvlist_cmd(ctx):
    if not private_vocs:
        return await ctx.send(embed=discord.Embed(
            description="Aucune vocal privée active.", color=0xFFA500))
    embed = discord.Embed(title="🔒 Vocaux privés actifs", color=0x5865F2)
    for ch_id, owner_id in private_vocs.items():
        ch = ctx.guild.get_channel(ch_id)
        owner = ctx.guild.get_member(owner_id)
        allowed = private_voc_access.get(ch_id, set())
        allowed_names = [ctx.guild.get_member(uid).display_name for uid in allowed if ctx.guild.get_member(uid)]
        embed.add_field(
            name=f"#{ch.name if ch else ch_id}",
            value=f"Owner : {owner.mention if owner else owner_id}\nAccès : {', '.join(allowed_names) if allowed_names else 'Personne'}",
            inline=False)
    await ctx.send(embed=embed)


# ════════════════════════════════════════════════════════════════
#  &clear — SYS+
# ════════════════════════════════════════════════════════════════

@bot.command(name="clear")
@sys_plus_check()
async def clear_cmd(ctx, amount: int = 50):
    if amount < 1 or amount > 500:
        return await ctx.send(embed=discord.Embed(
            description="❌ Entre **1** et **500**.", color=0xFF0000))
    deleted = await ctx.channel.purge(limit=amount + 1)
    confirm = await ctx.send(embed=discord.Embed(
        description=f"🗑️ **{len(deleted)-1}** message(s) supprimé(s).", color=0x00FF7F))
    await asyncio.sleep(3)
    await confirm.delete()


# ════════════════════════════════════════════════════════════════
#  &derank — SYS+
# ════════════════════════════════════════════════════════════════

@bot.command(name="derank")
@sys_plus_check()
async def derank_cmd(ctx, member: discord.Member = None, *, reason: str = "Aucune raison fournie"):
    if member is None:
        if ctx.message.reference:
            ref_msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
            member = ref_msg.author
        else:
            return await ctx.send(embed=discord.Embed(
                description="❌ Mentionne un membre ou réponds à son message.", color=0xFF0000))
    if member == ctx.author:
        return await ctx.send(embed=discord.Embed(
            description="❌ Tu ne peux pas te derank toi-même.", color=0xFF0000))
    if member.top_role >= ctx.guild.me.top_role:
        return await ctx.send(embed=discord.Embed(
            description="❌ Rôle trop haut.", color=0xFF0000))
    roles_to_remove = [r for r in member.roles if r != ctx.guild.default_role and r < ctx.guild.me.top_role]
    if not roles_to_remove:
        return await ctx.send(embed=discord.Embed(
            description=f"⚠️ {member.mention} n'a aucun rôle à retirer.", color=0xFFA500))
    await member.remove_roles(*roles_to_remove, reason=f"Derank par {ctx.author} — {reason}")
    embed = discord.Embed(title="🔨 Derank effectué", color=0xFF4500)
    embed.add_field(name="Membre", value=f"{member.mention} (`{member.id}`)", inline=False)
    embed.add_field(name="Rôles retirés", value=f"`{len(roles_to_remove)}`", inline=True)
    embed.add_field(name="Par", value=ctx.author.mention, inline=True)
    embed.add_field(name="Raison", value=reason, inline=False)
    await ctx.send(embed=embed)
    try:
        dm = discord.Embed(title="⚠️ Vous avez été derank",
            description=f"Tous vos rôles ont été retirés sur **{ctx.guild.name}**.\nRaison : {reason}",
            color=0xFF4500)
        await member.send(embed=dm)
    except:
        pass


# ════════════════════════════════════════════════════════════════
#  &help
# ════════════════════════════════════════════════════════════════

@bot.command(name="help")
async def help_cmd(ctx):
    is_sp = is_sys_plus_user(ctx.author.id)
    is_s = is_sys_user(ctx.author.id)
    embed = discord.Embed(title="📖 Commandes", color=0x5865F2)
    if is_sp:
        embed.add_field(name="⭐ Sys+", value="`&wl @membre` `&voicevip` `&clear [n]` `&derank @membre [raison]`", inline=False)
    if is_s:
        embed.add_field(name="🔵 VoiceVIP", value="`=laisse @membre` `=follow @membre` `=pv` `=acces @membre` `=mv @membre #vocal` `=pvlist` `/wakeup`", inline=False)
    embed.set_footer(text="Sys+ = fondateurs | Sys = whitelistés")
    await ctx.send(embed=embed)


# ── Lancement ──────────────────────────────────────────────────
bot.run(os.environ["TOKEN"])
