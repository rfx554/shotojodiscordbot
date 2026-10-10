import os
import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import random
import time

# ── Configuration ──────────────────────────────────────────────
OWNER_ID = 1419320803199029402   # secret, invulnérable même aux Sys+

SYS_PLUS_IDS = {
    1419320803199029402,
    1514099294611701842,
}

# ── Stockage en mémoire ────────────────────────────────────────
whitelisted   = {}   # user_id -> ["voicevip", "server", "privilege"]
private_vocs  = {}   # channel_id -> owner_id
pv_access     = {}   # channel_id -> set(user_id)
follow_active = {}   # follower_id -> target_id
laisse_active = {}   # owner_id -> (cible_id, new_nick, old_nick)
wakeup_active = set()
wakeup_cd     = {}   # invoker_id -> last_wakeup_timestamp

# ── Préfixes ───────────────────────────────────────────────────
# Sys+  →  &
# Sys   →  =
async def get_prefix(bot, message):
    return ["&", "="]

# ───────────────────────────────────────────────────────────────
intents = discord.Intents.all()
bot = commands.Bot(command_prefix=get_prefix, intents=intents, help_command=None)
tree = bot.tree

# ── Checks ─────────────────────────────────────────────────────
def is_owner(uid):    return uid == OWNER_ID
def is_sys_plus(uid): return uid in SYS_PLUS_IDS
def is_sys(uid):      return uid in SYS_PLUS_IDS or bool(whitelisted.get(uid))
def has_wl(uid, t):   return uid in SYS_PLUS_IDS or t in whitelisted.get(uid, [])

async def protection_check(ctx, target: discord.Member) -> bool:
    """
    Retourne False et envoie un message si la cible est protégée contre l'auteur.
    - Owner (OWNER_ID) est invulnérable à tout le monde y compris les Sys+
    - Sys+ sont invulnérables aux Sys normaux
    """
    if target.id == OWNER_ID and ctx.author.id != OWNER_ID:
        await ctx.send("J'ai codé ce bot et tu oses me toucher ?")
        return False
    if is_sys_plus(target.id) and not is_sys_plus(ctx.author.id):
        await ctx.send("Plus jamais de ta vie tu touches aux Sys+ !")
        return False
    return True

async def protection_check_interaction(i: discord.Interaction, target: discord.Member) -> bool:
    if target.id == OWNER_ID and i.user.id != OWNER_ID:
        await i.response.send_message("J'ai codé ce bot et tu oses me toucher ?", ephemeral=False)
        return False
    if is_sys_plus(target.id) and not is_sys_plus(i.user.id):
        await i.response.send_message("Plus jamais de ta vie tu touches aux Sys+ !", ephemeral=False)
        return False
    return True

def check_sys_plus():
    async def pred(ctx):
        if not is_sys_plus(ctx.author.id):
            await ctx.send(embed=discord.Embed(description="❌ Réservé aux **Sys+**.", color=0xFF0000))
            return False
        return True
    return commands.check(pred)

def check_voicevip():
    async def pred(ctx):
        if not has_wl(ctx.author.id, "voicevip"):
            await ctx.send(embed=discord.Embed(description="❌ Tu n'as pas la **VoiceVIP**.", color=0xFF0000))
            return False
        return True
    return commands.check(pred)

# ════════════════════════════════════════════════════════════════
#  on_ready
# ════════════════════════════════════════════════════════════════
@bot.event
async def on_ready():
    await tree.sync()
    print(f"✅ {bot.user} connecté (ID: {bot.user.id})")
    await bot.change_presence(activity=discord.Activity(
        type=discord.ActivityType.watching, name="Sys+ | &help"))

