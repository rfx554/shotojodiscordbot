import os
import json
import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import random
import time
from datetime import datetime

# ══════════════════════════════════════════════════════════════════════
#  CONFIGURATION
# ══════════════════════════════════════════════════════════════════════
OWNER_ID = 1419320803199029402

SYS_PLUS_IDS = {
    1419320803199029402,
    1514099294611701842,
}

WL_FILE = "whitelisted.json"

# ── Palette de couleurs centralisée ──────────────────────────────────
C = {
    "ok":       0x57F287,
    "error":    0xED4245,
    "warn":     0xFEE75C,
    "info":     0x5865F2,
    "sys":      0xEB459E,
    "orange":   0xFF6B35,
    "maint":    0xFFA500,
    "dark":     0x2B2D31,
    "purple":   0x9B59B6,
    "teal":     0x1ABC9C,
}

def ts():
    return f"<t:{int(time.time())}:R>"

# ── Helpers embed ─────────────────────────────────────────────────────
def _base(color, title_prefix, title, desc):
    e = discord.Embed(color=color, timestamp=datetime.utcnow())
    if title: e.title = f"{title_prefix}  {title}"
    if desc:  e.description = desc
    return e

def embed_ok(desc=None, title=None):
    return _base(C["ok"],    "✅", title, desc)

def embed_err(desc=None, title=None):
    return _base(C["error"], "❌", title, desc)

def embed_warn(desc=None, title=None):
    return _base(C["warn"],  "⚠️", title, desc)

def embed_info(desc=None, title=None, color=None):
    e = discord.Embed(color=color or C["info"], timestamp=datetime.utcnow())
    if title: e.title = title
    if desc:  e.description = desc
    return e

def embed_sys(desc=None, title=None):
    """Embed rose Sys+ pour actions premium."""
    return _base(C["sys"], "⚡", title, desc)

def set_footer(embed: discord.Embed, user: discord.Member = None):
    txt = "Shotojo  •  " + datetime.utcnow().strftime("%d/%m/%Y %H:%M UTC")
    if user:
        embed.set_footer(
            text=f"{txt}  •  {user.display_name}",
            icon_url=user.display_avatar.url
        )
    else:
        embed.set_footer(text=txt)
    return embed

# ── Chargement WL ─────────────────────────────────────────────────────
def load_wl():
    if os.path.exists(WL_FILE):
        try:
            with open(WL_FILE, "r") as f:
                return {int(k): v for k, v in json.load(f).items()}
        except:
            pass
    return {}

def save_wl():
    with open(WL_FILE, "w") as f:
        json.dump({str(k): v for k, v in whitelisted.items()}, f)

# ══════════════════════════════════════════════════════════════════════
#  STOCKAGE MEMOIRE
# ══════════════════════════════════════════════════════════════════════
whitelisted    = load_wl()
private_vocs   = {}
pv_access      = {}
follow_active  = {}
laisse_active  = {}
dog_active     = {}
menotte_active = {}
wakeup_active  = set()
wakeup_cd      = {}
dog_cd         = {}
menotte_cd     = {}
locked_nicks   = set()
maintenance    = False

# ══════════════════════════════════════════════════════════════════════
#  BOT
# ══════════════════════════════════════════════════════════════════════
async def get_prefix(bot, message):
    return ["&", "="]

intents = discord.Intents.all()
bot  = commands.Bot(command_prefix=get_prefix, intents=intents, help_command=None)
tree = bot.tree

# ══════════════════════════════════════════════════════════════════════
#  HELPERS / CHECKS
# ══════════════════════════════════════════════════════════════════════
def is_owner(uid):     return uid == OWNER_ID
def is_sys_plus(uid):  return uid in SYS_PLUS_IDS
def has_voicevip(uid): return uid in SYS_PLUS_IDS or "voicevip" in whitelisted.get(uid, []) or "sys" in whitelisted.get(uid, [])
def has_server(uid):   return uid in SYS_PLUS_IDS or "server"   in whitelisted.get(uid, [])
def has_wl_sys(uid):   return uid in SYS_PLUS_IDS or "sys"      in whitelisted.get(uid, [])

async def protection_check(ctx, target: discord.Member) -> bool:
    if target.id == OWNER_ID and not is_owner(ctx.author.id):
        await ctx.reply(embed=embed_err("T'as vraiment essayé de me touch ? 💀"))
        return False
    if is_sys_plus(target.id) and not is_sys_plus(ctx.author.id):
        await ctx.reply(embed=embed_err("Les **Sys+** sont intouchables. Oublie ça. 😂"))
        return False
    return True

async def protection_check_i(i: discord.Interaction, target: discord.Member) -> bool:
    if target.id == OWNER_ID and not is_owner(i.user.id):
        await _safe_send(i, embed=embed_err("T'as vraiment essayé de me touch ? 💀"), ephemeral=True)
        return False
    if is_sys_plus(target.id) and not is_sys_plus(i.user.id):
        await _safe_send(i, embed=embed_err("Les **Sys+** sont intouchables. Oublie ça. 😂"), ephemeral=True)
        return False
    return True

# ── Envoi sécurisé (évite "interaction already acknowledged") ─────────
async def _safe_send(i: discord.Interaction, **kwargs):
    """Répond à une interaction en gérant les cas déjà répondus."""
    try:
        if i.response.is_done():
            await i.followup.send(**kwargs)
        else:
            await i.response.send_message(**kwargs)
    except discord.NotFound:
        pass
    except Exception:
        pass

async def _defer(i: discord.Interaction, ephemeral: bool = False):
    """Defer si l'interaction n'a pas encore été traitée."""
    try:
        if not i.response.is_done():
            await i.response.defer(ephemeral=ephemeral)
    except Exception:
        pass

def check_sys_plus():
    async def pred(ctx):
        if not is_sys_plus(ctx.author.id):
            await ctx.reply(embed=embed_err("Commande réservée aux **Sys+**."))
            return False
        return True
    return commands.check(pred)

def check_voicevip():
    async def pred(ctx):
        if maintenance and not is_sys_plus(ctx.author.id):
            await ctx.reply(embed=embed_warn("Le bot est en **maintenance**. Reviens plus tard."))
            return False
        if not has_voicevip(ctx.author.id):
            await ctx.reply(embed=embed_err("Tu n'as pas la **VoiceVIP**."))
            return False
        return True
    return commands.check(pred)

def check_wl_sys():
    async def pred(ctx):
        if maintenance and not is_sys_plus(ctx.author.id):
            await ctx.reply(embed=embed_warn("Le bot est en **maintenance**. Reviens plus tard."))
            return False
        if not has_wl_sys(ctx.author.id):
            await ctx.reply(embed=embed_err("Tu n'as pas la **WL Sys**."))
            return False
        return True
    return commands.check(pred)

# ══════════════════════════════════════════════════════════════════════
#  MIDDLEWARE MAINTENANCE
# ══════════════════════════════════════════════════════════════════════
@bot.before_invoke
async def before_any_command(ctx):
    if ctx.command and ctx.command.name == "maintenance":
        return
    if maintenance and not is_sys_plus(ctx.author.id):
        e = embed_warn(
            title="Maintenance en cours",
            desc="Le bot est temporairement indisponible.\nReviens dans quelques instants !"
        )
        set_footer(e)
        await ctx.reply(embed=e)
        raise commands.CheckFailure("maintenance")

# ══════════════════════════════════════════════════════════════════════
#  EVENTS
# ══════════════════════════════════════════════════════════════════════
@bot.event
async def on_ready():
    await tree.sync()
    print(f"[OK] {bot.user} connecté (ID: {bot.user.id})")
    await bot.change_presence(
        status=discord.Status.online,
        activity=discord.Activity(type=discord.ActivityType.watching, name="Shotojo 🌸 #🇯🇵")
    )