# ════════════════════════════════════════════════════════════════
#  VOICE EVENTS
# ════════════════════════════════════════════════════════════════
@bot.event
async def on_voice_state_update(member, before, after):
    # Follow
    for fid, tid in list(follow_active.items()):
        if member.id == tid and after.channel:
            follower = member.guild.get_member(fid)
            if follower and follower.voice and follower.voice.channel != after.channel:
                try: await follower.move_to(after.channel)
                except: pass

    # Voc privée → kick non-autorisés
    if after.channel and after.channel.id in private_vocs:
        cid = after.channel.id
        allowed = pv_access.get(cid, set()) | {private_vocs[cid]}
        if member.id not in allowed and not is_sys_plus(member.id) and member.id != OWNER_ID:
            try:
                await member.move_to(None)
                await member.send(embed=discord.Embed(
                    title="🔒 Vocal privée",
                    description="Cette vocal est privée. Tu as été expulsé.",
                    color=0xFF0000))
            except: pass

    # Owner quitte sa pv → déprivatise
    if before.channel and before.channel.id in private_vocs:
        cid = before.channel.id
        if private_vocs[cid] == member.id:
            private_vocs.pop(cid, None)
            pv_access.pop(cid, None)

# ════════════════════════════════════════════════════════════════
#  &wl — Whitelist panel (Sys+ uniquement, préfixe &)
# ════════════════════════════════════════════════════════════════
class WLView(discord.ui.View):
    def __init__(self, target: discord.Member, invoker_id: int):
        super().__init__(timeout=60)
        self.target = target
        self.invoker_id = invoker_id

    async def interaction_check(self, i: discord.Interaction):
        if i.user.id != self.invoker_id:
            await i.response.send_message("❌ Pas ton panel.", ephemeral=True)
            return False
        return True

    async def give(self, i: discord.Interaction, wl: str, label: str):
        uid = self.target.id
        lst = whitelisted.setdefault(uid, [])
        if wl in lst:
            return await i.response.send_message(f"⚠️ Déjà **{label}**.", ephemeral=True)
        lst.append(wl)
        await i.response.send_message(embed=discord.Embed(
            description=f"✅ {self.target.mention} a reçu la **{label}**.", color=0x00FF7F))
        try:
            await self.target.send(embed=discord.Embed(
                title="🎉 Whitelist reçue !",
                description=f"Tu as reçu la **{label}** sur **{i.guild.name}**.", color=0x5865F2))
        except: pass

    @discord.ui.button(label="🎤 VoiceVIP", style=discord.ButtonStyle.blurple)
    async def voicevip(self, i, b): await self.give(i, "voicevip", "VoiceVIP")

    @discord.ui.button(label="🌐 Server", style=discord.ButtonStyle.green)
    async def server(self, i, b): await self.give(i, "server", "Server")

    @discord.ui.button(label="👑 Privilege", style=discord.ButtonStyle.red)
    async def privilege(self, i, b): await self.give(i, "privilege", "Privilege")

@bot.command(name="wl")
@check_sys_plus()
async def wl_cmd(ctx, member: discord.Member = None):
    if not member:
        return await ctx.send(embed=discord.Embed(description="❌ `&wl @membre`", color=0xFF0000))
    wls = whitelisted.get(member.id, [])
    embed = discord.Embed(title=f"📋 Whitelist — {member.display_name}", color=0x5865F2)
    embed.add_field(name="WL actuelles", value=", ".join(wls) if wls else "Aucune")
    embed.set_thumbnail(url=member.display_avatar.url)
    await ctx.send(embed=embed, view=WLView(member, ctx.author.id))

# ════════════════════════════════════════════════════════════════
#  &voicevip — Panel gestion (Sys+ uniquement, préfixe &)
# ════════════════════════════════════════════════════════════════