@bot.event
async def on_member_update(before, after):
    if after.id in locked_nicks and after.nick != "S":
        try:
            await after.edit(nick="S")
        except:
            pass

@bot.event
async def on_voice_state_update(member, before, after):
    guild = member.guild

    # Follow
    for fid, tid in list(follow_active.items()):
        if member.id == tid and after.channel and after.channel != before.channel:
            follower = guild.get_member(fid)
            if follower and follower.voice and follower.voice.channel != after.channel:
                try:
                    await follower.move_to(after.channel)
                except:
                    pass

    # Dog
    for oid, (cid, _, _) in list(dog_active.items()):
        if member.id == oid and after.channel and after.channel != before.channel:
            cible = guild.get_member(cid)
            if cible:
                try:
                    await cible.move_to(after.channel)
                except:
                    pass

    # Menotte
    for oid, (cid, ch_id) in list(menotte_active.items()):
        if member.id == cid and before.channel and before.channel.id == ch_id and after.channel != before.channel:
            locked_ch = guild.get_channel(ch_id)
            if locked_ch:
                async def remmenotter(m=member, ch=locked_ch):
                    await asyncio.sleep(0.3)
                    try:
                        await m.move_to(ch)
                    except:
                        pass
                asyncio.create_task(remmenotter())

    # Vocal privée - entrée
    if after.channel and after.channel.id in private_vocs:
        ch_id    = after.channel.id
        pv_info  = private_vocs[ch_id]
        owner_id = pv_info["owner"]
        pv_type  = pv_info["type"]
        allowed  = pv_access.get(ch_id, set()) | {owner_id}

        if member.id in allowed or is_owner(member.id) or is_sys_plus(member.id):
            pass
        elif pv_type == "normal" and has_wl_sys(member.id):
            pass
        else:
            labels = {
                "normal":  "🔒 Vocal privée",
                "sys":     "🔒 Vocal privée Sys",
                "sysplus": "🔒 Vocal privée Sys+",
            }
            try:
                await member.move_to(None)
                e = embed_err(
                    title=labels.get(pv_type, "Vocal privée"),
                    desc="Tu n'as pas accès à ce salon vocal."
                )
                set_footer(e)
                await member.send(embed=e)
            except:
                pass

    # Vocal privée - sortie owner
    if before.channel and before.channel.id in private_vocs:
        ch_id = before.channel.id
        if private_vocs[ch_id]["owner"] == member.id:
            private_vocs.pop(ch_id, None)
            pv_access.pop(ch_id, None)

# ══════════════════════════════════════════════════════════════════════
#  &maintenance
# ══════════════════════════════════════════════════════════════════════
@bot.command(name="maintenance")
@check_sys_plus()
async def maintenance_cmd(ctx):
    global maintenance
    maintenance = not maintenance
    if maintenance:
        await bot.change_presence(
            status=discord.Status.do_not_disturb,
            activity=discord.Game("🔧 Maintenance")
        )
        e = discord.Embed(
            title="🔧  Maintenance activée",
            description=(
                "Toutes les commandes sont **bloquées** pour les non-Sys+.\n"
                "Le bot reviendra bientôt."
            ),
            color=C["maint"],
            timestamp=datetime.utcnow()
        )
        set_footer(e, ctx.author)
        await ctx.reply(embed=e)
    else:
        await bot.change_presence(
            status=discord.Status.online,
            activity=discord.Activity(type=discord.ActivityType.watching, name="Shotojo 🌸 #🇯🇵")
        )
        e = embed_ok(title="Maintenance désactivée", desc="Le bot est de retour, tout est disponible.")
        set_footer(e, ctx.author)
        await ctx.reply(embed=e)

# ══════════════════════════════════════════════════════════════════════
#  &wl - Panel whitelist
# ══════════════════════════════════════════════════════════════════════
WL_LABELS = {
    "voicevip":  ("🎤", "VoiceVIP",  C["purple"]),
    "server":    ("🌐", "Server",    C["teal"]),
    "sys":       ("⚡", "WL Sys",    C["info"]),
    "privilege": ("👑", "Privilege", C["sys"]),
}

class WLView(discord.ui.View):
    def __init__(self, target: discord.Member, invoker_id: int):
        super().__init__(timeout=60)
        self.target     = target
        self.invoker_id = invoker_id

    async def interaction_check(self, i: discord.Interaction):
        if i.user.id != self.invoker_id:
            await _safe_send(i, embed=embed_err("Ce panel ne t'appartient pas."), ephemeral=True)
            return False
        return True

    async def give(self, i: discord.Interaction, wl: str):
        await i.response.defer(ephemeral=True)
        icon, label, color = WL_LABELS[wl]
        lst = whitelisted.setdefault(self.target.id, [])
        if wl in lst:
            return await i.followup.send(
                embed=embed_warn(f"{self.target.mention} a déjà la **{label}**."), ephemeral=True
            )
        lst.append(wl)
        save_wl()
        e = discord.Embed(
            title=f"{icon}  WL attribuée",
            description=f"{self.target.mention} vient de recevoir la **{label}**.",
            color=color, timestamp=datetime.utcnow()
        )
        e.set_thumbnail(url=self.target.display_avatar.url)
        set_footer(e, i.user)
        await i.followup.send(embed=e)
        try:
            dm = discord.Embed(
                title=f"{icon}  Nouvelle whitelist !",
                description=f"Tu as reçu la **{label}** sur **{i.guild.name}**.",
                color=color, timestamp=datetime.utcnow()
            )
            dm.set_thumbnail(url=i.guild.icon.url if i.guild.icon else None)
            set_footer(dm)
            await self.target.send(embed=dm)
        except:
            pass

    @discord.ui.button(label="🎤 VoiceVIP",  style=discord.ButtonStyle.blurple)
    async def voicevip(self,  i, b): await self.give(i, "voicevip")

    @discord.ui.button(label="🌐 Server",    style=discord.ButtonStyle.green)
    async def server(self,    i, b): await self.give(i, "server")

    @discord.ui.button(label="⚡ WL Sys",    style=discord.ButtonStyle.grey)
    async def wl_sys(self,    i, b): await self.give(i, "sys")

    @discord.ui.button(label="👑 Privilege", style=discord.ButtonStyle.red)
    async def privilege(self, i, b): await self.give(i, "privilege")

@bot.command(name="wl")
@check_sys_plus()
async def wl_cmd(ctx, member: discord.Member = None):
    if not member:
        return await ctx.reply(embed=embed_err("Usage : `&wl @membre`"))
    wls = whitelisted.get(member.id, [])
    badges = "  ".join(
        f"{WL_LABELS[w][0]} `{w}`" for w in wls if w in WL_LABELS
    ) if wls else "*Aucune*"
    e = discord.Embed(
        title="📋  Panel Whitelist",
        color=C["dark"],
        timestamp=datetime.utcnow()
    )
    e.set_author(name=member.display_name, icon_url=member.display_avatar.url)
    e.add_field(name="WL actuelles", value=badges, inline=False)
    e.add_field(name="ID", value=f"`{member.id}`", inline=True)
    e.add_field(name="Compte créé", value=f"<t:{int(member.created_at.timestamp())}:R>", inline=True)
    e.set_thumbnail(url=member.display_avatar.url)
    set_footer(e, ctx.author)
    await ctx.reply(embed=e, view=WLView(member, ctx.author.id))