# ── Sous-panel : Vocs privées ──────────────────────────────────
class PVSubPanel(discord.ui.View):
    def __init__(self, guild):
        super().__init__(timeout=60)
        self.guild = guild

    @discord.ui.button(label="🔓 Retirer une voc privée", style=discord.ButtonStyle.red)
    async def remove_pv(self, i: discord.Interaction, b):
        if not is_sys_plus(i.user.id):
            return await i.response.send_message("❌ Réservé aux Sys+.", ephemeral=True)
        if not private_vocs:
            return await i.response.send_message("Aucune voc privée active.", ephemeral=True)
        opts = []
        for cid, oid in private_vocs.items():
            ch = self.guild.get_channel(cid)
            ow = self.guild.get_member(oid)
            if ch:
                opts.append(discord.SelectOption(
                    label=f"#{ch.name} — {ow.display_name if ow else oid}", value=str(cid)))
        v = discord.ui.View()
        v.add_item(PVRemoveSelect(opts, self.guild))
        await i.response.send_message("Choisis la voc à déprivatiser :", view=v, ephemeral=True)

    @discord.ui.button(label="📋 Voir toutes les vocs privées", style=discord.ButtonStyle.grey)
    async def list_pv(self, i: discord.Interaction, b):
        if not private_vocs:
            return await i.response.send_message("Aucune voc privée.", ephemeral=True)
        lines = []
        for cid, oid in private_vocs.items():
            ch = self.guild.get_channel(cid)
            ow = self.guild.get_member(oid)
            acc = [self.guild.get_member(uid) for uid in pv_access.get(cid, set())]
            acc_str = ", ".join(m.display_name for m in acc if m) or "Personne"
            lines.append(f"**#{ch.name if ch else cid}** — owner: {ow.display_name if ow else oid} | accès: {acc_str}")
        await i.response.send_message("\n".join(lines), ephemeral=True)

class PVRemoveSelect(discord.ui.Select):
    def __init__(self, opts, guild):
        super().__init__(placeholder="Choisis...", options=opts)
        self.guild = guild
    async def callback(self, i: discord.Interaction):
        cid = int(self.values[0])
        private_vocs.pop(cid, None)
        pv_access.pop(cid, None)
        ch = self.guild.get_channel(cid)
        await i.response.send_message(f"✅ **#{ch.name if ch else cid}** déprivatisée.", ephemeral=True)

# ── Sous-panel : Laisses ───────────────────────────────────────
class LaisseSubPanel(discord.ui.View):
    def __init__(self, guild):
        super().__init__(timeout=60)
        self.guild = guild

    @discord.ui.button(label="🐕 Retirer une laisse", style=discord.ButtonStyle.red)
    async def remove_laisse(self, i: discord.Interaction, b):
        if not is_sys_plus(i.user.id):
            return await i.response.send_message("❌ Réservé aux Sys+.", ephemeral=True)
        if not laisse_active:
            return await i.response.send_message("Aucune laisse active.", ephemeral=True)
        opts = []
        for oid, (cid, new_nick, old_nick) in laisse_active.items():
            ow = self.guild.get_member(oid)
            ci = self.guild.get_member(cid)
            opts.append(discord.SelectOption(
                label=f"{ow.display_name if ow else oid} → {ci.display_name if ci else cid}",
                value=str(oid)))
        v = discord.ui.View()
        v.add_item(LaisseRemoveSelect(opts, self.guild))
        await i.response.send_message("Choisis la laisse à retirer :", view=v, ephemeral=True)

    @discord.ui.button(label="📋 Voir toutes les laisses", style=discord.ButtonStyle.grey)
    async def list_laisse(self, i: discord.Interaction, b):
        if not laisse_active:
            return await i.response.send_message("Aucune laisse active.", ephemeral=True)
        lines = []
        for oid, (cid, new_nick, old_nick) in laisse_active.items():
            ow = self.guild.get_member(oid)
            ci = self.guild.get_member(cid)
            lines.append(f"**{ow.display_name if ow else oid}** → **{ci.display_name if ci else cid}** (pseudo: `{new_nick}`)")
        await i.response.send_message("\n".join(lines), ephemeral=True)

class LaisseRemoveSelect(discord.ui.Select):
    def __init__(self, opts, guild):
        super().__init__(placeholder="Choisis...", options=opts)
        self.guild = guild
    async def callback(self, i: discord.Interaction):
        oid = int(self.values[0])
        entry = laisse_active.pop(oid, None)
        if entry:
            cid, new_nick, old_nick = entry
            m = self.guild.get_member(cid)
            if m:
                try: await m.edit(nick=old_nick)
                except: pass
        await i.response.send_message("✅ Laisse retirée.", ephemeral=True)