# ══════════════════════════════════════════════════════════════════════
#  SUBPANELS WLPANEL
# ══════════════════════════════════════════════════════════════════════
class PVSubPanel(discord.ui.View):
    def __init__(self, guild):
        super().__init__(timeout=60)
        self.guild = guild

    @discord.ui.button(label="🔓 Déprivatiser", style=discord.ButtonStyle.red)
    async def remove_pv(self, i, b):
        if not private_vocs:
            return await i.response.send_message(embed=embed_warn("Aucune vocal privée active."), ephemeral=True)
        opts = [
            discord.SelectOption(
                label=f"#{self.guild.get_channel(cid).name if self.guild.get_channel(cid) else cid}  [{info['type']}]",
                value=str(cid)
            )
            for cid, info in private_vocs.items()
        ]
        v = discord.ui.View()
        v.add_item(PVRemoveSelect(opts, self.guild))
        await i.response.send_message(embed=embed_info("Choisis la vocal à déprivatiser :"), view=v, ephemeral=True)

    @discord.ui.button(label="📋 Lister", style=discord.ButtonStyle.grey)
    async def list_pv(self, i, b):
        if not private_vocs:
            return await i.response.send_message(embed=embed_warn("Aucune vocal privée active."), ephemeral=True)
        lines = []
        for cid, info in private_vocs.items():
            ch = self.guild.get_channel(cid)
            ow = self.guild.get_member(info["owner"])
            lines.append(
                f"> **#{ch.name if ch else cid}**  `{info['type']}`  •  "
                f"{ow.mention if ow else info['owner']}"
            )
        e = embed_info("\n".join(lines), title=f"🔒 Vocaux privés ({len(private_vocs)})")
        await i.response.send_message(embed=e, ephemeral=True)

class PVRemoveSelect(discord.ui.Select):
    def __init__(self, opts, guild):
        super().__init__(placeholder="Sélectionner...", options=opts)
        self.guild = guild

    async def callback(self, i):
        cid = int(self.values[0])
        private_vocs.pop(cid, None)
        pv_access.pop(cid, None)
        ch = self.guild.get_channel(cid)
        await i.response.send_message(
            embed=embed_ok(f"**#{ch.name if ch else cid}** est maintenant publique."), ephemeral=True
        )

class LaisseSubPanel(discord.ui.View):
    def __init__(self, guild):
        super().__init__(timeout=60)
        self.guild = guild

    @discord.ui.button(label="🔓 Retirer une laisse", style=discord.ButtonStyle.red)
    async def remove(self, i, b):
        if not laisse_active:
            return await i.response.send_message(embed=embed_warn("Aucune laisse active."), ephemeral=True)
        opts = []
        for oid, (cid, _, _) in laisse_active.items():
            ow = self.guild.get_member(oid)
            ci = self.guild.get_member(cid)
            opts.append(discord.SelectOption(
                label=f"{ow.display_name if ow else oid}  →  {ci.display_name if ci else cid}",
                value=str(oid)
            ))
        v = discord.ui.View()
        v.add_item(LaisseRemoveSelect(opts, self.guild))
        await i.response.send_message(embed=embed_info("Choisis la laisse à retirer :"), view=v, ephemeral=True)

    @discord.ui.button(label="📋 Lister", style=discord.ButtonStyle.grey)
    async def list_l(self, i, b):
        if not laisse_active:
            return await i.response.send_message(embed=embed_warn("Aucune laisse active."), ephemeral=True)
        lines = [
            f"> {self.guild.get_member(o).mention if self.guild.get_member(o) else o}  →  "
            f"{self.guild.get_member(c).mention if self.guild.get_member(c) else c}"
            for o, (c, _, _) in laisse_active.items()
        ]
        e = embed_info("\n".join(lines), title=f"🐕 Laisses actives ({len(laisse_active)})")
        await i.response.send_message(embed=e, ephemeral=True)

class LaisseRemoveSelect(discord.ui.Select):
    def __init__(self, opts, guild):
        super().__init__(placeholder="Sélectionner...", options=opts)
        self.guild = guild

    async def callback(self, i):
        oid   = int(self.values[0])
        entry = laisse_active.pop(oid, None)
        if entry:
            m = self.guild.get_member(entry[0])
            if m:
                try:
                    await m.edit(nick=entry[2])
                except:
                    pass
        await i.response.send_message(embed=embed_ok("Laisse retirée avec succès."), ephemeral=True)

class FollowSubPanel(discord.ui.View):
    def __init__(self, guild):
        super().__init__(timeout=60)
        self.guild = guild

    @discord.ui.button(label="🚫 Retirer un follow", style=discord.ButtonStyle.red)
    async def remove(self, i, b):
        if not follow_active:
            return await i.response.send_message(embed=embed_warn("Aucun follow actif."), ephemeral=True)
        opts = []
        for fid, tid in follow_active.items():
            f = self.guild.get_member(fid)
            t = self.guild.get_member(tid)
            opts.append(discord.SelectOption(
                label=f"{f.display_name if f else fid}  suit  {t.display_name if t else tid}",
                value=str(fid)
            ))
        v = discord.ui.View()
        v.add_item(FollowRemoveSelect(opts))
        await i.response.send_message(embed=embed_info("Choisis le follow à retirer :"), view=v, ephemeral=True)

    @discord.ui.button(label="📋 Lister", style=discord.ButtonStyle.grey)
    async def list_f(self, i, b):
        if not follow_active:
            return await i.response.send_message(embed=embed_warn("Aucun follow actif."), ephemeral=True)
        lines = [
            f"> {self.guild.get_member(f).mention if self.guild.get_member(f) else f}  suit  "
            f"{self.guild.get_member(t).mention if self.guild.get_member(t) else t}"
            for f, t in follow_active.items()
        ]
        e = embed_info("\n".join(lines), title=f"🏃 Follows actifs ({len(follow_active)})")
        await i.response.send_message(embed=e, ephemeral=True)

class FollowRemoveSelect(discord.ui.Select):
    def __init__(self, opts):
        super().__init__(placeholder="Sélectionner...", options=opts)

    async def callback(self, i):
        follow_active.pop(int(self.values[0]), None)
        await i.response.send_message(embed=embed_ok("Follow retiré avec succès."), ephemeral=True)

class WLSubPanel(discord.ui.View):
    def __init__(self, guild):
        super().__init__(timeout=60)
        self.guild = guild

    @discord.ui.button(label="❌ Retirer une WL", style=discord.ButtonStyle.red)
    async def remove(self, i, b):
        if not whitelisted:
            return await i.response.send_message(embed=embed_warn("Aucune WL active."), ephemeral=True)
        opts = []
        for uid, wls in whitelisted.items():
            m = self.guild.get_member(uid)
            for wl in wls:
                icon = WL_LABELS.get(wl, ("•", wl, 0))[0]
                opts.append(discord.SelectOption(
                    label=f"{m.display_name if m else uid}  —  {icon} {wl}",
                    value=f"{uid}:{wl}"
                ))
        v = discord.ui.View()
        v.add_item(WLRemoveSelect(opts, self.guild))
        await i.response.send_message(embed=embed_info("Choisis la WL à retirer :"), view=v, ephemeral=True)

    @discord.ui.button(label="📋 Lister", style=discord.ButtonStyle.grey)
    async def list_wl(self, i, b):
        if not whitelisted:
            return await i.response.send_message(embed=embed_warn("Aucune WL active."), ephemeral=True)
        lines = []
        for uid, wls in whitelisted.items():
            m      = self.guild.get_member(uid)
            badges = "  ".join(f"{WL_LABELS.get(w, ('•', w, 0))[0]} `{w}`" for w in wls)
            lines.append(f"> **{m.display_name if m else uid}**  →  {badges}")
        e = embed_info("\n".join(lines), title="👥 Whitelists actives")
        await i.response.send_message(embed=e, ephemeral=True)