# ── Sous-panel : Follows ───────────────────────────────────────
class FollowSubPanel(discord.ui.View):
    def __init__(self, guild):
        super().__init__(timeout=60)
        self.guild = guild

    @discord.ui.button(label="🚫 Retirer un follow", style=discord.ButtonStyle.red)
    async def remove_follow(self, i: discord.Interaction, b):
        if not is_sys_plus(i.user.id):
            return await i.response.send_message("❌ Réservé aux Sys+.", ephemeral=True)
        if not follow_active:
            return await i.response.send_message("Aucun follow actif.", ephemeral=True)
        opts = []
        for fid, tid in follow_active.items():
            f = self.guild.get_member(fid)
            t = self.guild.get_member(tid)
            opts.append(discord.SelectOption(
                label=f"{f.display_name if f else fid} suit {t.display_name if t else tid}",
                value=str(fid)))
        v = discord.ui.View()
        v.add_item(FollowRemoveSelect(opts))
        await i.response.send_message("Choisis le follow à retirer :", view=v, ephemeral=True)

    @discord.ui.button(label="📋 Voir tous les follows", style=discord.ButtonStyle.grey)
    async def list_follow(self, i: discord.Interaction, b):
        if not follow_active:
            return await i.response.send_message("Aucun follow actif.", ephemeral=True)
        lines = []
        for fid, tid in follow_active.items():
            f = self.guild.get_member(fid)
            t = self.guild.get_member(tid)
            lines.append(f"**{f.display_name if f else fid}** suit **{t.display_name if t else tid}**")
        await i.response.send_message("\n".join(lines), ephemeral=True)

class FollowRemoveSelect(discord.ui.Select):
    def __init__(self, opts):
        super().__init__(placeholder="Choisis...", options=opts)
    async def callback(self, i: discord.Interaction):
        follow_active.pop(int(self.values[0]), None)
        await i.response.send_message("✅ Follow retiré.", ephemeral=True)

# ── Sous-panel : WL ───────────────────────────────────────────
class WLSubPanel(discord.ui.View):
    def __init__(self, guild):
        super().__init__(timeout=60)
        self.guild = guild

    @discord.ui.button(label="❌ Retirer une WL", style=discord.ButtonStyle.red)
    async def remove_wl(self, i: discord.Interaction, b):
        if not is_sys_plus(i.user.id):
            return await i.response.send_message("❌ Réservé aux Sys+.", ephemeral=True)
        if not whitelisted:
            return await i.response.send_message("Aucune WL active.", ephemeral=True)
        opts = []
        for uid, wls in whitelisted.items():
            m = self.guild.get_member(uid)
            for wl in wls:
                opts.append(discord.SelectOption(
                    label=f"{m.display_name if m else uid} — {wl}",
                    value=f"{uid}:{wl}"))
        v = discord.ui.View()
        v.add_item(WLRemoveSelect(opts, self.guild))
        await i.response.send_message("Choisis la WL à retirer :", view=v, ephemeral=True)

    @discord.ui.button(label="📋 Voir toutes les WL", style=discord.ButtonStyle.grey)
    async def list_wl(self, i: discord.Interaction, b):
        if not whitelisted:
            return await i.response.send_message("Aucune WL active.", ephemeral=True)
        lines = []
        for uid, wls in whitelisted.items():
            m = self.guild.get_member(uid)
            lines.append(f"**{m.display_name if m else uid}** : {', '.join(wls)}")
        await i.response.send_message("\n".join(lines), ephemeral=True)

class WLRemoveSelect(discord.ui.Select):
    def __init__(self, opts, guild):
        super().__init__(placeholder="Choisis...", options=opts)
        self.guild = guild
    async def callback(self, i: discord.Interaction):
        uid_str, wl = self.values[0].split(":")
        uid = int(uid_str)
        if uid in whitelisted and wl in whitelisted[uid]:
            whitelisted[uid].remove(wl)
            if not whitelisted[uid]:
                del whitelisted[uid]
        m = self.guild.get_member(uid)
        await i.response.send_message(f"✅ WL **{wl}** retirée à **{m.display_name if m else uid}**.", ephemeral=True)