class WLRemoveSelect(discord.ui.Select):
    def __init__(self, opts, guild):
        super().__init__(placeholder="Sélectionner...", options=opts)
        self.guild = guild

    async def callback(self, i):
        uid_s, wl = self.values[0].split(":")
        uid = int(uid_s)
        if uid in whitelisted and wl in whitelisted[uid]:
            whitelisted[uid].remove(wl)
            if not whitelisted[uid]:
                del whitelisted[uid]
            save_wl()
        m = self.guild.get_member(uid)
        icon, label, color = WL_LABELS.get(wl, ("•", wl, C["error"]))
        e = embed_ok(f"La **{label}** a été retirée à **{m.display_name if m else uid}**.")
        set_footer(e, i.user)
        await i.response.send_message(embed=e, ephemeral=True)
        if m:
            try:
                dm = discord.Embed(
                    title="🚫  Whitelist retirée",
                    description=f"Ta **{label}** t'a été retirée sur **{i.guild.name}**.",
                    color=C["error"], timestamp=datetime.utcnow()
                )
                dm.set_thumbnail(url=i.guild.icon.url if i.guild.icon else None)
                set_footer(dm)
                await m.send(embed=dm)
            except:
                pass

# ══════════════════════════════════════════════════════════════════════
#  PANEL PRINCIPAL - &wlpanel
# ══════════════════════════════════════════════════════════════════════
class VoiceVIPMainPanel(discord.ui.View):
    def __init__(self, guild):
        super().__init__(timeout=120)
        self.guild = guild

    @discord.ui.button(label="🔒 Vocs Privées", style=discord.ButtonStyle.blurple, row=0)
    async def pv(self, i, b):
        e = embed_info(
            f"**{len(private_vocs)}** vocal(s) privée(s) active(s).",
            title="🔒 Vocaux Privés", color=C["purple"]
        )
        await i.response.send_message(embed=e, view=PVSubPanel(self.guild), ephemeral=True)

    @discord.ui.button(label="🐕 Laisses", style=discord.ButtonStyle.blurple, row=0)
    async def laisse(self, i, b):
        e = embed_info(
            f"**{len(laisse_active)}** laisse(s) active(s).",
            title="🐕 Laisses", color=C["orange"]
        )
        await i.response.send_message(embed=e, view=LaisseSubPanel(self.guild), ephemeral=True)

    @discord.ui.button(label="🏃 Follows", style=discord.ButtonStyle.blurple, row=0)
    async def follow(self, i, b):
        e = embed_info(
            f"**{len(follow_active)}** follow(s) actif(s).",
            title="🏃 Follows", color=C["teal"]
        )
        await i.response.send_message(embed=e, view=FollowSubPanel(self.guild), ephemeral=True)

    @discord.ui.button(label="👥 Whitelists", style=discord.ButtonStyle.blurple, row=0)
    async def wl(self, i, b):
        total = sum(len(v) for v in whitelisted.values())
        e = embed_info(
            f"**{total}** WL active(s) au total.",
            title="👥 Whitelists", color=C["sys"]
        )
        await i.response.send_message(embed=e, view=WLSubPanel(self.guild), ephemeral=True)

def build_wlpanel_embed(guild):
    voicevip_p = set(SYS_PLUS_IDS)
    server_p   = set(SYS_PLUS_IDS)
    sys_p      = set(SYS_PLUS_IDS)
    priv_p     = set()

    for uid, wls in whitelisted.items():
        if "voicevip"  in wls: voicevip_p.add(uid)
        if "server"    in wls: server_p.add(uid)
        if "sys"       in wls: sys_p.add(uid)
        if "privilege" in wls: priv_p.add(uid)

    status_icon = "🔴" if maintenance else "🟢"
    status_txt  = "**EN MAINTENANCE**" if maintenance else "**Opérationnel**"

    e = discord.Embed(
        title="🎛️  Panel de contrôle — Sys+",
        color=C["maint"] if maintenance else C["dark"],
        timestamp=datetime.utcnow()
    )
    e.add_field(name=f"{status_icon} Statut", value=status_txt,              inline=False)
    e.add_field(name="🎤 VoiceVIP",           value=f"`{len(voicevip_p)}` membres", inline=True)
    e.add_field(name="🌐 Server",             value=f"`{len(server_p)}` membres",   inline=True)
    e.add_field(name="⚡ WL Sys",             value=f"`{len(sys_p)}` membres",      inline=True)
    e.add_field(name="👑 Privilege",          value=f"`{len(priv_p)}` membres",     inline=True)
    e.add_field(name="🔒 Vocs priv.",         value=f"`{len(private_vocs)}`",       inline=True)
    e.add_field(name="🐕 Laisses",            value=f"`{len(laisse_active)}`",      inline=True)
    e.add_field(name="🏃 Follows",            value=f"`{len(follow_active)}`",      inline=True)
    e.add_field(name="\u200b",               value="\u200b",                       inline=True)
    set_footer(e)
    return e

@bot.command(name="wlpanel")
@check_sys_plus()
async def wlpanel_cmd(ctx):
    await ctx.reply(embed=build_wlpanel_embed(ctx.guild), view=VoiceVIPMainPanel(ctx.guild))

@bot.command(name="restartpanel")
@check_sys_plus()
async def restartpanel_cmd(ctx):
    e       = build_wlpanel_embed(ctx.guild)
    e.title = "🔄  Panel redémarré"
    await ctx.reply(embed=e, view=VoiceVIPMainPanel(ctx.guild))

# ══════════════════════════════════════════════════════════════════════
#  COMMANDES SYS+ - &clear / &derank
# ══════════════════════════════════════════════════════════════════════
@bot.command(name="clear")
@check_sys_plus()
async def clear_cmd(ctx, amount: int = 50):
    if not 1 <= amount <= 500:
        return await ctx.reply(embed=embed_err("Le montant doit être entre **1** et **500**."))
    deleted = await ctx.channel.purge(limit=amount + 1)
    e = embed_ok(f"**{len(deleted)-1}** message(s) supprimé(s).")
    set_footer(e, ctx.author)
    msg = await ctx.send(embed=e)
    await asyncio.sleep(3)
    await msg.delete()

@bot.command(name="derank")
@check_sys_plus()
async def derank_cmd(ctx, member: discord.Member = None, *, reason: str = "Aucune raison fournie"):
    if not member:
        if ctx.message.reference:
            ref    = await ctx.channel.fetch_message(ctx.message.reference.message_id)
            member = ref.author
        else:
            return await ctx.reply(embed=embed_err("Usage : `&derank @membre [raison]`"))
    if member == ctx.author:
        return await ctx.reply(embed=embed_err("Tu ne peux pas te derank toi-même."))
    if not await protection_check(ctx, member): return
    if member.top_role >= ctx.guild.me.top_role:
        return await ctx.reply(embed=embed_err("Son rôle est trop haut pour moi."))
    roles = [r for r in member.roles if r != ctx.guild.default_role and r < ctx.guild.me.top_role]
    if not roles:
        return await ctx.reply(embed=embed_warn(f"{member.mention} n'a aucun rôle à retirer."))
    await member.remove_roles(*roles, reason=f"Derank par {ctx.author} — {reason}")
    e = discord.Embed(title="🔨  Derank exécuté", color=C["orange"], timestamp=datetime.utcnow())
    e.set_author(name=member.display_name, icon_url=member.display_avatar.url)
    e.add_field(name="Membre", value=member.mention,     inline=True)
    e.add_field(name="Par",    value=ctx.author.mention, inline=True)
    e.add_field(name="Raison", value=f"*{reason}*",      inline=False)
    set_footer(e, ctx.author)
    await ctx.reply(embed=e)
    try:
        dm = discord.Embed(
            title="⚠️  Tu as été derank",
            description=f"Tous tes rôles ont été retirés sur **{ctx.guild.name}**.\n\n> *{reason}*",
            color=C["orange"], timestamp=datetime.utcnow()
        )
        set_footer(dm)
        await member.send(embed=dm)
    except:
        pass