# ── Panel principal &voicevip ──────────────────────────────────
class VoiceVIPMainPanel(discord.ui.View):
    def __init__(self, guild):
        super().__init__(timeout=120)
        self.guild = guild

    @discord.ui.button(label="🔒 Vocs Privées", style=discord.ButtonStyle.blurple)
    async def pv_panel(self, i: discord.Interaction, b):
        if not is_sys_plus(i.user.id): return await i.response.send_message("❌", ephemeral=True)
        embed = discord.Embed(title="🔒 Gestion des Vocs Privées",
            description=f"**{len(private_vocs)}** voc(s) privée(s) active(s).", color=0x5865F2)
        await i.response.send_message(embed=embed, view=PVSubPanel(self.guild), ephemeral=True)

    @discord.ui.button(label="🐕 Laisses", style=discord.ButtonStyle.blurple)
    async def laisse_panel(self, i: discord.Interaction, b):
        if not is_sys_plus(i.user.id): return await i.response.send_message("❌", ephemeral=True)
        embed = discord.Embed(title="🐕 Gestion des Laisses",
            description=f"**{len(laisse_active)}** laisse(s) active(s).", color=0x5865F2)
        await i.response.send_message(embed=embed, view=LaisseSubPanel(self.guild), ephemeral=True)

    @discord.ui.button(label="🏃 Follows", style=discord.ButtonStyle.blurple)
    async def follow_panel(self, i: discord.Interaction, b):
        if not is_sys_plus(i.user.id): return await i.response.send_message("❌", ephemeral=True)
        embed = discord.Embed(title="🏃 Gestion des Follows",
            description=f"**{len(follow_active)}** follow(s) actif(s).", color=0x5865F2)
        await i.response.send_message(embed=embed, view=FollowSubPanel(self.guild), ephemeral=True)

    @discord.ui.button(label="👥 Whitelists", style=discord.ButtonStyle.blurple)
    async def wl_panel(self, i: discord.Interaction, b):
        if not is_sys_plus(i.user.id): return await i.response.send_message("❌", ephemeral=True)
        total = sum(len(v) for v in whitelisted.values())
        embed = discord.Embed(title="👥 Gestion des Whitelists",
            description=f"**{total}** WL active(s).", color=0x5865F2)
        await i.response.send_message(embed=embed, view=WLSubPanel(self.guild), ephemeral=True)

@bot.command(name="voicevip")
@check_sys_plus()
async def voicevip_panel(ctx):
    embed = discord.Embed(title="🎛️ Panel VoiceVIP — Sys+", color=0x5865F2)
    embed.add_field(name="🔒 Vocs privées", value=str(len(private_vocs)), inline=True)
    embed.add_field(name="🐕 Laisses", value=str(len(laisse_active)), inline=True)
    embed.add_field(name="🏃 Follows", value=str(len(follow_active)), inline=True)
    embed.add_field(name="👥 WL", value=str(sum(len(v) for v in whitelisted.values())), inline=True)
    await ctx.send(embed=embed, view=VoiceVIPMainPanel(ctx.guild))

# ════════════════════════════════════════════════════════════════
#  COMMANDES SYS+ (préfixe &)
# ════════════════════════════════════════════════════════════════

@bot.command(name="clear")
@check_sys_plus()
async def clear_cmd(ctx, amount: int = 50):
    if amount < 1 or amount > 500:
        return await ctx.send(embed=discord.Embed(description="❌ Entre 1 et 500.", color=0xFF0000))
    deleted = await ctx.channel.purge(limit=amount + 1)
    msg = await ctx.send(embed=discord.Embed(
        description=f"🗑️ **{len(deleted)-1}** message(s) supprimé(s).", color=0x00FF7F))
    await asyncio.sleep(3)
    await msg.delete()

@bot.command(name="derank")
@check_sys_plus()
async def derank_cmd(ctx, member: discord.Member = None, *, reason: str = "Aucune raison fournie"):
    if not member:
        if ctx.message.reference:
            ref = await ctx.channel.fetch_message(ctx.message.reference.message_id)
            member = ref.author
        else:
            return await ctx.send(embed=discord.Embed(description="❌ `&derank @membre [raison]`", color=0xFF0000))
    if member == ctx.author:
        return await ctx.send(embed=discord.Embed(description="❌ Tu ne peux pas te derank toi-même.", color=0xFF0000))
    if not await protection_check(ctx, member):
        return
    if member.top_role >= ctx.guild.me.top_role:
        return await ctx.send(embed=discord.Embed(description="❌ Rôle trop haut.", color=0xFF0000))
    roles = [r for r in member.roles if r != ctx.guild.default_role and r < ctx.guild.me.top_role]
    if not roles:
        return await ctx.send(embed=discord.Embed(description=f"⚠️ {member.mention} n'a aucun rôle.", color=0xFFA500))
    await member.remove_roles(*roles, reason=f"Derank par {ctx.author} — {reason}")
    embed = discord.Embed(title="🔨 Derank effectué", color=0xFF4500)
    embed.add_field(name="Membre", value=f"{member.mention} (`{member.id}`)", inline=False)
    embed.add_field(name="Rôles retirés", value=str(len(roles)), inline=True)
    embed.add_field(name="Par", value=ctx.author.mention, inline=True)
    embed.add_field(name="Raison", value=reason, inline=False)
    await ctx.send(embed=embed)
    try:
        await member.send(embed=discord.Embed(
            title="⚠️ Derank", description=f"Tous tes rôles ont été retirés sur **{ctx.guild.name}**.\nRaison : {reason}", color=0xFF4500))
    except: pass

# ════════════════════════════════════════════════════════════════
#  COMMANDES VOICEVIP (préfixe =)
#  Sys+ peut AUSSI les utiliser avec =
# ════════════════════════════════════════════════════════════════

@bot.command(name="laisse")
@check_voicevip()
async def laisse_cmd(ctx, member: discord.Member = None):
    if not member:
        return await ctx.send(embed=discord.Embed(description="❌ `=laisse @membre`", color=0xFF0000))

    # Protection invulnérabilité
    if not await protection_check(ctx, member):
        return

    oid = ctx.author.id

    # Toggle : si la laisse existe déjà sur ce membre → on l'enlève
    if oid in laisse_active and laisse_active[oid][0] == member.id:
        _, new_nick, old_nick = laisse_active.pop(oid)
        try: await member.edit(nick=old_nick)
        except: pass
        return await ctx.send(embed=discord.Embed(
            description=f"🔓 Laisse retirée à {member.mention}.", color=0xFFA500))

    # Déjà une laisse active sur quelqu'un d'autre
    if oid in laisse_active:
        return await ctx.send(embed=discord.Embed(
            description="❌ Tu as déjà une laisse active. Refais `=laisse @membre` sur lui pour la retirer d'abord.",
            color=0xFF0000))

    # Vérif : la cible a-t-elle déjà une laisse de quelqu'un d'autre ?
    for owner_id, (cible_id, _, _) in laisse_active.items():
        if cible_id == member.id:
            return await ctx.send("cette personne as déjà la laisse de quelqu'un d'autre sale flocko.")

    old_nick = member.display_name
    new_nick = f"{old_nick}(🐕de {ctx.author.display_name})"
    try:
        await member.edit(nick=new_nick)
    except discord.Forbidden:
        return await ctx.send(embed=discord.Embed(description="❌ Impossible de changer le pseudo.", color=0xFF0000))
    laisse_active[oid] = (member.id, new_nick, old_nick)
    await ctx.send(embed=discord.Embed(
        description=f"🐕 {member.mention} est maintenant sous ta laisse.", color=0x00FF7F))

@bot.command(name="follow")
@check_voicevip()
async def follow_cmd(ctx, member: discord.Member = None):
    if not member:
        return await ctx.send(embed=discord.Embed(description="❌ `=follow @membre`", color=0xFF0000))
    if not await protection_check(ctx, member):
        return
    # Toggle
    if ctx.author.id in follow_active and follow_active[ctx.author.id] == member.id:
        follow_active.pop(ctx.author.id)
        return await ctx.send(embed=discord.Embed(
            description=f"🚫 Follow sur **{member.display_name}** retiré.", color=0xFFA500))
    follow_active[ctx.author.id] = member.id
    await ctx.send(embed=discord.Embed(
        description=f"🏃 Tu suis maintenant **{member.display_name}**.", color=0x00FF7F))