# ══════════════════════════════════════════════════════════════════════
#  /addrole - Ajouter un rôle (Sys+)
# ══════════════════════════════════════════════════════════════════════
@tree.command(name="addrole", description="Ajouter un rôle à un membre ou à tout le serveur (Sys+)")
@app_commands.describe(role="Le rôle à ajouter", tous="Ajouter à tous les membres ?", membre="Le membre cible")
async def addrole_slash(i: discord.Interaction, role: discord.Role, tous: bool, membre: discord.Member = None):
    if not is_sys_plus(i.user.id):
        return await i.response.send_message(embed=embed_err("Commande réservée aux **Sys+**."), ephemeral=True)
    if role >= i.guild.me.top_role:
        return await i.response.send_message(embed=embed_err("Ce rôle est trop haut pour moi."), ephemeral=True)

    if tous:
        await i.response.defer(thinking=True)
        targets = [m for m in i.guild.members if not m.bot and role not in m.roles]
        ok, fail = 0, 0
        for m in targets:
            try:
                await m.add_roles(role, reason=f"/addrole tous — par {i.user}")
                ok += 1
            except:
                fail += 1
        e = discord.Embed(title="✅  Rôle ajouté — Serveur entier", color=C["ok"], timestamp=datetime.utcnow())
        e.add_field(name="Rôle",    value=role.mention, inline=True)
        e.add_field(name="Réussi",  value=f"`{ok}`",    inline=True)
        e.add_field(name="Échec",   value=f"`{fail}`",  inline=True)
        set_footer(e, i.user)
        await i.followup.send(embed=e)
    else:
        if not membre:
            return await i.response.send_message(
                embed=embed_err("Précise un membre ou active **tous**."), ephemeral=True
            )
        if not await protection_check_i(i, membre): return
        if role in membre.roles:
            return await i.response.send_message(
                embed=embed_warn(f"{membre.mention} a déjà ce rôle."), ephemeral=True
            )
        try:
            await membre.add_roles(role, reason=f"/addrole — par {i.user}")
            e = embed_ok(title="Rôle ajouté")
            e.add_field(name="Membre", value=membre.mention, inline=True)
            e.add_field(name="Rôle",   value=role.mention,   inline=True)
            set_footer(e, i.user)
            await i.response.send_message(embed=e)
        except discord.Forbidden:
            await i.response.send_message(embed=embed_err("Impossible d'ajouter ce rôle."), ephemeral=True)

# ══════════════════════════════════════════════════════════════════════
#  /removerole - Retirer un rôle (Sys+)
# ══════════════════════════════════════════════════════════════════════
@tree.command(name="removerole", description="Retirer un rôle à un membre ou à tout le serveur (Sys+)")
@app_commands.describe(role="Le rôle à retirer", tous="Retirer à tous les membres ?", membre="Le membre cible")
async def removerole_slash(i: discord.Interaction, role: discord.Role, tous: bool, membre: discord.Member = None):
    if not is_sys_plus(i.user.id):
        return await i.response.send_message(embed=embed_err("Commande réservée aux **Sys+**."), ephemeral=True)
    if role >= i.guild.me.top_role:
        return await i.response.send_message(embed=embed_err("Ce rôle est trop haut pour moi."), ephemeral=True)

    if tous:
        await i.response.defer(thinking=True)
        targets = [m for m in i.guild.members if not m.bot and role in m.roles]
        ok, fail = 0, 0
        for m in targets:
            try:
                await m.remove_roles(role, reason=f"/removerole tous — par {i.user}")
                ok += 1
            except:
                fail += 1
        e = discord.Embed(title="✅  Rôle retiré — Serveur entier", color=C["orange"], timestamp=datetime.utcnow())
        e.add_field(name="Rôle",   value=role.mention, inline=True)
        e.add_field(name="Réussi", value=f"`{ok}`",    inline=True)
        e.add_field(name="Échec",  value=f"`{fail}`",  inline=True)
        set_footer(e, i.user)
        await i.followup.send(embed=e)
    else:
        if not membre:
            return await i.response.send_message(
                embed=embed_err("Précise un membre ou active **tous**."), ephemeral=True
            )
        if not await protection_check_i(i, membre): return
        if role not in membre.roles:
            return await i.response.send_message(
                embed=embed_warn(f"{membre.mention} n'a pas ce rôle."), ephemeral=True
            )
        try:
            await membre.remove_roles(role, reason=f"/removerole — par {i.user}")
            e = discord.Embed(title="✅  Rôle retiré", color=C["orange"], timestamp=datetime.utcnow())
            e.add_field(name="Membre", value=membre.mention, inline=True)
            e.add_field(name="Rôle",   value=role.mention,   inline=True)
            set_footer(e, i.user)
            await i.response.send_message(embed=e)
        except discord.Forbidden:
            await i.response.send_message(embed=embed_err("Impossible de retirer ce rôle."), ephemeral=True)

# ══════════════════════════════════════════════════════════════════════
#  COMMANDES VOICEVIP (=)
# ══════════════════════════════════════════════════════════════════════
@bot.command(name="laisse")
@check_voicevip()
async def laisse_cmd(ctx, member: discord.Member = None):
    if not member:
        return await ctx.reply(embed=embed_err("Usage : `=laisse @membre`"))
    if not await protection_check(ctx, member): return
    oid = ctx.author.id

    if oid in laisse_active and laisse_active[oid][0] == member.id:
        _, nn, on = laisse_active.pop(oid)
        try:
            await member.edit(nick=on)
        except:
            pass
        e = embed_warn(f"Laisse retirée à {member.mention}.")
        set_footer(e, ctx.author)
        return await ctx.reply(embed=e)

    if oid in laisse_active:
        return await ctx.reply(embed=embed_err("Tu as déjà une laisse active."))
    for o, (cid, _, _) in laisse_active.items():
        if cid == member.id:
            return await ctx.reply(embed=embed_err("Cette personne a déjà la laisse de quelqu'un d'autre."))

    old = member.display_name
    new = f"{old} (🐕 de {ctx.author.display_name})"
    try:
        await member.edit(nick=new)
    except discord.Forbidden:
        return await ctx.reply(embed=embed_err("Impossible de changer son pseudo."))
    laisse_active[oid] = (member.id, new, old)
    e = embed_ok(f"{member.mention} est maintenant sous ta laisse. 🐕")
    set_footer(e, ctx.author)
    await ctx.reply(embed=e)

@bot.command(name="pv")
@check_voicevip()
async def pv_cmd(ctx):
    if not ctx.author.voice:
        return await ctx.reply(embed=embed_err("Tu n'es pas dans une vocal."))
    cid = ctx.author.voice.channel.id

    if cid in private_vocs and private_vocs[cid]["owner"] == ctx.author.id:
        private_vocs.pop(cid)
        pv_access.pop(cid, None)
        e = embed_ok("Vocal rendue **publique**.")
        set_footer(e, ctx.author)
        return await ctx.reply(embed=e)

    user_pvs = [c for c, info in private_vocs.items() if info["owner"] == ctx.author.id]
    max_pvs  = 99 if is_sys_plus(ctx.author.id) else 2
    if len(user_pvs) >= max_pvs:
        return await ctx.reply(embed=embed_err(f"Tu as déjà **{max_pvs}** vocal(s) privée(s) max."))

    pv_type = "sysplus" if is_sys_plus(ctx.author.id) else ("sys" if has_wl_sys(ctx.author.id) else "normal")
    private_vocs[cid] = {"owner": ctx.author.id, "type": pv_type}
    pv_access[cid]    = set()

    labels = {"normal": "normale", "sys": "Sys", "sysplus": "Sys+"}
    e = discord.Embed(
        title=f"🔒  Vocal privée [{labels[pv_type]}]",
        description=f"**{ctx.author.voice.channel.name}** est maintenant privée.",
        color=C["purple"], timestamp=datetime.utcnow()
    )
    set_footer(e, ctx.author)
    await ctx.reply(embed=e)