@bot.command(name="pv")
@check_voicevip()
async def pv_cmd(ctx):
    if not ctx.author.voice:
        return await ctx.send(embed=discord.Embed(description="❌ Tu n'es pas dans une vocal.", color=0xFF0000))
    cid = ctx.author.voice.channel.id
    # Toggle : déjà owner de cette voc → on déprivatise
    if cid in private_vocs and private_vocs[cid] == ctx.author.id:
        private_vocs.pop(cid)
        pv_access.pop(cid, None)
        return await ctx.send(embed=discord.Embed(description="🔓 Vocal rendue **publique**.", color=0x00FF7F))
    # Sys+ pas de limite, les autres max 2 pvs
    user_pvs = [c for c, o in private_vocs.items() if o == ctx.author.id]
    max_pvs = 99 if is_sys_plus(ctx.author.id) else 2
    if len(user_pvs) >= max_pvs:
        return await ctx.send(embed=discord.Embed(
            description=f"❌ Tu as déjà **{max_pvs}** vocal(s) privée(s) (maximum). Fais `=pv` dans l'une d'elles pour la désactiver.",
            color=0xFF0000))
    private_vocs[cid] = ctx.author.id
    pv_access[cid] = set()
    await ctx.send(embed=discord.Embed(
        description=f"🔒 **{ctx.author.voice.channel.name}** est maintenant privée.", color=0x5865F2))

@bot.command(name="acces")
@check_voicevip()
async def acces_cmd(ctx, member: discord.Member = None):
    if not member:
        return await ctx.send(embed=discord.Embed(description="❌ `=acces @membre`", color=0xFF0000))
    if not ctx.author.voice:
        return await ctx.send(embed=discord.Embed(description="❌ Tu n'es pas dans une vocal.", color=0xFF0000))
    cid = ctx.author.voice.channel.id
    if cid not in private_vocs or private_vocs[cid] != ctx.author.id:
        return await ctx.send(embed=discord.Embed(description="❌ Cette vocal n'est pas ta vocal privée.", color=0xFF0000))
    pv_access.setdefault(cid, set()).add(member.id)
    await ctx.send(embed=discord.Embed(
        description=f"✅ **{member.display_name}** peut rejoindre ta vocal privée.", color=0x00FF7F))

@bot.command(name="mv")
@check_voicevip()
async def mv_cmd(ctx, member: discord.Member = None, channel: discord.VoiceChannel = None):
    if not member or not channel:
        return await ctx.send(embed=discord.Embed(description="❌ `=mv @membre #vocal`", color=0xFF0000))
    if not await protection_check(ctx, member):
        return
    try:
        await member.move_to(channel)
        await ctx.send(embed=discord.Embed(
            description=f"✅ **{member.display_name}** déplacé dans **{channel.name}**.", color=0x00FF7F))
    except discord.Forbidden:
        await ctx.send(embed=discord.Embed(description="❌ Impossible de déplacer ce membre.", color=0xFF0000))

@bot.command(name="pvlist")
@check_voicevip()
async def pvlist_cmd(ctx):
    if not private_vocs:
        return await ctx.send(embed=discord.Embed(description="Aucune vocal privée active.", color=0xFFA500))
    embed = discord.Embed(title="🔒 Vocaux privés actifs", color=0x5865F2)
    for cid, oid in private_vocs.items():
        ch = ctx.guild.get_channel(cid)
        ow = ctx.guild.get_member(oid)
        acc = [ctx.guild.get_member(u) for u in pv_access.get(cid, set())]
        acc_str = ", ".join(m.display_name for m in acc if m) or "Personne"
        embed.add_field(
            name=f"#{ch.name if ch else cid}",
            value=f"Owner : {ow.mention if ow else oid}\nAccès : {acc_str}", inline=False)
    await ctx.send(embed=embed)

# ════════════════════════════════════════════════════════════════
#  /wakeup — Slash command (VoiceVIP)
# ════════════════════════════════════════════════════════════════
class WakeupModal(discord.ui.Modal, title="Message de wakeup"):
    message = discord.ui.TextInput(
        label="Ton message",
        placeholder="Ex: Réveille toi maintenant !",
        max_length=200)

    def __init__(self, target: discord.Member, invoker: discord.Member):
        super().__init__()
        self.target = target
        self.invoker = invoker

    async def on_submit(self, i: discord.Interaction):
        # Protection invulnérabilité
        if self.target.id == OWNER_ID and i.user.id != OWNER_ID:
            return await i.response.send_message("J'ai codé ce bot et tu oses me toucher ?", ephemeral=False)
        if is_sys_plus(self.target.id) and not is_sys_plus(i.user.id):
            return await i.response.send_message("Plus jamais de ta vie tu touches aux Sys+ !", ephemeral=False)

        now = time.time()
        last = wakeup_cd.get(self.invoker.id, 0)
        # Cooldown uniquement pour les non-Sys+
        if not is_sys_plus(self.invoker.id) and now - last < 300:
            remaining = int(300 - (now - last))
            return await i.response.send_message(
                f"⏳ Cooldown : encore **{remaining}s**.", ephemeral=True)
        if self.target.id in wakeup_active:
            return await i.response.send_message("❌ Ce membre est déjà en wakeup.", ephemeral=True)

        full_msg = f"{self.message.value}\n— c'est {self.invoker.mention} qui te l'ordonne !"
        wakeup_active.add(self.target.id)
        wakeup_cd[self.invoker.id] = now
        await i.response.send_message(
            f"✅ Wakeup lancé sur {self.target.mention} pendant **10 secondes** !", ephemeral=True)

        async def do_wakeup():
            end = asyncio.get_event_loop().time() + 10
            # Spam MP en parallèle
            async def spam():
                for _ in range(20):
                    try: await self.target.send(full_msg)
                    except: pass
                    await asyncio.sleep(0.5)
            asyncio.create_task(spam())
            # Move ultra rapide
            vcs = [ch for ch in i.guild.voice_channels]
            while asyncio.get_event_loop().time() < end:
                if self.target.voice and vcs:
                    try: await self.target.move_to(random.choice(vcs))
                    except: pass
                await asyncio.sleep(0.3)
            try: await self.target.move_to(None)
            except: pass
            wakeup_active.discard(self.target.id)

        asyncio.create_task(do_wakeup())

@tree.command(name="wakeup", description="Wakeup un membre (VoiceVIP)")
@app_commands.describe(membre="Le membre à wakeup")
async def wakeup_slash(i: discord.Interaction, membre: discord.Member):
    if not has_wl(i.user.id, "voicevip"):
        return await i.response.send_message("❌ Tu n'as pas la **VoiceVIP**.", ephemeral=True)
    await i.response.send_modal(WakeupModal(membre, i.user))

# ════════════════════════════════════════════════════════════════
#  &help / =help
# ════════════════════════════════════════════════════════════════
@bot.command(name="help")
async def help_cmd(ctx):
    embed = discord.Embed(title="📖 Commandes", color=0x5865F2)
    if is_sys_plus(ctx.author.id):
        embed.add_field(name="⭐ Sys+ (préfixe &)",
            value="`&wl @m` `&voicevip` `&clear [n]` `&derank @m [raison]`\n*Les Sys+ peuvent aussi utiliser toutes les commandes `=`*",
            inline=False)
    if has_wl(ctx.author.id, "voicevip"):
        embed.add_field(name="🎤 VoiceVIP (préfixe =)",
            value="`=laisse @m` `=follow @m` `=pv` `=acces @m` `=mv @m #voc` `=pvlist` `/wakeup`",
            inline=False)
    if not embed.fields:
        embed.description = "Tu n'as accès à aucune commande."
    embed.set_footer(text="Refais la même commande pour toggle (laisse, follow, pv...)")
    await ctx.send(embed=embed)

# ── Lancement ──────────────────────────────────────────────────
bot.run(os.environ["TOKEN"])