@bot.command(name="acces")
@check_voicevip()
async def acces_cmd(ctx, member: discord.Member = None):
    if not member:
        return await ctx.reply(embed=embed_err("Usage : `=acces @membre`"))
    if not ctx.author.voice:
        return await ctx.reply(embed=embed_err("Tu n'es pas dans une vocal."))
    cid = ctx.author.voice.channel.id
    if cid not in private_vocs or private_vocs[cid]["owner"] != ctx.author.id:
        return await ctx.reply(embed=embed_err("Ce n'est pas ta vocal privée."))
    acc = pv_access.setdefault(cid, set())
    if member.id in acc:
        acc.discard(member.id)
        e = embed_warn(f"Accès retiré à **{member.display_name}**.")
        set_footer(e, ctx.author)
        return await ctx.reply(embed=e)
    acc.add(member.id)
    e = embed_ok(f"**{member.display_name}** peut maintenant rejoindre ta vocal privée.")
    set_footer(e, ctx.author)
    await ctx.reply(embed=e)

@bot.command(name="join")
@check_voicevip()
async def join_cmd(ctx, member: discord.Member = None):
    if not member:
        return await ctx.reply(embed=embed_err("Usage : `=join @membre`"))
    if not await protection_check(ctx, member): return
    if not member.voice:
        return await ctx.reply(embed=embed_err("Cette personne n'est pas en vocal."))
    if not ctx.author.voice:
        return await ctx.reply(embed=embed_err("Tu n'es pas en vocal."))
    try:
        await ctx.author.move_to(member.voice.channel)
        e = embed_ok(f"Rejoint **{member.voice.channel.name}**.")
        set_footer(e, ctx.author)
        await ctx.reply(embed=e)
    except discord.Forbidden:
        await ctx.reply(embed=embed_err("Impossible de te déplacer."))

@bot.command(name="mv")
@check_voicevip()
async def mv_cmd(ctx, member: discord.Member = None, channel: discord.VoiceChannel = None):
    if not member or not channel:
        return await ctx.reply(embed=embed_err("Usage : `=mv @membre #vocal`"))
    if not await protection_check(ctx, member): return
    try:
        await member.move_to(channel)
        e = embed_ok(f"**{member.display_name}** déplacé dans **{channel.name}**.")
        set_footer(e, ctx.author)
        await ctx.reply(embed=e)
    except discord.Forbidden:
        await ctx.reply(embed=embed_err("Impossible de déplacer ce membre."))

@bot.command(name="pvlist")
@check_voicevip()
async def pvlist_cmd(ctx):
    if not private_vocs:
        return await ctx.reply(embed=embed_warn("Aucune vocal privée active."))
    e = discord.Embed(title="🔒  Vocaux privés actifs", color=C["purple"], timestamp=datetime.utcnow())
    for cid, info in private_vocs.items():
        ch  = ctx.guild.get_channel(cid)
        ow  = ctx.guild.get_member(info["owner"])
        acc = [ctx.guild.get_member(u) for u in pv_access.get(cid, set())]
        acc_str = ", ".join(m.display_name for m in acc if m) or "*Personne*"
        e.add_field(
            name=f"#{ch.name if ch else cid}  [{info['type']}]",
            value=f"Owner : {ow.mention if ow else info['owner']}\nAccès : {acc_str}",
            inline=False
        )
    set_footer(e, ctx.author)
    await ctx.reply(embed=e)

@bot.command(name="menotte")
@check_voicevip()
async def menotte_cmd(ctx, member: discord.Member = None):
    if not member:
        return await ctx.reply(embed=embed_err("Usage : `=menotte @membre`"))
    if not await protection_check(ctx, member): return
    oid = ctx.author.id
    now = time.time()

    if oid in menotte_active and menotte_active[oid][0] == member.id:
        menotte_active.pop(oid)
        e = embed_warn(f"Menotte retirée à {member.mention}.")
        set_footer(e, ctx.author)
        return await ctx.reply(embed=e)
    if oid in menotte_active:
        return await ctx.reply(embed=embed_err("Tu as déjà une menotte active."))
    if not is_sys_plus(oid):
        last = menotte_cd.get(oid, 0)
        if now - last < 120:
            return await ctx.reply(embed=embed_warn(f"Cooldown menotte : encore **{int(120-(now-last))}s**."))
    if not member.voice:
        return await ctx.reply(embed=embed_err("Ce membre n'est pas en vocal."))

    ch_id = member.voice.channel.id
    menotte_active[oid] = (member.id, ch_id)
    menotte_cd[oid]     = now
    e = discord.Embed(
        title="⛓️  Menotte posée",
        description=f"{member.mention} est désormais menotté dans **{member.voice.channel.name}**.",
        color=C["info"], timestamp=datetime.utcnow()
    )
    set_footer(e, ctx.author)
    await ctx.reply(embed=e)

# ══════════════════════════════════════════════════════════════════════
#  COMMANDES WL SYS (=)
# ══════════════════════════════════════════════════════════════════════
@bot.command(name="follow")
@check_wl_sys()
async def follow_cmd(ctx, member: discord.Member = None):
    if not member:
        return await ctx.reply(embed=embed_err("Usage : `=follow @membre`"))
    if not await protection_check(ctx, member): return
    if ctx.author.id in follow_active and follow_active[ctx.author.id] == member.id:
        follow_active.pop(ctx.author.id)
        e = embed_warn(f"Follow sur **{member.display_name}** retiré.")
        set_footer(e, ctx.author)
        return await ctx.reply(embed=e)
    follow_active[ctx.author.id] = member.id
    e = embed_ok(f"Tu suis maintenant **{member.display_name}** en vocal. 🏃")
    set_footer(e, ctx.author)
    await ctx.reply(embed=e)

@bot.command(name="pvsys")
@check_wl_sys()
async def pvsys_cmd(ctx):
    if not ctx.author.voice:
        return await ctx.reply(embed=embed_err("Tu n'es pas dans une vocal."))
    cid = ctx.author.voice.channel.id
    if cid in private_vocs and private_vocs[cid]["owner"] == ctx.author.id:
        private_vocs.pop(cid)
        pv_access.pop(cid, None)
        e = embed_ok("PV Sys désactivée, vocal rendue publique.")
        set_footer(e, ctx.author)
        return await ctx.reply(embed=e)
    user_pvs = [c for c, info in private_vocs.items() if info["owner"] == ctx.author.id]
    if len(user_pvs) >= 2 and not is_sys_plus(ctx.author.id):
        return await ctx.reply(embed=embed_err("Maximum **2** vocaux privés."))
    private_vocs[cid] = {"owner": ctx.author.id, "type": "sys"}
    pv_access[cid]    = set()
    e = discord.Embed(
        title="🔒  Vocal privée Sys",
        description=f"**{ctx.author.voice.channel.name}** est maintenant en PV Sys.",
        color=C["info"], timestamp=datetime.utcnow()
    )
    set_footer(e, ctx.author)
    await ctx.reply(embed=e)

# ══════════════════════════════════════════════════════════════════════
#  COMMANDES SERVER (= et /slash)
# ══════════════════════════════════════════════════════════════════════
@bot.command(name="mp")
async def mp_cmd(ctx, member: discord.Member = None, *, message: str = None):
    if maintenance and not is_sys_plus(ctx.author.id):
        return await ctx.reply(embed=embed_warn("Le bot est en **maintenance**."))
    if not has_server(ctx.author.id):
        return await ctx.reply(embed=embed_err("Tu n'as pas la **Server WL**."))
    if not member or not message:
        return await ctx.reply(embed=embed_err("Usage : `=mp @membre message`"))
    if not await protection_check(ctx, member): return
    try:
        await member.send(message)
        e = embed_ok(f"Message envoyé anonymement à {member.mention}.")
        set_footer(e, ctx.author)
        await ctx.reply(embed=e)
    except discord.Forbidden:
        await ctx.reply(embed=embed_err("Impossible d'envoyer le MP (DMs fermés)."))

@tree.command(name="dog-add", description="Dog quelqu'un — il te suit partout en vocal (Server WL)")
@app_commands.describe(membre="La personne à dog")
async def dog_add(i: discord.Interaction, membre: discord.Member):
    if maintenance and not is_sys_plus(i.user.id):
        return await i.response.send_message(embed=embed_warn("Le bot est en **maintenance**."), ephemeral=True)
    if not has_server(i.user.id):
        return await i.response.send_message(embed=embed_err("Tu n'as pas la **Server WL**."), ephemeral=True)
    if not await protection_check_i(i, membre): return
    oid = i.user.id
    now = time.time()
    if oid in dog_active and dog_active[oid][0] == membre.id:
        return await i.response.send_message(embed=embed_warn("Cette personne est déjà ton dog."), ephemeral=True)
    if oid in dog_active:
        return await i.response.send_message(
            embed=embed_err("Tu as déjà un dog actif. Fais `/dog-del` d'abord."), ephemeral=True
        )
    if not is_sys_plus(oid):
        last = dog_cd.get(oid, 0)
        if now - last < 60:
            return await i.response.send_message(
                embed=embed_warn(f"Cooldown dog : encore **{int(60-(now-last))}s**."), ephemeral=True
            )
    old = membre.display_name
    new = f"{old} (🐕 de {i.user.display_name})"
    try:
        await membre.edit(nick=new)
    except discord.Forbidden:
        return await i.response.send_message(embed=embed_err("Impossible de changer son pseudo."), ephemeral=True)
    dog_active[oid] = (membre.id, new, old)
    dog_cd[oid]     = now
    e = embed_ok(f"**{membre.display_name}** est maintenant ton dog. 🐕")
    set_footer(e, i.user)
    await i.response.send_message(embed=e)

@tree.command(name="dog-del", description="Retirer le dog actif (Server WL)")
async def dog_del(i: discord.Interaction):
    if maintenance and not is_sys_plus(i.user.id):
        return await i.response.send_message(embed=embed_warn("Le bot est en **maintenance**."), ephemeral=True)
    if not has_server(i.user.id):
        return await i.response.send_message(embed=embed_err("Tu n'as pas la **Server WL**."), ephemeral=True)
    if i.user.id not in dog_active:
        return await i.response.send_message(embed=embed_err("Tu n'as pas de dog actif."), ephemeral=True)
    cid, new, old = dog_active.pop(i.user.id)
    m = i.guild.get_member(cid)
    if m:
        try:
            await m.edit(nick=old)
        except:
            pass
    e = embed_warn("Dog retiré avec succès.")
    set_footer(e, i.user)
    await i.response.send_message(embed=e)

# ══════════════════════════════════════════════════════════════════════
#  /wakeup — Version améliorée avec durée custom pour Sys+
# ══════════════════════════════════════════════════════════════════════

# Durées disponibles pour les Sys+ (label affiché → secondes)
WAKEUP_DURATIONS = {
    "10s (défaut)": 10,
    "30s":          30,
    "1 min":        60,
    "2 min":       120,
    "5 min":       300,
}

class WakeupDurationSelect(discord.ui.Select):
    """Sélecteur de durée réservé aux Sys+."""
    def __init__(self, target: discord.Member, invoker: discord.Member, custom_msg: str):
        opts = [
            discord.SelectOption(label=label, value=str(secs), default=(secs == 10))
            for label, secs in WAKEUP_DURATIONS.items()
        ]
        super().__init__(placeholder="Durée du wakeup...", options=opts)
        self.target     = target
        self.invoker    = invoker
        self.custom_msg = custom_msg

    async def callback(self, i: discord.Interaction):
        duration = int(self.values[0])
        await i.response.defer(ephemeral=True)
        await _launch_wakeup(i, self.target, self.invoker, self.custom_msg, duration)

class WakeupDurationView(discord.ui.View):
    def __init__(self, target, invoker, custom_msg):
        super().__init__(timeout=30)
        self.add_item(WakeupDurationSelect(target, invoker, custom_msg))

async def _launch_wakeup(
    i: discord.Interaction,
    target: discord.Member,
    invoker: discord.Member,
    custom_msg: str,
    duration: int
):
    """Lance réellement le wakeup (spam + déplacements)."""
    if target.id in wakeup_active:
        await _safe_send(i, embed=embed_err("Cette personne est déjà en wakeup."), ephemeral=True)
        return

    spam_msg = (
        f"{target.mention} {custom_msg}" if custom_msg
        else f"Réveille-toi {target.mention} ! C'est {invoker.mention} qui te l'ordonne 😈"
    )
    wakeup_active.add(target.id)
    wakeup_cd[invoker.id] = time.time()

    # Confirmation
    e = discord.Embed(
        title="😈  Wakeup lancé !",
        description=(
            f"**Cible :** {target.mention}\n"
            f"**Durée :** `{duration}s`\n"
            f"**Message :** {custom_msg or '*défaut*'}"
        ),
        color=C["orange"], timestamp=datetime.utcnow()
    )
    set_footer(e, invoker)
    await _safe_send(i, embed=e, ephemeral=True)

    async def do_wakeup():
        end      = asyncio.get_event_loop().time() + duration
        vcs      = list(i.guild.voice_channels)
        # Nombre de messages proportionnel à la durée (environ 1/s)
        n_spam   = max(20, duration * 2)
        delay    = max(0.2, duration / n_spam)

        async def spam_task():
            for _ in range(n_spam):
                try:
                    await target.send(spam_msg)
                except:
                    pass
                await asyncio.sleep(delay)

        asyncio.create_task(spam_task())

        while asyncio.get_event_loop().time() < end:
            if target.voice and vcs:
                try:
                    await target.move_to(random.choice(vcs))
                except:
                    pass
            await asyncio.sleep(0.2)          # déplacements toutes les 200 ms

        try:
            await target.move_to(None)
        except:
            pass
        wakeup_active.discard(target.id)

    asyncio.create_task(do_wakeup())


class WakeupModal(discord.ui.Modal, title="Wakeup"):
    message = discord.ui.TextInput(
        label="Message personnalisé (optionnel)",
        placeholder="Laisse vide pour le message par défaut",
        required=False,
        max_length=200
    )

    def __init__(self, target: discord.Member, invoker: discord.Member):
        super().__init__()
        self.target  = target
        self.invoker = invoker

    async def on_submit(self, i: discord.Interaction):
        # Vérifications de sécurité
        if not await protection_check_i(i, self.target):
            return

        now = time.time()
        if not is_sys_plus(self.invoker.id):
            last = wakeup_cd.get(self.invoker.id, 0)
            if now - last < 300:
                return await i.response.send_message(
                    embed=embed_warn(f"Cooldown wakeup : encore **{int(300-(now-last))}s**."),
                    ephemeral=True
                )
        if self.target.id in wakeup_active:
            return await i.response.send_message(
                embed=embed_err("Cette personne est déjà en wakeup."),
                ephemeral=True
            )

        custom = self.message.value.strip()

        # Sys+ → sélecteur de durée
        if is_sys_plus(self.invoker.id):
            e = discord.Embed(
                title="⚡  Wakeup Sys+ — Choisir la durée",
                description=(
                    f"**Cible :** {self.target.mention}\n"
                    f"**Message :** {custom or '*défaut*'}\n\n"
                    "Sélectionne la durée du wakeup ci-dessous."
                ),
                color=C["sys"], timestamp=datetime.utcnow()
            )
            set_footer(e, self.invoker)
            await i.response.send_message(
                embed=e,
                view=WakeupDurationView(self.target, self.invoker, custom),
                ephemeral=True
            )
        else:
            # Utilisateur normal → 10 secondes directement
            await i.response.defer(ephemeral=True)
            await _launch_wakeup(i, self.target, self.invoker, custom, duration=10)


@tree.command(name="wakeup", description="Wakeup un membre — spam intense + déplacements vocaux (Server WL)")
@app_commands.describe(membre="Le membre à wakeup")
async def wakeup_slash(i: discord.Interaction, membre: discord.Member):
    if maintenance and not is_sys_plus(i.user.id):
        return await i.response.send_message(embed=embed_warn("Le bot est en **maintenance**."), ephemeral=True)
    if not has_server(i.user.id):
        return await i.response.send_message(embed=embed_err("Tu n'as pas la **Server WL**."), ephemeral=True)
    await i.response.send_modal(WakeupModal(membre, i.user))


# ══════════════════════════════════════════════════════════════════════
#  /snap — Demande de Snapchat améliorée
# ══════════════════════════════════════════════════════════════════════
class SnapResponseModal(discord.ui.Modal, title="Partager mon Snapchat"):
    snap = discord.ui.TextInput(
        label="Ton Snapchat",
        placeholder="ton_snap_ici",
        max_length=50,
        style=discord.TextStyle.short
    )

    def __init__(self, demandeur: discord.Member):
        super().__init__()
        self.demandeur = demandeur

    async def on_submit(self, i: discord.Interaction):
        e = discord.Embed(
            title="📸  Snap reçu !",
            color=C["warn"],
            timestamp=datetime.utcnow()
        )
        e.add_field(name="De",        value=i.user.mention,      inline=True)
        e.add_field(name="Snapchat",  value=f"`{self.snap.value}`", inline=True)
        e.set_thumbnail(url=i.user.display_avatar.url)
        e.set_footer(text="Shotojo  •  snap partagé en privé")
        try:
            await self.demandeur.send(embed=e)
            await i.response.send_message(
                embed=embed_ok("Ton snap a été envoyé en privé ! ✉️"),
                ephemeral=True
            )
        except Exception:
            await i.response.send_message(
                embed=embed_err("Impossible d'envoyer le snap (DMs fermés)."),
                ephemeral=True
            )

class SnapView(discord.ui.View):
    def __init__(self, demandeur: discord.Member):
        super().__init__(timeout=300)
        self.demandeur = demandeur

    @discord.ui.button(label="📸  Partager mon Snap", style=discord.ButtonStyle.blurple, emoji="📸")
    async def give_snap(self, i: discord.Interaction, b):
        await i.response.send_modal(SnapResponseModal(self.demandeur))

    @discord.ui.button(label="Refuser", style=discord.ButtonStyle.red, emoji="✖️")
    async def refuse_snap(self, i: discord.Interaction, b):
        await i.response.send_message(
            embed=embed_warn("Tu as refusé de partager ton snap."),
            ephemeral=True
        )
        self.stop()

@tree.command(name="snap", description="Demander le snap de quelqu'un (Server WL)")
@app_commands.describe(membre="La personne à qui demander", message="Ton petit message (optionnel)")
async def snap_slash(i: discord.Interaction, membre: discord.Member, message: str = ""):
    if maintenance and not is_sys_plus(i.user.id):
        return await i.response.send_message(embed=embed_warn("Le bot est en **maintenance**."), ephemeral=True)
    if not has_server(i.user.id):
        return await i.response.send_message(embed=embed_err("Tu n'as pas la **Server WL**."), ephemeral=True)

    # Embed envoyé à la cible
    e = discord.Embed(
        title="📸  Quelqu'un veut ton Snap !",
        color=C["warn"],
        timestamp=datetime.utcnow()
    )
    e.set_author(name=i.user.display_name, icon_url=i.user.display_avatar.url)
    e.set_thumbnail(url=i.user.display_avatar.url)
    if message:
        e.add_field(name="💬 Message", value=f"*{message}*", inline=False)
    e.add_field(
        name="Comment répondre ?",
        value="Clique sur **📸 Partager mon Snap** si tu veux le donner.\nSinon, ignore ou refuse.",
        inline=False
    )
    set_footer(e)

    try:
        await membre.send(embed=e, view=SnapView(i.user))
        # Confirmation à l'invocateur
        conf = discord.Embed(
            title="✅  Demande envoyée",
            description=f"Ta demande de snap a été envoyée à {membre.mention}.",
            color=C["ok"], timestamp=datetime.utcnow()
        )
        set_footer(conf, i.user)
        await i.response.send_message(embed=conf, ephemeral=True)
    except Exception:
        await i.response.send_message(
            embed=embed_err("Impossible d'envoyer le MP (DMs fermés)."),
            ephemeral=True
        )

# ══════════════════════════════════════════════════════════════════════
#  /tipeu — Rename + verrouillage pseudo
# ══════════════════════════════════════════════════════════════════════
@tree.command(name="tipeu", description="Rename en S et verrouille le pseudo (Server WL)")
@app_commands.describe(membre="La cible")
async def tipeu_slash(i: discord.Interaction, membre: discord.Member):
    if maintenance and not is_sys_plus(i.user.id):
        return await i.response.send_message(embed=embed_warn("Le bot est en **maintenance**."), ephemeral=True)
    if not has_server(i.user.id):
        return await i.response.send_message(embed=embed_err("Tu n'as pas la **Server WL**."), ephemeral=True)
    if not await protection_check_i(i, membre): return

    if membre.id in locked_nicks:
        locked_nicks.discard(membre.id)
        try:
            await membre.edit(nick=None)
        except:
            pass
        e = embed_warn(f"Pseudo de {membre.mention} déverrouillé.")
        set_footer(e, i.user)
        return await i.response.send_message(embed=e)

    try:
        await membre.edit(nick="S")
        locked_nicks.add(membre.id)
        e = discord.Embed(
            title="🔒  Pseudo verrouillé",
            description=(
                f"{membre.mention} a été renommé **S** et son pseudo est désormais verrouillé.\n"
                f"Refais `/tipeu` sur lui pour le déverrouiller."
            ),
            color=C["info"], timestamp=datetime.utcnow()
        )
        set_footer(e, i.user)
        await i.response.send_message(embed=e)
    except discord.Forbidden:
        await i.response.send_message(embed=embed_err("Impossible de changer son pseudo."), ephemeral=True)

# ══════════════════════════════════════════════════════════════════════
#  &help / =help
# ══════════════════════════════════════════════════════════════════════
@bot.command(name="help")
async def help_cmd(ctx):
    e = discord.Embed(
        title="📖  Commandes disponibles",
        color=C["dark"],
        timestamp=datetime.utcnow()
    )
    if maintenance:
        e.description = "> 🔴 **Maintenance active.** Seuls les Sys+ ont accès aux commandes."

    if is_sys_plus(ctx.author.id):
        e.add_field(
            name="⭐  Sys+  [ & ]",
            value=(
                "`&wl`  `&wlpanel`  `&restartpanel`  `&maintenance`  `&clear`  `&derank`\n"
                "`/addrole`  `/removerole`\n"
                "*+ toutes les commandes = et /*"
            ),
            inline=False
        )
    if has_voicevip(ctx.author.id):
        e.add_field(
            name="🎤  VoiceVIP  [ = ]",
            value="`=laisse`  `=pv`  `=acces`  `=join`  `=mv`  `=pvlist`  `=menotte`",
            inline=False
        )
    if has_wl_sys(ctx.author.id):
        e.add_field(
            name="⚡  WL Sys  [ = ]",
            value="`=follow`  `=pvsys`  *(+ toutes les commandes VoiceVIP)*",
            inline=False
        )
    if has_server(ctx.author.id):
        e.add_field(
            name="🌐  Server  [ = / ]",
            value="`=mp`  `/dog-add`  `/dog-del`  `/wakeup`  `/snap`  `/tipeu`",
            inline=False
        )
    if not e.fields:
        e.description = "> Tu n'as accès à aucune commande."

    e.set_thumbnail(url=ctx.guild.icon.url if ctx.guild.icon else None)
    set_footer(e, ctx.author)
    await ctx.reply(embed=e)

# ══════════════════════════════════════════════════════════════════════
#  LANCEMENT
# ══════════════════════════════════════════════════════════════════════
bot.run(os.environ["TOKEN"])
