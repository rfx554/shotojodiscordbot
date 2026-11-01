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

WL_FILE        = "whitelisted.json"
LOG_CHANNEL_ID = 1558616294788698293
CIVIL_ROLE_ID  = 1564722577060929546   # rôle "civil" à verrouiller comme @everyone

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
    "log":      0x36393F,
}

# ══════════════════════════════════════════════════════════════════════
#  EMBED HELPERS
# ══════════════════════════════════════════════════════════════════════
def ts():
    return f"<t:{int(time.time())}:R>"

def embed_ok(desc=None, title=None):
    e = discord.Embed(color=C["ok"], timestamp=datetime.utcnow())
    if title: e.title = f"✅  {title}"
    if desc:  e.description = desc
    return e

def embed_err(desc=None, title=None):
    e = discord.Embed(color=C["error"], timestamp=datetime.utcnow())
    if title: e.title = f"❌  {title}"
    if desc:  e.description = desc
    return e

def embed_warn(desc=None, title=None):
    e = discord.Embed(color=C["warn"], timestamp=datetime.utcnow())
    if title: e.title = f"⚠️  {title}"
    if desc:  e.description = desc
    return e

def embed_info(desc=None, title=None, color=None):
    e = discord.Embed(color=color or C["info"], timestamp=datetime.utcnow())
    if title: e.title = title
    if desc:  e.description = desc
    return e

def set_footer(embed: discord.Embed, user: discord.Member = None):
    txt = "Shotojo  •  " + datetime.utcnow().strftime("%d/%m/%Y %H:%M")
    if user:
        embed.set_footer(text=f"{txt}  •  par {user.display_name}", icon_url=user.display_avatar.url)
    else:
        embed.set_footer(text=txt)
    return embed

def load_wl():
    if os.path.exists(WL_FILE):
        try:
            with open(WL_FILE, "r") as f:
                return {int(k): v for k, v in json.load(f).items()}
        except: pass
    return {}

def save_wl():
    with open(WL_FILE, "w") as f:
        json.dump({str(k): v for k, v in whitelisted.items()}, f)

# ══════════════════════════════════════════════════════════════════════
#  SYSTÈME DE LOGS
# ══════════════════════════════════════════════════════════════════════
LOG_COLORS = {
    "snap":        0xFEE75C,
    "snap_give":   0x57F287,
    "snap_refuse": 0xED4245,
    "laisse":      0xFF6B35,
    "dog":         0xFF6B35,
    "wakeup":      0xEB459E,
    "follow":      0x1ABC9C,
    "pv":          0x9B59B6,
    "menotte":     0x5865F2,
    "mp":          0x36393F,
    "tipeu":       0x5865F2,
    "wl":          0xEB459E,
    "derank":      0xFF6B35,
    "clear":       0xED4245,
    "lock":        0xFFA500,
    "renew":       0xFFA500,
    "maintenance": 0xFFA500,
    "addrole":     0x57F287,
    "removerole":  0xED4245,
    "acces":       0x9B59B6,
    "join":        0x1ABC9C,
    "mv":          0x1ABC9C,
    "pvsys":       0x5865F2,
    "dmall":       0x5865F2,
    "default":     0x36393F,
}

LOG_ICONS = {
    "snap":        "📸",
    "snap_give":   "📸✅",
    "snap_refuse": "📸❌",
    "laisse":      "🐕",
    "dog":         "🐕",
    "wakeup":      "😈",
    "follow":      "🏃",
    "pv":          "🔒",
    "menotte":     "⛓️",
    "mp":          "✉️",
    "tipeu":       "🔒",
    "wl":          "👥",
    "derank":      "🔨",
    "clear":       "🗑️",
    "lock":        "🔒",
    "renew":       "🔄",
    "maintenance": "🔧",
    "addrole":     "✅",
    "removerole":  "❌",
    "acces":       "🔑",
    "join":        "📞",
    "mv":          "↗️",
    "pvsys":       "🔒",
    "dmall":       "📨",
    "default":     "📋",
}

async def send_log(
    guild: discord.Guild,
    author: discord.Member,
    action_key: str,
    title: str,
    fields: list,
    target: discord.Member = None,
    extra_desc: str = None,
):
    if not LOG_CHANNEL_ID:
        return
    ch = guild.get_channel(LOG_CHANNEL_ID)
    if not ch:
        return

    icon  = LOG_ICONS.get(action_key, LOG_ICONS["default"])
    color = LOG_COLORS.get(action_key, LOG_COLORS["default"])
    now   = datetime.utcnow()

    e = discord.Embed(
        title=f"{icon}  {title}",
        color=color,
        timestamp=now,
    )

    e.set_author(
        name=f"{author.display_name}  •  {author.name}",
        icon_url=author.display_avatar.url,
    )
    e.set_thumbnail(url=author.display_avatar.url)

    e.add_field(name="👤 Exécuté par",  value=f"{author.mention}\n`{author.id}`", inline=True)
    e.add_field(name="🕐 Timestamp",    value=f"<t:{int(now.timestamp())}:F>\n<t:{int(now.timestamp())}:R>", inline=True)

    if target:
        e.add_field(name="🎯 Cible",    value=f"{target.mention}\n`{target.id}`", inline=True)
        e.set_image(url=target.display_avatar.url)

    if fields:
        e.add_field(name="\u200b", value="\u200b", inline=False)

    for f in fields:
        name, value = f[0], f[1]
        inline = f[2] if len(f) > 2 else True
        e.add_field(name=name, value=str(value), inline=inline)

    if extra_desc:
        e.add_field(name="\u200b", value=extra_desc, inline=False)

    e.set_footer(
        text=f"Shotojo Logs  •  ID auteur : {author.id}",
        icon_url=guild.icon.url if guild.icon else None,
    )

    try:
        await ch.send(embed=e)
    except Exception:
        pass

# ══════════════════════════════════════════════════════════════════════
#  STOCKAGE MEMOIRE
# ══════════════════════════════════════════════════════════════════════
whitelisted     = load_wl()
private_vocs    = {}
pv_access       = {}
pv_violations   = {}   # member_id -> count (nombre de tentatives d'intrusion en PV)
follow_active   = {}
laisse_active   = {}
dog_active      = {}
menotte_active  = {}
wakeup_active   = set()
wakeup_cd       = {}
dog_cd          = {}
menotte_cd      = {}
locked_nicks    = set()
locked_channels = {}
maintenance     = False
snipe_cache     = {}   # channel_id -> {"content", "author", "author_icon", "deleted_at"}

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
        await ctx.reply(embed=embed_err("🫵💀 Frérot, j'ai crée le bot et t'essayes de me toucher ? La prochaine c TO 24h, tu feras un ticket pour te faire unto. 🎟️"))
        return False
    if is_sys_plus(target.id) and not is_sys_plus(ctx.author.id):
        await ctx.reply(embed=embed_err("🚫⚡ N'essaye plus jamais de toucher un Sys+ ! 😤"))
        return False
    return True

async def protection_check_i(i: discord.Interaction, target: discord.Member) -> bool:
    if target.id == OWNER_ID and not is_owner(i.user.id):
        await i.channel.send(embed=embed_err(f"🫵💀 {i.user.mention} Frérot, j'ai crée le bot et t'essayes de me toucher ? La prochaine c TO 24h, tu feras un ticket pour te faire unto. 🎟️"))
        return False
    if is_sys_plus(target.id) and not is_sys_plus(i.user.id):
        await i.channel.send(embed=embed_err(f"🚫⚡ {i.user.mention} N'essaye plus jamais de toucher un Sys+ ! 😤"))
        return False
    return True

def check_sys_plus():
    async def pred(ctx):
        if not is_sys_plus(ctx.author.id):
            # silencieux : on ne réagit pas
            return False
        return True
    return commands.check(pred)

def check_server():
    async def pred(ctx):
        if maintenance and not is_sys_plus(ctx.author.id):
            await ctx.reply(embed=embed_warn("Le bot est en **maintenance**. Reviens plus tard."))
            return False
        if not has_server(ctx.author.id):
            # silencieux : on ne réagit pas
            return False
        return True
    return commands.check(pred)

def check_voicevip():
    async def pred(ctx):
        if maintenance and not is_sys_plus(ctx.author.id):
            await ctx.reply(embed=embed_warn("Le bot est en **maintenance**. Reviens plus tard."))
            return False
        if not has_voicevip(ctx.author.id):
            # silencieux : on ne réagit pas
            return False
        return True
    return commands.check(pred)

def check_wl_sys():
    async def pred(ctx):
        if maintenance and not is_sys_plus(ctx.author.id):
            await ctx.reply(embed=embed_warn("Le bot est en **maintenance**. Reviens plus tard."))
            return False
        if not has_wl_sys(ctx.author.id):
            # silencieux : on ne réagit pas
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
        e = embed_warn(title="Maintenance en cours", desc="Le bot est temporairement indisponible.\nReviens dans quelques instants !")
        set_footer(e)
        await ctx.reply(embed=e)
        raise commands.CheckFailure("maintenance")

# ══════════════════════════════════════════════════════════════════════
#  EVENTS
# ══════════════════════════════════════════════════════════════════════
@bot.event
async def on_ready():
    await tree.sync()
    print(f"[OK] {bot.user} connecte (ID: {bot.user.id})")
    await bot.change_presence(
        status=discord.Status.online,
        activity=discord.Activity(type=discord.ActivityType.watching, name="Shotojo 🌸 #🇯🇵")
    )

@bot.event
async def on_message_delete(message):
    if message.author.bot or not message.content:
        return
    if message.content.strip().lower().startswith("=snipe"):
        return
    snipe_cache[message.channel.id] = {
        "content":     message.content,
        "author":      str(message.author),
        "author_icon": message.author.display_avatar.url,
        "deleted_at":  datetime.utcnow(),
    }

@bot.event
async def on_member_update(before, after):
    if after.id in locked_nicks and after.nick != "S":
        try: await after.edit(nick="S")
        except: pass

@bot.event
async def on_voice_state_update(member, before, after):
    guild = member.guild

    # ── Follow ──
    for fid, tid in list(follow_active.items()):
        if member.id == tid and after.channel and after.channel != before.channel:
            follower = guild.get_member(fid)
            if follower and follower.voice and follower.voice.channel != after.channel:
                try: await follower.move_to(after.channel)
                except: pass

    # ── Dog ──
    for oid, (cid, _, _) in list(dog_active.items()):
        if member.id == oid and after.channel and after.channel != before.channel:
            cible = guild.get_member(cid)
            if cible:
                try: await cible.move_to(after.channel)
                except: pass

    # ── Menotte ──
    for oid, (cid, ch_id) in list(menotte_active.items()):
        if member.id == cid and before.channel and before.channel.id == ch_id and after.channel != before.channel:
            locked_ch = guild.get_channel(ch_id)
            if locked_ch:
                async def remmenotter(m=member, ch=locked_ch):
                    await asyncio.sleep(0.3)
                    try: await m.move_to(ch)
                    except: pass
                asyncio.create_task(remmenotter())

    # ── Vocal privée : intrusion ──
    if after.channel and after.channel.id in private_vocs:
        ch_id    = after.channel.id
        pv_info  = private_vocs[ch_id]
        owner_id = pv_info["owner"]
        pv_type  = pv_info["type"]
        allowed  = pv_access.get(ch_id, set()) | {owner_id}

        authorized = (
            member.id in allowed
            or is_owner(member.id)
            or is_sys_plus(member.id)
            or (pv_type == "normal" and has_wl_sys(member.id))
        )

        if not authorized:
            labels = {"normal": "🔒 Vocal privée", "sys": "🔒 Vocal privée Sys", "sysplus": "🔒 Vocal privée Sys+"}

            # Compter les violations
            count = pv_violations.get(member.id, 0) + 1
            pv_violations[member.id] = count

            # Éjecter
            try:
                await member.move_to(None)
            except: pass

            if count == 1:
                # 1ère fois : éjection + DM
                try:
                    e = embed_err(title=labels.get(pv_type, "Vocal privée"), desc="Tu n'as pas accès à ce salon vocal.")
                    set_footer(e)
                    await member.send(embed=e)
                except: pass
            else:
                # 2ème fois et + : timeout progressif
                timeout_minutes = min(count - 1, 60)  # 1 min, 2 min, ... max 60 min
                timeout_seconds = timeout_minutes * 60
                try:
                    until = discord.utils.utcnow() + discord.timedelta(seconds=timeout_seconds)
                    await member.timeout(until, reason=f"Tentative d'intrusion dans une vocal privée (x{count})")
                    try:
                        e = embed_err(
                            title="⛔ Timeout",
                            desc=f"Tu as reçu un timeout de **{timeout_minutes} minute(s)** pour avoir tenté d'entrer dans une vocal privée (tentative n°{count})."
                        )
                        set_footer(e)
                        await member.send(embed=e)
                    except: pass
                except: pass

    # ── Nettoyage PV si owner quitte ──
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
        await bot.change_presence(status=discord.Status.do_not_disturb, activity=discord.Game("🔧 Maintenance en cours"))
        e = discord.Embed(title="🔧  Maintenance activée", description="Toutes les commandes sont **bloquées** pour les non-Sys+.\nLe bot reviendra bientôt.", color=C["maint"], timestamp=datetime.utcnow())
        set_footer(e, ctx.author)
        await ctx.reply(embed=e)
    else:
        await bot.change_presence(status=discord.Status.online, activity=discord.Activity(type=discord.ActivityType.watching, name="Shotojo 🌸 #🇯🇵"))
        e = embed_ok(title="Maintenance désactivée", desc="Le bot est de retour, tout est disponible.")
        set_footer(e, ctx.author)
        await ctx.reply(embed=e)
    asyncio.create_task(send_log(
        ctx.guild, ctx.author, "maintenance",
        f"Maintenance {'activée' if maintenance else 'désactivée'}",
        [
            ("⌨️ Commande", "`&maintenance`"),
            ("🔧 Statut", "🔴 EN MAINTENANCE" if maintenance else "🟢 Opérationnel"),
        ],
    ))

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
    def __init__(self, target: discord.Member, invoker: discord.Member):
        super().__init__(timeout=60)
        self.target  = target
        self.invoker = invoker

    async def interaction_check(self, i: discord.Interaction):
        if i.user.id != self.invoker.id:
            await i.response.send_message(embed=embed_err("Ce panel ne t'appartient pas."), ephemeral=True)
            return False
        return True

    async def give(self, i: discord.Interaction, wl: str):
        icon, label, color = WL_LABELS[wl]
        lst = whitelisted.setdefault(self.target.id, [])
        if wl in lst:
            return await i.response.send_message(embed=embed_warn(f"{self.target.mention} a déjà la **{label}**."), ephemeral=True)
        lst.append(wl)
        save_wl()
        e = discord.Embed(title=f"{icon}  WL attribuée", description=f"{self.target.mention} vient de recevoir la **{label}**.", color=color, timestamp=datetime.utcnow())
        e.set_thumbnail(url=self.target.display_avatar.url)
        set_footer(e, i.user)
        await i.response.send_message(embed=e)
        asyncio.create_task(send_log(
            i.guild, self.invoker, "wl",
            f"WL attribuée — {label}",
            [
                ("⌨️ Commande", "`&wl`"),
                ("🏷️ WL",    f"`{wl}`  {icon}"),
                ("📋 Label",  label),
            ],
            target=self.target,
        ))
        try:
            dm = discord.Embed(title=f"{icon}  Nouvelle whitelist !", description=f"Tu as reçu la **{label}** sur **{i.guild.name}**.", color=color, timestamp=datetime.utcnow())
            dm.set_thumbnail(url=i.guild.icon.url if i.guild.icon else None)
            set_footer(dm)
            await self.target.send(embed=dm)
        except: pass

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
    wl_display = " ".join(f"`{w}`" for w in wls) if wls else "*Aucune*"
    e = discord.Embed(title="📋  Panel Whitelist", color=C["dark"], timestamp=datetime.utcnow())
    e.set_author(name=member.display_name, icon_url=member.display_avatar.url)
    e.add_field(name="WL actuelles", value=wl_display, inline=False)
    e.set_thumbnail(url=member.display_avatar.url)
    set_footer(e, ctx.author)
    await ctx.reply(embed=e, view=WLView(member, ctx.author))

# ══════════════════════════════════════════════════════════════════════
#  PANEL PRINCIPAL - &wlpanel  (nouveau design : boutons simples)
# ══════════════════════════════════════════════════════════════════════

def build_wlpanel_embed(guild: discord.Guild):
    voicevip_p = set(SYS_PLUS_IDS); server_p = set(SYS_PLUS_IDS)
    sys_p      = set(SYS_PLUS_IDS); priv_p   = set()
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
        timestamp=datetime.utcnow(),
    )
    e.add_field(name=f"{status_icon} Statut",     value=status_txt,              inline=False)
    e.add_field(name="🎤 VoiceVIP",               value=f"`{len(voicevip_p)}` membres", inline=True)
    e.add_field(name="🌐 Server",                 value=f"`{len(server_p)}` membres",   inline=True)
    e.add_field(name="⚡ WL Sys",                 value=f"`{len(sys_p)}` membres",      inline=True)
    e.add_field(name="👑 Privilege",              value=f"`{len(priv_p)}` membres",     inline=True)
    e.add_field(name="🔒 Vocs privées",           value=f"`{len(private_vocs)}`",       inline=True)
    e.add_field(name="🐕 Laisses",               value=f"`{len(laisse_active)}`",       inline=True)
    e.add_field(name="🏃 Follows",               value=f"`{len(follow_active)}`",       inline=True)
    e.add_field(name="⛓️ Menottes",              value=f"`{len(menotte_active)}`",      inline=True)
    e.add_field(name="😈 Wakeups actifs",         value=f"`{len(wakeup_active)}`",      inline=True)
    set_footer(e)
    return e


class WLPanelView(discord.ui.View):
    """Panel principal — tous les boutons d'action en direct, sans sous-panneaux."""

    def __init__(self, guild: discord.Guild, invoker_id: int):
        super().__init__(timeout=180)
        self.guild      = guild
        self.invoker_id = invoker_id

    async def interaction_check(self, i: discord.Interaction) -> bool:
        if not is_sys_plus(i.user.id):
            await i.response.send_message(embed=embed_err("Ce panel est réservé aux **Sys+**."), ephemeral=True)
            return False
        return True

    # ── Ligne 1 : Vocaux privées ──────────────────────────────────
    @discord.ui.button(label="🔒 Lister les PV", style=discord.ButtonStyle.blurple, row=0)
    async def list_pv(self, i: discord.Interaction, b):
        if not private_vocs:
            return await i.response.send_message(embed=embed_warn("Aucune vocal privée active."), ephemeral=True)
        lines = []
        for cid, info in private_vocs.items():
            ch = self.guild.get_channel(cid)
            ow = self.guild.get_member(info["owner"])
            lines.append(f"> **#{ch.name if ch else cid}**  `{info['type']}`  •  {ow.mention if ow else info['owner']}")
        e = embed_info("\n".join(lines), title=f"🔒 Vocaux privés ({len(private_vocs)})")
        await i.response.send_message(embed=e, ephemeral=True)

    @discord.ui.button(label="🔓 Déprivatiser PV", style=discord.ButtonStyle.red, row=0)
    async def deprivatiser_pv(self, i: discord.Interaction, b):
        if not private_vocs:
            return await i.response.send_message(embed=embed_warn("Aucune vocal privée active."), ephemeral=True)
        lines = []
        for cid, info in private_vocs.items():
            ch = self.guild.get_channel(cid)
            ow = self.guild.get_member(info["owner"])
            lines.append(f"> **#{ch.name if ch else cid}**  `{info['type']}`  •  {ow.mention if ow else info['owner']}")
        info_e = embed_info(
            "\n".join(lines) + "\n\n**Réponds avec l'ID du salon vocal** à déprivatiser, ou `annuler`.",
            title=f"🔒 Vocaux privés — Choisir",
        )
        await i.response.send_message(embed=info_e, ephemeral=True)

        def check(m):
            return m.author.id == i.user.id and m.channel == i.channel

        try:
            msg = await bot.wait_for("message", check=check, timeout=30)
            if msg.content.strip().lower() == "annuler":
                return await msg.reply(embed=embed_warn("Annulé."), delete_after=5)
            cid = int(msg.content.strip())
            if cid not in private_vocs:
                return await msg.reply(embed=embed_err("ID introuvable parmi les PV actives."), delete_after=5)
            private_vocs.pop(cid, None)
            pv_access.pop(cid, None)
            ch = self.guild.get_channel(cid)
            await msg.reply(embed=embed_ok(f"**#{ch.name if ch else cid}** est maintenant publique."), delete_after=5)
        except asyncio.TimeoutError:
            pass

    # ── Ligne 1 : Laisses ────────────────────────────────────────
    @discord.ui.button(label="🐕 Lister les laisses", style=discord.ButtonStyle.blurple, row=0)
    async def list_laisse(self, i: discord.Interaction, b):
        if not laisse_active:
            return await i.response.send_message(embed=embed_warn("Aucune laisse active."), ephemeral=True)
        lines = [
            f"> {self.guild.get_member(o).mention if self.guild.get_member(o) else o}  →  {self.guild.get_member(c).mention if self.guild.get_member(c) else c}"
            for o, (c, _, _) in laisse_active.items()
        ]
        e = embed_info("\n".join(lines), title=f"🐕 Laisses actives ({len(laisse_active)})")
        await i.response.send_message(embed=e, ephemeral=True)

    @discord.ui.button(label="🔓 Retirer une laisse", style=discord.ButtonStyle.red, row=0)
    async def retirer_laisse(self, i: discord.Interaction, b):
        if not laisse_active:
            return await i.response.send_message(embed=embed_warn("Aucune laisse active."), ephemeral=True)
        lines = []
        for oid, (cid, _, _) in laisse_active.items():
            ow = self.guild.get_member(oid)
            ci = self.guild.get_member(cid)
            lines.append(f"> `{oid}` — {ow.display_name if ow else oid}  →  {ci.display_name if ci else cid}")
        info_e = embed_info(
            "\n".join(lines) + "\n\n**Réponds avec l'ID du propriétaire** de la laisse à retirer, ou `annuler`.",
            title="🐕 Laisses — Choisir",
        )
        await i.response.send_message(embed=info_e, ephemeral=True)

        def check(m):
            return m.author.id == i.user.id and m.channel == i.channel

        try:
            msg = await bot.wait_for("message", check=check, timeout=30)
            if msg.content.strip().lower() == "annuler":
                return await msg.reply(embed=embed_warn("Annulé."), delete_after=5)
            oid = int(msg.content.strip())
            entry = laisse_active.pop(oid, None)
            if entry:
                m = self.guild.get_member(entry[0])
                if m:
                    try: await m.edit(nick=entry[2])
                    except: pass
                await msg.reply(embed=embed_ok("Laisse retirée avec succès."), delete_after=5)
            else:
                await msg.reply(embed=embed_err("ID introuvable."), delete_after=5)
        except asyncio.TimeoutError:
            pass

    # ── Ligne 2 : Follows ────────────────────────────────────────
    @discord.ui.button(label="🏃 Lister les follows", style=discord.ButtonStyle.blurple, row=1)
    async def list_follow(self, i: discord.Interaction, b):
        if not follow_active:
            return await i.response.send_message(embed=embed_warn("Aucun follow actif."), ephemeral=True)
        lines = [
            f"> {self.guild.get_member(f).mention if self.guild.get_member(f) else f}  suit  {self.guild.get_member(t).mention if self.guild.get_member(t) else t}"
            for f, t in follow_active.items()
        ]
        e = embed_info("\n".join(lines), title=f"🏃 Follows actifs ({len(follow_active)})")
        await i.response.send_message(embed=e, ephemeral=True)

    @discord.ui.button(label="🚫 Retirer un follow", style=discord.ButtonStyle.red, row=1)
    async def retirer_follow(self, i: discord.Interaction, b):
        if not follow_active:
            return await i.response.send_message(embed=embed_warn("Aucun follow actif."), ephemeral=True)
        lines = []
        for fid, tid in follow_active.items():
            f = self.guild.get_member(fid)
            t = self.guild.get_member(tid)
            lines.append(f"> `{fid}` — {f.display_name if f else fid}  suit  {t.display_name if t else tid}")
        info_e = embed_info(
            "\n".join(lines) + "\n\n**Réponds avec l'ID** du follower à retirer, ou `annuler`.",
            title="🏃 Follows — Choisir",
        )
        await i.response.send_message(embed=info_e, ephemeral=True)

        def check(m):
            return m.author.id == i.user.id and m.channel == i.channel

        try:
            msg = await bot.wait_for("message", check=check, timeout=30)
            if msg.content.strip().lower() == "annuler":
                return await msg.reply(embed=embed_warn("Annulé."), delete_after=5)
            fid = int(msg.content.strip())
            if fid in follow_active:
                follow_active.pop(fid)
                await msg.reply(embed=embed_ok("Follow retiré avec succès."), delete_after=5)
            else:
                await msg.reply(embed=embed_err("ID introuvable."), delete_after=5)
        except asyncio.TimeoutError:
            pass

    # ── Ligne 2 : Menottes ───────────────────────────────────────
    @discord.ui.button(label="⛓️ Lister les menottes", style=discord.ButtonStyle.blurple, row=1)
    async def list_menotte(self, i: discord.Interaction, b):
        if not menotte_active:
            return await i.response.send_message(embed=embed_warn("Aucune menotte active."), ephemeral=True)
        lines = []
        for oid, (cid, ch_id) in menotte_active.items():
            ow = self.guild.get_member(oid)
            ci = self.guild.get_member(cid)
            ch = self.guild.get_channel(ch_id)
            lines.append(f"> {ow.mention if ow else oid}  ⛓️  {ci.mention if ci else cid}  dans **{ch.name if ch else ch_id}**")
        e = embed_info("\n".join(lines), title=f"⛓️ Menottes actives ({len(menotte_active)})")
        await i.response.send_message(embed=e, ephemeral=True)

    @discord.ui.button(label="🔓 Retirer une menotte", style=discord.ButtonStyle.red, row=1)
    async def retirer_menotte(self, i: discord.Interaction, b):
        if not menotte_active:
            return await i.response.send_message(embed=embed_warn("Aucune menotte active."), ephemeral=True)
        lines = []
        for oid, (cid, ch_id) in menotte_active.items():
            ow = self.guild.get_member(oid)
            ci = self.guild.get_member(cid)
            lines.append(f"> `{oid}` — {ow.display_name if ow else oid}  ⛓️  {ci.display_name if ci else cid}")
        info_e = embed_info(
            "\n".join(lines) + "\n\n**Réponds avec l'ID** du poseur de menotte à retirer, ou `annuler`.",
            title="⛓️ Menottes — Choisir",
        )
        await i.response.send_message(embed=info_e, ephemeral=True)

        def check(m):
            return m.author.id == i.user.id and m.channel == i.channel

        try:
            msg = await bot.wait_for("message", check=check, timeout=30)
            if msg.content.strip().lower() == "annuler":
                return await msg.reply(embed=embed_warn("Annulé."), delete_after=5)
            oid = int(msg.content.strip())
            if oid in menotte_active:
                menotte_active.pop(oid)
                await msg.reply(embed=embed_ok("Menotte retirée avec succès."), delete_after=5)
            else:
                await msg.reply(embed=embed_err("ID introuvable."), delete_after=5)
        except asyncio.TimeoutError:
            pass

    # ── Ligne 3 : Whitelists ─────────────────────────────────────
    @discord.ui.button(label="👥 Lister les WL", style=discord.ButtonStyle.blurple, row=2)
    async def list_wl(self, i: discord.Interaction, b):
        if not whitelisted:
            return await i.response.send_message(embed=embed_warn("Aucune WL active."), ephemeral=True)
        lines = []
        for uid, wls in whitelisted.items():
            m = self.guild.get_member(uid)
            badges = "  ".join(f"{WL_LABELS.get(w, ('•', w, 0))[0]} `{w}`" for w in wls)
            lines.append(f"> **{m.display_name if m else uid}**  →  {badges}")
        e = embed_info("\n".join(lines), title="👥 Whitelists actives")
        await i.response.send_message(embed=e, ephemeral=True)

    @discord.ui.button(label="❌ Retirer une WL", style=discord.ButtonStyle.red, row=2)
    async def retirer_wl(self, i: discord.Interaction, b):
        if not whitelisted:
            return await i.response.send_message(embed=embed_warn("Aucune WL active."), ephemeral=True)
        lines = []
        for uid, wls in whitelisted.items():
            m = self.guild.get_member(uid)
            badges = ", ".join(f"{WL_LABELS.get(w, ('•', w, 0))[0]} {w}" for w in wls)
            lines.append(f"> `{uid}` — **{m.display_name if m else uid}**  →  {badges}")
        info_e = embed_info(
            "\n".join(lines) + "\n\n**Réponds avec : `ID_membre NomWL`** (ex: `123456789 server`), ou `annuler`.",
            title="👥 WL — Choisir",
        )
        await i.response.send_message(embed=info_e, ephemeral=True)

        def check(m):
            return m.author.id == i.user.id and m.channel == i.channel

        try:
            msg = await bot.wait_for("message", check=check, timeout=30)
            if msg.content.strip().lower() == "annuler":
                return await msg.reply(embed=embed_warn("Annulé."), delete_after=5)
            parts = msg.content.strip().split()
            if len(parts) != 2:
                return await msg.reply(embed=embed_err("Format invalide. Ex: `123456789 server`"), delete_after=5)
            uid, wl = int(parts[0]), parts[1]
            if uid in whitelisted and wl in whitelisted[uid]:
                whitelisted[uid].remove(wl)
                if not whitelisted[uid]:
                    del whitelisted[uid]
                save_wl()
                icon, label, color = WL_LABELS.get(wl, ("•", wl, C["error"]))
                m = self.guild.get_member(uid)
                await msg.reply(embed=embed_ok(f"La **{label}** a été retirée à **{m.display_name if m else uid}**."), delete_after=8)
                asyncio.create_task(send_log(
                    i.guild, i.user, "wl",
                    f"WL retirée — {label}",
                    [("⌨️ Commande", "`&wlpanel` → Retirer WL"), ("🏷️ WL", f"`{wl}`  {icon}"), ("📋 Label", label)],
                    target=m,
                ))
                if m:
                    try:
                        dm = discord.Embed(title="🚫  Whitelist retirée", description=f"Ta **{label}** t'a été retirée sur **{i.guild.name}**.", color=C["error"], timestamp=datetime.utcnow())
                        dm.set_thumbnail(url=i.guild.icon.url if i.guild.icon else None)
                        set_footer(dm)
                        await m.send(embed=dm)
                    except: pass
            else:
                await msg.reply(embed=embed_err("Cette WL n'existe pas pour cet utilisateur."), delete_after=5)
        except asyncio.TimeoutError:
            pass

    # ── Ligne 3 : Wakeups & Dogs ─────────────────────────────────
    @discord.ui.button(label="😈 Stop wakeup", style=discord.ButtonStyle.grey, row=2)
    async def stop_wakeup(self, i: discord.Interaction, b):
        if not wakeup_active:
            return await i.response.send_message(embed=embed_warn("Aucun wakeup actif."), ephemeral=True)
        ids = ", ".join(f"`{uid}`" for uid in wakeup_active)
        info_e = embed_info(
            f"Wakeups actifs sur : {ids}\n\n**Réponds avec l'ID** du membre à libérer, ou `tous` / `annuler`.",
            title="😈 Wakeups — Choisir",
        )
        await i.response.send_message(embed=info_e, ephemeral=True)

        def check(m):
            return m.author.id == i.user.id and m.channel == i.channel

        try:
            msg = await bot.wait_for("message", check=check, timeout=30)
            val = msg.content.strip().lower()
            if val == "annuler":
                return await msg.reply(embed=embed_warn("Annulé."), delete_after=5)
            if val == "tous":
                wakeup_active.clear()
                return await msg.reply(embed=embed_ok("Tous les wakeups ont été stoppés."), delete_after=5)
            wakeup_active.discard(int(val))
            await msg.reply(embed=embed_ok(f"Wakeup stoppé pour `{val}`."), delete_after=5)
        except asyncio.TimeoutError:
            pass

    @discord.ui.button(label="🐕 Lister les dogs", style=discord.ButtonStyle.blurple, row=3)
    async def list_dog(self, i: discord.Interaction, b):
        if not dog_active:
            return await i.response.send_message(embed=embed_warn("Aucun dog actif."), ephemeral=True)
        lines = []
        for oid, (cid, new, old) in dog_active.items():
            ow = self.guild.get_member(oid)
            ci = self.guild.get_member(cid)
            lines.append(f"> {ow.mention if ow else oid}  🐕  {ci.mention if ci else cid}  *(pseudo : `{new}`)*")
        e = embed_info("\n".join(lines), title=f"🐕 Dogs actifs ({len(dog_active)})")
        await i.response.send_message(embed=e, ephemeral=True)

    @discord.ui.button(label="🔓 Retirer un dog", style=discord.ButtonStyle.red, row=3)
    async def retirer_dog(self, i: discord.Interaction, b):
        if not dog_active:
            return await i.response.send_message(embed=embed_warn("Aucun dog actif."), ephemeral=True)
        lines = []
        for oid, (cid, new, old) in dog_active.items():
            ow = self.guild.get_member(oid)
            ci = self.guild.get_member(cid)
            lines.append(f"> `{oid}` — {ow.display_name if ow else oid}  🐕  {ci.display_name if ci else cid}")
        info_e = embed_info(
            "\n".join(lines) + "\n\n**Réponds avec l'ID** du propriétaire du dog à retirer, ou `annuler`.",
            title="🐕 Dogs — Choisir",
        )
        await i.response.send_message(embed=info_e, ephemeral=True)

        def check(m):
            return m.author.id == i.user.id and m.channel == i.channel

        try:
            msg = await bot.wait_for("message", check=check, timeout=30)
            if msg.content.strip().lower() == "annuler":
                return await msg.reply(embed=embed_warn("Annulé."), delete_after=5)
            oid = int(msg.content.strip())
            if oid in dog_active:
                cid, new, old = dog_active.pop(oid)
                m = self.guild.get_member(cid)
                if m:
                    try: await m.edit(nick=old)
                    except: pass
                await msg.reply(embed=embed_ok("Dog retiré avec succès."), delete_after=5)
            else:
                await msg.reply(embed=embed_err("ID introuvable."), delete_after=5)
        except asyncio.TimeoutError:
            pass

    # ── Ligne 4 : Tipeus & violations PV ─────────────────────────
    @discord.ui.button(label="🔒 Lister les tipeus", style=discord.ButtonStyle.blurple, row=3)
    async def list_tipeu(self, i: discord.Interaction, b):
        if not locked_nicks:
            return await i.response.send_message(embed=embed_warn("Aucun pseudo verrouillé (tipeu) actif."), ephemeral=True)
        lines = []
        for uid in locked_nicks:
            m = self.guild.get_member(uid)
            lines.append(f"> {m.mention if m else uid}  →  pseudo verrouillé sur `S`")
        e = embed_info("\n".join(lines), title=f"🔒 Tipeus actifs ({len(locked_nicks)})")
        await i.response.send_message(embed=e, ephemeral=True)

    @discord.ui.button(label="🔓 Retirer un tipeu", style=discord.ButtonStyle.red, row=3)
    async def retirer_tipeu(self, i: discord.Interaction, b):
        if not locked_nicks:
            return await i.response.send_message(embed=embed_warn("Aucun tipeu actif."), ephemeral=True)
        lines = []
        for uid in locked_nicks:
            m = self.guild.get_member(uid)
            lines.append(f"> `{uid}` — {m.display_name if m else uid}")
        info_e = embed_info(
            "\n".join(lines) + "\n\n**Réponds avec l'ID** du membre à déverrouiller, ou `annuler`.",
            title="🔒 Tipeus — Choisir",
        )
        await i.response.send_message(embed=info_e, ephemeral=True)

        def check(m):
            return m.author.id == i.user.id and m.channel == i.channel

        try:
            msg = await bot.wait_for("message", check=check, timeout=30)
            if msg.content.strip().lower() == "annuler":
                return await msg.reply(embed=embed_warn("Annulé."), delete_after=5)
            uid = int(msg.content.strip())
            if uid in locked_nicks:
                locked_nicks.discard(uid)
                m = self.guild.get_member(uid)
                if m:
                    try: await m.edit(nick=None)
                    except: pass
                await msg.reply(embed=embed_ok(f"Tipeu retiré pour `{uid}`."), delete_after=5)
            else:
                await msg.reply(embed=embed_err("ID introuvable."), delete_after=5)
        except asyncio.TimeoutError:
            pass

    # ── Ligne 4 : Reset violations PV ────────────────────────────
    @discord.ui.button(label="🔄 Reset violations PV", style=discord.ButtonStyle.grey, row=4)
    async def reset_violations(self, i: discord.Interaction, b):
        if not pv_violations:
            return await i.response.send_message(embed=embed_warn("Aucune violation enregistrée."), ephemeral=True)
        lines = []
        for uid, count in pv_violations.items():
            m = self.guild.get_member(uid)
            lines.append(f"> {m.mention if m else uid} — `{count}` violation(s)")
        info_e = embed_info(
            "\n".join(lines) + "\n\n**Réponds avec l'ID** du membre à reset, ou `tous` / `annuler`.",
            title="🛡️ Violations PV — Reset",
        )
        await i.response.send_message(embed=info_e, ephemeral=True)

        def check(m):
            return m.author.id == i.user.id and m.channel == i.channel

        try:
            msg = await bot.wait_for("message", check=check, timeout=30)
            val = msg.content.strip().lower()
            if val == "annuler":
                return await msg.reply(embed=embed_warn("Annulé."), delete_after=5)
            if val == "tous":
                pv_violations.clear()
                return await msg.reply(embed=embed_ok("Toutes les violations ont été réinitialisées."), delete_after=5)
            uid = int(val)
            if uid in pv_violations:
                pv_violations.pop(uid)
                await msg.reply(embed=embed_ok(f"Violations réinitialisées pour `{uid}`."), delete_after=5)
            else:
                await msg.reply(embed=embed_err("Aucune violation trouvée pour cet ID."), delete_after=5)
        except asyncio.TimeoutError:
            pass

    @discord.ui.button(label="🔄 Rafraîchir", style=discord.ButtonStyle.grey, row=4)
    async def refresh(self, i: discord.Interaction, b):
        await i.response.edit_message(embed=build_wlpanel_embed(self.guild), view=self)


@bot.command(name="wlpanel")
@check_sys_plus()
async def wlpanel_cmd(ctx):
    await ctx.reply(embed=build_wlpanel_embed(ctx.guild), view=WLPanelView(ctx.guild, ctx.author.id))

@bot.command(name="restartpanel")
@check_sys_plus()
async def restartpanel_cmd(ctx):
    e = build_wlpanel_embed(ctx.guild)
    e.title = "🔄  Panel redémarré"
    await ctx.reply(embed=e, view=WLPanelView(ctx.guild, ctx.author.id))

# ══════════════════════════════════════════════════════════════════════
#  &clear / &derank
# ══════════════════════════════════════════════════════════════════════
@bot.command(name="clear")
@check_sys_plus()
async def clear_cmd(ctx, amount: int = 50):
    if not 1 <= amount <= 500:
        return await ctx.reply(embed=embed_err("Le montant doit être entre **1** et **500**."))
    deleted = await ctx.channel.purge(limit=amount + 1)
    count = len(deleted) - 1
    e = embed_ok(f"**{count}** message(s) supprimé(s).")
    set_footer(e, ctx.author)
    msg = await ctx.send(embed=e)
    asyncio.create_task(send_log(
        ctx.guild, ctx.author, "clear",
        "Clear salon",
        [
            ("⌨️ Commande",              "`&clear`"),
            ("🗑️ Messages supprimés", f"`{count}`"),
            ("📌 Salon",              ctx.channel.mention),
        ],
    ))
    await asyncio.sleep(1.5)
    await msg.delete()

@bot.command(name="derank")
@check_sys_plus()
async def derank_cmd(ctx, member: discord.Member = None, *, reason: str = "Aucune raison fournie"):
    if not member:
        if ctx.message.reference:
            ref = await ctx.channel.fetch_message(ctx.message.reference.message_id); member = ref.author
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
    roles_txt = ", ".join(r.mention for r in roles)
    await member.remove_roles(*roles, reason=f"Derank par {ctx.author} - {reason}")
    e = discord.Embed(title="🔨  Derank exécuté", color=C["orange"], timestamp=datetime.utcnow())
    e.set_author(name=member.display_name, icon_url=member.display_avatar.url)
    e.add_field(name="Membre", value=member.mention,     inline=True)
    e.add_field(name="Par",    value=ctx.author.mention, inline=True)
    e.add_field(name="Raison", value=f"*{reason}*",      inline=False)
    set_footer(e, ctx.author)
    await ctx.reply(embed=e)
    asyncio.create_task(send_log(
        ctx.guild, ctx.author, "derank",
        "Derank exécuté",
        [
            ("⌨️ Commande",        "`&derank`"),
            ("⚠️ Raison",         f"*{reason}*", False),
            ("🎭 Rôles retirés",  roles_txt,     False),
        ],
        target=member,
    ))
    try:
        dm = discord.Embed(title="⚠️  Tu as été derank", description=f"Tous tes rôles ont été retirés sur **{ctx.guild.name}**.\n\n> *{reason}*", color=C["orange"], timestamp=datetime.utcnow())
        set_footer(dm)
        await member.send(embed=dm)
    except: pass

# ══════════════════════════════════════════════════════════════════════
#  /addrole  /removerole
# ══════════════════════════════════════════════════════════════════════
@tree.command(name="addrole", description="Ajouter un rôle à un membre ou à tout le serveur (Sys+)")
@app_commands.describe(role="Le rôle à ajouter", tous="Ajouter à tous les membres ?", membre="Le membre cible")
async def addrole_slash(i: discord.Interaction, role: discord.Role, tous: bool, membre: discord.Member = None):
    if not is_sys_plus(i.user.id):
        return  # silencieux
    if role >= i.guild.me.top_role:
        return await i.response.send_message(embed=embed_err("Ce rôle est trop haut pour moi."), ephemeral=True)
    if tous:
        await i.response.defer(thinking=True)
        targets = [m for m in i.guild.members if not m.bot and role not in m.roles]
        ok, fail = 0, 0
        for m in targets:
            try:    await m.add_roles(role, reason=f"/addrole tous - par {i.user}"); ok += 1
            except: fail += 1
        e = discord.Embed(title="✅  Rôle ajouté — Serveur entier", color=C["ok"], timestamp=datetime.utcnow())
        e.add_field(name="Rôle",   value=role.mention, inline=True)
        e.add_field(name="Réussi", value=f"`{ok}`",    inline=True)
        e.add_field(name="Échec",  value=f"`{fail}`",  inline=True)
        set_footer(e, i.user); await i.followup.send(embed=e)
        asyncio.create_task(send_log(
            i.guild, i.user, "addrole",
            "Rôle ajouté — Serveur entier",
            [("⌨️ Commande", "`/addrole`"), ("🎭 Rôle", role.mention), ("✅ Réussi", f"`{ok}`"), ("❌ Échec", f"`{fail}`")],
        ))
    else:
        if not membre:
            return await i.response.send_message(embed=embed_err("Précise un membre ou active **tous**."), ephemeral=True)
        if not await protection_check_i(i, membre): return
        if role in membre.roles:
            return await i.response.send_message(embed=embed_warn(f"{membre.mention} a déjà ce rôle."), ephemeral=True)
        try:
            await membre.add_roles(role, reason=f"/addrole - par {i.user}")
            e = embed_ok(title="Rôle ajouté")
            e.add_field(name="Membre", value=membre.mention, inline=True)
            e.add_field(name="Rôle",   value=role.mention,   inline=True)
            set_footer(e, i.user); await i.response.send_message(embed=e)
            asyncio.create_task(send_log(
                i.guild, i.user, "addrole",
                "Rôle ajouté",
                [("⌨️ Commande", "`/addrole`"), ("🎭 Rôle", role.mention)],
                target=membre,
            ))
        except discord.Forbidden:
            await i.response.send_message(embed=embed_err("Impossible d'ajouter ce rôle."), ephemeral=True)

@tree.command(name="removerole", description="Retirer un rôle à un membre ou à tout le serveur (Sys+)")
@app_commands.describe(role="Le rôle à retirer", tous="Retirer à tous les membres ?", membre="Le membre cible")
async def removerole_slash(i: discord.Interaction, role: discord.Role, tous: bool, membre: discord.Member = None):
    if not is_sys_plus(i.user.id):
        return  # silencieux
    if role >= i.guild.me.top_role:
        return await i.response.send_message(embed=embed_err("Ce rôle est trop haut pour moi."), ephemeral=True)
    if tous:
        await i.response.defer(thinking=True)
        targets = [m for m in i.guild.members if not m.bot and role in m.roles]
        ok, fail = 0, 0
        for m in targets:
            try:    await m.remove_roles(role, reason=f"/removerole tous - par {i.user}"); ok += 1
            except: fail += 1
        e = discord.Embed(title="✅  Rôle retiré — Serveur entier", color=C["orange"], timestamp=datetime.utcnow())
        e.add_field(name="Rôle",   value=role.mention, inline=True)
        e.add_field(name="Réussi", value=f"`{ok}`",    inline=True)
        e.add_field(name="Échec",  value=f"`{fail}`",  inline=True)
        set_footer(e, i.user); await i.followup.send(embed=e)
        asyncio.create_task(send_log(
            i.guild, i.user, "removerole",
            "Rôle retiré — Serveur entier",
            [("⌨️ Commande", "`/removerole`"), ("🎭 Rôle", role.mention), ("✅ Réussi", f"`{ok}`"), ("❌ Échec", f"`{fail}`")],
        ))
    else:
        if not membre:
            return await i.response.send_message(embed=embed_err("Précise un membre ou active **tous**."), ephemeral=True)
        if not await protection_check_i(i, membre): return
        if role not in membre.roles:
            return await i.response.send_message(embed=embed_warn(f"{membre.mention} n'a pas ce rôle."), ephemeral=True)
        try:
            await membre.remove_roles(role, reason=f"/removerole - par {i.user}")
            e = discord.Embed(title="✅  Rôle retiré", color=C["orange"], timestamp=datetime.utcnow())
            e.add_field(name="Membre", value=membre.mention, inline=True)
            e.add_field(name="Rôle",   value=role.mention,   inline=True)
            set_footer(e, i.user); await i.response.send_message(embed=e)
            asyncio.create_task(send_log(
                i.guild, i.user, "removerole",
                "Rôle retiré",
                [("⌨️ Commande", "`/removerole`"), ("🎭 Rôle", role.mention)],
                target=membre,
            ))
        except discord.Forbidden:
            await i.response.send_message(embed=embed_err("Impossible de retirer ce rôle."), ephemeral=True)

# ══════════════════════════════════════════════════════════════════════
#  COMMANDES VOICEVIP (=)
# ══════════════════════════════════════════════════════════════════════

@bot.command(name="laisse")
@check_server()
async def laisse_cmd(ctx, member: discord.Member = None):
    if not member:
        return await ctx.reply(embed=embed_err("Usage : `=laisse @membre`"))
    if not await protection_check(ctx, member): return
    oid = ctx.author.id
    if oid in laisse_active and laisse_active[oid][0] == member.id:
        _, nn, on = laisse_active.pop(oid)
        try: await member.edit(nick=on)
        except: pass
        e = embed_warn(f"Laisse retirée à {member.mention}.")
        set_footer(e, ctx.author)
        await ctx.reply(embed=e)
        asyncio.create_task(send_log(
            ctx.guild, ctx.author, "laisse", "Laisse retirée",
            [("⌨️ Commande", "`=laisse`"), ("📝 Ancien pseudo", f"`{on}`")],
            target=member,
        ))
        return
    if oid in laisse_active:
        return await ctx.reply(embed=embed_err("Tu as déjà une laisse active."))
    for o, (cid, _, _) in laisse_active.items():
        if cid == member.id:
            return await ctx.reply(embed=embed_err("Cette personne a déjà la laisse de quelqu'un d'autre."))
    old = member.display_name; new = f"{old} (🐕 de {ctx.author.display_name})"
    try:
        await member.edit(nick=new)
    except discord.Forbidden:
        return await ctx.reply(embed=embed_err("Impossible de changer son pseudo."))
    laisse_active[oid] = (member.id, new, old)
    e = embed_ok(f"{member.mention} est maintenant sous ta laisse. 🐕")
    set_footer(e, ctx.author); await ctx.reply(embed=e)
    asyncio.create_task(send_log(
        ctx.guild, ctx.author, "laisse", "Laisse posée",
        [("⌨️ Commande", "`=laisse`"), ("📝 Nouveau pseudo", f"`{new}`"), ("📝 Ancien pseudo", f"`{old}`")],
        target=member,
    ))

@bot.command(name="pv")
@check_voicevip()
async def pv_cmd(ctx):
    if not ctx.author.voice:
        return await ctx.reply(embed=embed_err("Tu n'es pas dans une vocal."))
    cid = ctx.author.voice.channel.id
    ch  = ctx.author.voice.channel
    if cid in private_vocs and private_vocs[cid]["owner"] == ctx.author.id:
        private_vocs.pop(cid); pv_access.pop(cid, None)
        e = embed_ok("Vocal rendue **publique**."); set_footer(e, ctx.author); await ctx.reply(embed=e)
        asyncio.create_task(send_log(
            ctx.guild, ctx.author, "pv", "Vocal rendue publique",
            [("⌨️ Commande", "`=pv`"), ("🔊 Salon", f"`{ch.name}`")],
        ))
        return
    user_pvs  = [c for c, info in private_vocs.items() if info["owner"] == ctx.author.id]
    max_pvs   = 99 if is_sys_plus(ctx.author.id) else 2
    if len(user_pvs) >= max_pvs:
        return await ctx.reply(embed=embed_err(f"Tu as déjà **{max_pvs}** vocal(s) privée(s) max."))
    pv_type = "sysplus" if is_sys_plus(ctx.author.id) else ("sys" if has_wl_sys(ctx.author.id) else "normal")
    private_vocs[cid] = {"owner": ctx.author.id, "type": pv_type}; pv_access[cid] = set()
    labels = {"normal": "normale", "sys": "Sys", "sysplus": "Sys+"}
    e = discord.Embed(title=f"🔒  Vocal privée [{labels[pv_type]}]", description=f"**{ch.name}** est maintenant privée.", color=C["purple"], timestamp=datetime.utcnow())
    set_footer(e, ctx.author); await ctx.reply(embed=e)
    asyncio.create_task(send_log(
        ctx.guild, ctx.author, "pv", "Vocal privatisée",
        [("⌨️ Commande", "`=pv`"), ("🔊 Salon", f"`{ch.name}`"), ("🏷️ Type", f"`{pv_type}`")],
    ))

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
        e = embed_warn(f"Accès retiré à **{member.display_name}**."); set_footer(e, ctx.author); await ctx.reply(embed=e)
        asyncio.create_task(send_log(
            ctx.guild, ctx.author, "acces", "Accès PV retiré",
            [("⌨️ Commande", "`=acces`"), ("🔊 Vocal", f"`{ctx.author.voice.channel.name}`")],
            target=member,
        ))
        return
    acc.add(member.id)
    e = embed_ok(f"**{member.display_name}** peut maintenant rejoindre ta vocal privée.")
    set_footer(e, ctx.author); await ctx.reply(embed=e)
    asyncio.create_task(send_log(
        ctx.guild, ctx.author, "acces", "Accès PV accordé",
        [("⌨️ Commande", "`=acces`"), ("🔊 Vocal", f"`{ctx.author.voice.channel.name}`")],
        target=member,
    ))

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
    ch_name = member.voice.channel.name
    try:
        await ctx.author.move_to(member.voice.channel)
        e = embed_ok(f"Rejoint **{ch_name}**."); set_footer(e, ctx.author); await ctx.reply(embed=e)
        asyncio.create_task(send_log(
            ctx.guild, ctx.author, "join", "Join vocal",
            [("⌨️ Commande", "`=join`"), ("🔊 Salon rejoint", f"`{ch_name}`")],
            target=member,
        ))
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
        e = embed_ok(f"**{member.display_name}** déplacé dans **{channel.name}**."); set_footer(e, ctx.author); await ctx.reply(embed=e)
        asyncio.create_task(send_log(
            ctx.guild, ctx.author, "mv", "Move vocal",
            [("⌨️ Commande", "`=mv`"), ("🔊 Salon destination", f"`{channel.name}`")],
            target=member,
        ))
    except discord.Forbidden:
        await ctx.reply(embed=embed_err("Impossible de déplacer ce membre."))

@bot.command(name="pvlist")
@check_voicevip()
async def pvlist_cmd(ctx):
    if not private_vocs:
        return await ctx.reply(embed=embed_warn("Aucune vocal privée active."))
    e = discord.Embed(title="🔒  Vocaux privés actifs", color=C["purple"], timestamp=datetime.utcnow())
    for cid, info in private_vocs.items():
        ch  = ctx.guild.get_channel(cid); ow = ctx.guild.get_member(info["owner"])
        acc = [ctx.guild.get_member(u) for u in pv_access.get(cid, set())]
        acc_str = ", ".join(m.display_name for m in acc if m) or "*Personne*"
        e.add_field(name=f"#{ch.name if ch else cid}  [{info['type']}]", value=f"Owner : {ow.mention if ow else info['owner']}\nAccès : {acc_str}", inline=False)
    set_footer(e, ctx.author); await ctx.reply(embed=e)

@bot.command(name="menotte")
@check_voicevip()
async def menotte_cmd(ctx, member: discord.Member = None):
    if not member:
        return await ctx.reply(embed=embed_err("Usage : `=menotte @membre`"))
    if not await protection_check(ctx, member): return
    oid = ctx.author.id; now = time.time()
    if oid in menotte_active and menotte_active[oid][0] == member.id:
        menotte_active.pop(oid)
        e = embed_warn(f"Menotte retirée à {member.mention}."); set_footer(e, ctx.author); await ctx.reply(embed=e)
        asyncio.create_task(send_log(
            ctx.guild, ctx.author, "menotte", "Menotte retirée",
            [("⌨️ Commande", "`=menotte`")],
            target=member,
        ))
        return
    if oid in menotte_active:
        return await ctx.reply(embed=embed_err("Tu as déjà une menotte active."))
    if not is_sys_plus(oid):
        last = menotte_cd.get(oid, 0)
        if now - last < 120:
            return await ctx.reply(embed=embed_warn(f"Cooldown menotte : encore **{int(120-(now-last))}s**."))
    if not member.voice:
        return await ctx.reply(embed=embed_err("Ce membre n'est pas en vocal."))
    ch_id = member.voice.channel.id; ch_name = member.voice.channel.name
    menotte_active[oid] = (member.id, ch_id); menotte_cd[oid] = now
    e = discord.Embed(title="⛓️  Menotte posée", description=f"{member.mention} est désormais menotté dans **{ch_name}**.", color=C["info"], timestamp=datetime.utcnow())
    set_footer(e, ctx.author); await ctx.reply(embed=e)
    asyncio.create_task(send_log(
        ctx.guild, ctx.author, "menotte", "Menotte posée",
        [("⌨️ Commande", "`=menotte`"), ("🔊 Salon verrouillé", f"`{ch_name}`")],
        target=member,
    ))

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
        e = embed_warn(f"Follow sur **{member.display_name}** retiré."); set_footer(e, ctx.author); await ctx.reply(embed=e)
        asyncio.create_task(send_log(
            ctx.guild, ctx.author, "follow", "Follow retiré",
            [("⌨️ Commande", "`=follow`")],
            target=member,
        ))
        return
    follow_active[ctx.author.id] = member.id
    e = embed_ok(f"Tu suis maintenant **{member.display_name}** en vocal. 🏃"); set_footer(e, ctx.author); await ctx.reply(embed=e)
    asyncio.create_task(send_log(
        ctx.guild, ctx.author, "follow", "Follow activé",
        [("⌨️ Commande", "`=follow`")],
        target=member,
    ))

@bot.command(name="pvsys")
@check_wl_sys()
async def pvsys_cmd(ctx):
    if not ctx.author.voice:
        return await ctx.reply(embed=embed_err("Tu n'es pas dans une vocal."))
    cid = ctx.author.voice.channel.id; ch = ctx.author.voice.channel
    if cid in private_vocs and private_vocs[cid]["owner"] == ctx.author.id:
        private_vocs.pop(cid); pv_access.pop(cid, None)
        e = embed_ok("PV Sys désactivée, vocal rendue publique."); set_footer(e, ctx.author); await ctx.reply(embed=e)
        asyncio.create_task(send_log(
            ctx.guild, ctx.author, "pvsys", "PV Sys désactivée",
            [("⌨️ Commande", "`=pvsys`"), ("🔊 Salon", f"`{ch.name}`")],
        ))
        return
    user_pvs = [c for c, info in private_vocs.items() if info["owner"] == ctx.author.id]
    if len(user_pvs) >= 2 and not is_sys_plus(ctx.author.id):
        return await ctx.reply(embed=embed_err("Maximum **2** vocaux privés."))
    private_vocs[cid] = {"owner": ctx.author.id, "type": "sys"}; pv_access[cid] = set()
    e = discord.Embed(title="🔒  Vocal privée Sys", description=f"**{ch.name}** est maintenant en PV Sys.", color=C["info"], timestamp=datetime.utcnow())
    set_footer(e, ctx.author); await ctx.reply(embed=e)
    asyncio.create_task(send_log(
        ctx.guild, ctx.author, "pvsys", "PV Sys activée",
        [("⌨️ Commande", "`=pvsys`"), ("🔊 Salon", f"`{ch.name}`")],
    ))

# ══════════════════════════════════════════════════════════════════════
#  COMMANDES SERVER
# ══════════════════════════════════════════════════════════════════════
@bot.command(name="mp")
async def mp_cmd(ctx, member: discord.Member = None, *, message: str = None):
    if maintenance and not is_sys_plus(ctx.author.id):
        return await ctx.reply(embed=embed_warn("Le bot est en **maintenance**."))
    if not has_server(ctx.author.id):
        return  # silencieux
    if not member or not message:
        return await ctx.reply(embed=embed_err("Usage : `=mp @membre message`"))
    if not await protection_check(ctx, member): return
    try:
        await member.send(message)
        e = embed_ok(f"Message envoyé anonymement à {member.mention}."); set_footer(e, ctx.author); await ctx.reply(embed=e)
        asyncio.create_task(send_log(
            ctx.guild, ctx.author, "mp", "MP anonyme envoyé",
            [("⌨️ Commande", "`=mp`"), ("✉️ Message", f"```{message[:200]}```", False)],
            target=member,
        ))
    except discord.Forbidden:
        await ctx.reply(embed=embed_err("Impossible d'envoyer le MP (DMs fermés)."))

@tree.command(name="dog-add", description="Dog quelqu'un — il te suit partout en vocal (Server WL)")
@app_commands.describe(membre="La personne à dog")
async def dog_add(i: discord.Interaction, membre: discord.Member):
    if maintenance and not is_sys_plus(i.user.id):
        return await i.response.send_message(embed=embed_warn("Le bot est en **maintenance**."), ephemeral=True)
    if not has_server(i.user.id):
        return  # silencieux
    if not await protection_check_i(i, membre): return
    oid = i.user.id; now = time.time()
    if oid in dog_active and dog_active[oid][0] == membre.id:
        return await i.response.send_message(embed=embed_warn("Cette personne est déjà ton dog."), ephemeral=True)
    if oid in dog_active:
        return await i.response.send_message(embed=embed_err("Tu as déjà un dog actif. Fais `/dog-del` d'abord."), ephemeral=True)
    if not is_sys_plus(oid):
        last = dog_cd.get(oid, 0)
        if now - last < 60:
            return await i.response.send_message(embed=embed_warn(f"Cooldown dog : encore **{int(60-(now-last))}s**."), ephemeral=True)
    old = membre.display_name; new = f"{old} (🐕 de {i.user.display_name})"
    try:
        await membre.edit(nick=new)
    except discord.Forbidden:
        return await i.response.send_message(embed=embed_err("Impossible de changer son pseudo."), ephemeral=True)
    dog_active[oid] = (membre.id, new, old); dog_cd[oid] = now
    e = embed_ok(f"**{membre.display_name}** est maintenant ton dog. 🐕"); set_footer(e, i.user)
    await i.response.send_message(embed=e)
    asyncio.create_task(send_log(
        i.guild, i.user, "dog", "Dog activé",
        [("⌨️ Commande", "`/dog-add`"), ("📝 Nouveau pseudo", f"`{new}`"), ("📝 Ancien pseudo", f"`{old}`")],
        target=membre,
    ))

@tree.command(name="dog-del", description="Retirer le dog actif (Server WL)")
async def dog_del(i: discord.Interaction):
    if maintenance and not is_sys_plus(i.user.id):
        return await i.response.send_message(embed=embed_warn("Le bot est en **maintenance**."), ephemeral=True)
    if not has_server(i.user.id):
        return  # silencieux
    if i.user.id not in dog_active:
        return await i.response.send_message(embed=embed_err("Tu n'as pas de dog actif."), ephemeral=True)
    cid, new, old = dog_active.pop(i.user.id)
    m = i.guild.get_member(cid)
    if m:
        try: await m.edit(nick=old)
        except: pass
    e = embed_warn("Dog retiré avec succès."); set_footer(e, i.user)
    await i.response.send_message(embed=e)
    asyncio.create_task(send_log(
        i.guild, i.user, "dog", "Dog retiré",
        [("⌨️ Commande", "`/dog-del`"), ("📝 Pseudo restauré", f"`{old}`")],
        target=m,
    ))

# ══════════════════════════════════════════════════════════════════════
#  /wakeup
# ══════════════════════════════════════════════════════════════════════
async def _run_wakeup(guild, target, invoker, custom_msg, duration):
    spam_msg = (f"{target.mention} {custom_msg}" if custom_msg else f"Reveille toi {target.mention} ! C'est {invoker.mention} qui te l'ordonne 😈")
    wakeup_active.add(target.id); wakeup_cd[invoker.id] = time.time()
    vcs = list(guild.voice_channels); delay = max(0.1, 1.0 / 3)
    async def spam_task():
        for _ in range(duration * 3):
            if target.id not in wakeup_active: break
            try: await target.send(spam_msg)
            except: pass
            await asyncio.sleep(delay)
    asyncio.create_task(spam_task())
    end = asyncio.get_event_loop().time() + duration
    while asyncio.get_event_loop().time() < end:
        if target.voice and vcs:
            try: await target.move_to(random.choice(vcs))
            except: pass
        await asyncio.sleep(0.2)
    try: await target.move_to(None)
    except: pass
    wakeup_active.discard(target.id)

class WakeupDurationSelect(discord.ui.Select):
    def __init__(self, target, invoker, custom_msg):
        opts = [
            discord.SelectOption(label="10s",   value="10"),
            discord.SelectOption(label="30s",   value="30"),
            discord.SelectOption(label="1 min", value="60"),
            discord.SelectOption(label="2 min", value="120"),
            discord.SelectOption(label="5 min", value="300"),
            discord.SelectOption(label="Durée personnalisée...", value="custom"),
        ]
        super().__init__(placeholder="Choisir la durée...", options=opts)
        self.target = target; self.invoker = invoker; self.custom_msg = custom_msg
    async def callback(self, i):
        if self.values[0] == "custom":
            return await i.response.send_modal(WakeupCustomDurationModal(self.target, self.invoker, self.custom_msg))
        duration = int(self.values[0]); await i.response.defer(ephemeral=True)
        e = discord.Embed(title="😈  Wakeup lancé !", description=f"**Cible :** {self.target.mention}\n**Durée :** `{duration}s`", color=C["orange"], timestamp=datetime.utcnow())
        set_footer(e, self.invoker); await i.followup.send(embed=e, ephemeral=True)
        asyncio.create_task(_run_wakeup(i.guild, self.target, self.invoker, self.custom_msg, duration))
        asyncio.create_task(send_log(
            i.guild, self.invoker, "wakeup", "Wakeup lancé",
            [("⌨️ Commande",  "`/wakeup`"), ("⏱️ Durée", f"`{duration}s`"), ("✉️ Message", f"`{self.custom_msg}`" if self.custom_msg else "*Aucun*")],
            target=self.target,
        ))

class WakeupDurationView(discord.ui.View):
    def __init__(self, target, invoker, custom_msg):
        super().__init__(timeout=30); self.add_item(WakeupDurationSelect(target, invoker, custom_msg))

class WakeupCustomDurationModal(discord.ui.Modal, title="Durée personnalisée"):
    duree = discord.ui.TextInput(label="Durée en secondes", placeholder="5 - 600", max_length=4, required=True)
    def __init__(self, target, invoker, custom_msg):
        super().__init__(); self.target = target; self.invoker = invoker; self.custom_msg = custom_msg
    async def on_submit(self, i):
        try:
            duration = int(self.duree.value.strip())
            if not 5 <= duration <= 600: raise ValueError
        except ValueError:
            return await i.response.send_message(embed=embed_err("Durée invalide (5-600s)."), ephemeral=True)
        await i.response.defer(ephemeral=True)
        e = discord.Embed(title="😈  Wakeup lancé !", description=f"**Cible :** {self.target.mention}\n**Durée :** `{duration}s`", color=C["orange"], timestamp=datetime.utcnow())
        set_footer(e, self.invoker); await i.followup.send(embed=e, ephemeral=True)
        asyncio.create_task(_run_wakeup(i.guild, self.target, self.invoker, self.custom_msg, duration))
        asyncio.create_task(send_log(
            i.guild, self.invoker, "wakeup", "Wakeup lancé (custom)",
            [("⌨️ Commande",  "`/wakeup`"), ("⏱️ Durée", f"`{duration}s`"), ("✉️ Message", f"`{self.custom_msg}`" if self.custom_msg else "*Aucun*")],
            target=self.target,
        ))

class WakeupModal(discord.ui.Modal, title="Wakeup"):
    message = discord.ui.TextInput(label="Message personnalisé (optionnel)", required=False, max_length=200)
    def __init__(self, target, invoker):
        super().__init__(); self.target = target; self.invoker = invoker
    async def on_submit(self, i):
        if not await protection_check_i(i, self.target): return
        now = time.time()
        if not is_sys_plus(self.invoker.id):
            last = wakeup_cd.get(self.invoker.id, 0)
            if now - last < 300:
                return await i.response.send_message(embed=embed_warn(f"Cooldown : encore **{int(300-(now-last))}s**."), ephemeral=True)
        if self.target.id in wakeup_active:
            return await i.response.send_message(embed=embed_err("Déjà en wakeup."), ephemeral=True)
        custom = self.message.value.strip()
        if is_sys_plus(self.invoker.id):
            e = discord.Embed(title="⚡  Wakeup Sys+ — Durée", description=f"**Cible :** {self.target.mention}\nChoisis la durée.", color=C["sys"], timestamp=datetime.utcnow())
            set_footer(e, self.invoker)
            await i.response.send_message(embed=e, view=WakeupDurationView(self.target, self.invoker, custom), ephemeral=True)
        else:
            await i.response.defer(ephemeral=True)
            await i.followup.send(embed=embed_ok(f"Wakeup lancé sur {self.target.mention} !"), ephemeral=True)
            asyncio.create_task(_run_wakeup(i.guild, self.target, self.invoker, custom, 10))
            asyncio.create_task(send_log(
                i.guild, self.invoker, "wakeup", "Wakeup lancé",
                [("⌨️ Commande",  "`/wakeup`"), ("⏱️ Durée", "`10s` (fixe)"), ("✉️ Message", f"`{custom}`" if custom else "*Aucun*")],
                target=self.target,
            ))

@tree.command(name="wakeup", description="Wakeup un membre (Server WL)")
@app_commands.describe(membre="Le membre à wakeup")
async def wakeup_slash(i, membre: discord.Member):
    if maintenance and not is_sys_plus(i.user.id):
        return await i.response.send_message(embed=embed_warn("Maintenance."), ephemeral=True)
    if not has_server(i.user.id):
        return  # silencieux
    await i.response.send_modal(WakeupModal(membre, i.user))

# ══════════════════════════════════════════════════════════════════════
#  /snap
# ══════════════════════════════════════════════════════════════════════
class SnapResponseModal(discord.ui.Modal, title="Donner mon Snapchat"):
    snap = discord.ui.TextInput(label="Ton Snapchat", placeholder="ton_snap", max_length=50)

    def __init__(self, demandeur: discord.Member, view: "SnapView"):
        super().__init__()
        self.demandeur = demandeur
        self._parent_view = view

    async def on_submit(self, i: discord.Interaction):
        e = discord.Embed(title="📸  Snap reçu !", color=C["warn"], timestamp=datetime.utcnow())
        e.add_field(name="De",       value=i.user.mention)
        e.add_field(name="Snapchat", value=f"`{self.snap.value}`")
        e.set_thumbnail(url=i.user.display_avatar.url)
        set_footer(e)
        try:
            await self.demandeur.send(embed=e)
            await i.response.send_message(embed=embed_ok("Snap envoyé ! 📸"), ephemeral=True)
            self._parent_view.disable_all()
            try: await self._parent_view.message.edit(view=self._parent_view)
            except: pass
            asyncio.create_task(send_log(
                self._parent_view.guild, i.user, "snap_give",
                "Snap partagé ✅",
                [("⌨️ Commande", "`/snap`"), ("📸 Snap", f"`{self.snap.value}`"), ("📨 Demandeur", f"{self.demandeur.mention}\n`{self.demandeur.id}`")],
                target=self.demandeur,
            ))
        except discord.Forbidden:
            await i.response.send_message(embed=embed_err("DMs fermés, impossible d'envoyer."), ephemeral=True)


class SnapView(discord.ui.View):
    def __init__(self, demandeur: discord.Member, guild: discord.Guild):
        super().__init__(timeout=300)
        self.demandeur = demandeur
        self.guild     = guild
        self.message: discord.Message | None = None

    def disable_all(self):
        for item in self.children:
            item.disabled = True

    @discord.ui.button(label="📸  Donner mon Snap", style=discord.ButtonStyle.blurple, custom_id="snap_give")
    async def give_snap(self, i: discord.Interaction, b: discord.ui.Button):
        await i.response.send_modal(SnapResponseModal(self.demandeur, self))

    @discord.ui.button(label="❌  Refuser", style=discord.ButtonStyle.red, custom_id="snap_refuse")
    async def refuse_snap(self, i: discord.Interaction, b: discord.ui.Button):
        try:
            e = discord.Embed(
                title="💀  Snap refusé",
                description="La honte, il/elle a refusé(e) ton Snap. 😂💀\n"
                            f"*(refus de **{i.user.display_name}**)*",
                color=C["error"],
                timestamp=datetime.utcnow(),
            )
            set_footer(e)
            await self.demandeur.send(embed=e)
        except discord.Forbidden:
            pass
        await i.response.send_message(embed=embed_ok("Refus envoyé. 👍"), ephemeral=True)
        self.disable_all()
        try: await self.message.edit(view=self)
        except: pass
        asyncio.create_task(send_log(
            self.guild, i.user, "snap_refuse",
            "Snap refusé ❌",
            [("⌨️ Commande", "`/snap`"), ("📨 Demandeur", f"{self.demandeur.mention}\n`{self.demandeur.id}`")],
            target=self.demandeur,
        ))
        self.stop()


@tree.command(name="snap", description="Demander le snap de quelqu'un (Server WL)")
@app_commands.describe(membre="La personne", message="Ton message (optionnel)")
async def snap_slash(i: discord.Interaction, membre: discord.Member, message: str = ""):
    if maintenance and not is_sys_plus(i.user.id):
        return await i.response.send_message(embed=embed_warn("Maintenance."), ephemeral=True)
    if not has_server(i.user.id):
        return  # silencieux
    e = discord.Embed(title="📸  Quelqu'un veut ton Snap !", color=C["warn"], timestamp=datetime.utcnow())
    e.set_author(name=i.user.display_name, icon_url=i.user.display_avatar.url)
    if message:
        e.add_field(name="Message", value=f"*{message}*", inline=False)
    e.set_footer(text="Clique si tu veux partager ton snap — ou refuse directement.")
    view = SnapView(i.user, i.guild)
    try:
        sent = await membre.send(embed=e, view=view)
        view.message = sent
        await i.response.send_message(embed=embed_ok(f"Demande envoyée à {membre.mention} ! 📨"), ephemeral=True)
        asyncio.create_task(send_log(
            i.guild, i.user, "snap",
            "Snap demandé 📸",
            [("⌨️ Commande", "`/snap`"), ("✉️ Message", f"`{message}`" if message else "*Aucun*")],
            target=membre,
        ))
    except discord.Forbidden:
        await i.response.send_message(embed=embed_err("Impossible d'envoyer le MP (DMs fermés)."), ephemeral=True)

# ══════════════════════════════════════════════════════════════════════
#  /tipeu
# ══════════════════════════════════════════════════════════════════════
@tree.command(name="tipeu", description="Rename en S et verrouille le pseudo (Server WL)")
@app_commands.describe(membre="La cible")
async def tipeu_slash(i, membre: discord.Member):
    if maintenance and not is_sys_plus(i.user.id):
        return await i.response.send_message(embed=embed_warn("Maintenance."), ephemeral=True)
    if not has_server(i.user.id):
        return  # silencieux
    if not await protection_check_i(i, membre): return
    if membre.id in locked_nicks:
        locked_nicks.discard(membre.id)
        try: await membre.edit(nick=None)
        except: pass
        e = embed_warn(f"Pseudo de {membre.mention} déverrouillé."); set_footer(e, i.user)
        await i.response.send_message(embed=e)
        asyncio.create_task(send_log(
            i.guild, i.user, "tipeu", "Tipeu retiré — pseudo déverrouillé",
            [("⌨️ Commande", "`/tipeu`")],
            target=membre,
        ))
        return
    try:
        old_nick = membre.display_name
        await membre.edit(nick="S")
        locked_nicks.add(membre.id)
        e = discord.Embed(title="🔒  Pseudo verrouillé", description=f"{membre.mention} renommé **S** et verrouillé.", color=C["info"], timestamp=datetime.utcnow())
        set_footer(e, i.user); await i.response.send_message(embed=e)
        asyncio.create_task(send_log(
            i.guild, i.user, "tipeu", "Tipeu activé — pseudo verrouillé",
            [("⌨️ Commande", "`/tipeu`"), ("📝 Ancien pseudo", f"`{old_nick}`"), ("📝 Nouveau pseudo", "`S`")],
            target=membre,
        ))
    except discord.Forbidden:
        await i.response.send_message(embed=embed_err("Impossible de changer son pseudo."), ephemeral=True)

# ══════════════════════════════════════════════════════════════════════
#  COMMANDES LIBERTÉ (accessibles à tous)
# ══════════════════════════════════════════════════════════════════════

@bot.command(name="ui")
async def ui_cmd(ctx, member: discord.Member = None):
    if maintenance and not is_sys_plus(ctx.author.id):
        return await ctx.reply(embed=embed_warn("Le bot est en **maintenance**."))
    member = member or ctx.author

    status_map = {
        discord.Status.online:    ("🟢", "En ligne"),
        discord.Status.idle:      ("🟡", "Absent"),
        discord.Status.dnd:       ("🔴", "Ne pas déranger"),
        discord.Status.offline:   ("⚫", "Hors ligne"),
        discord.Status.invisible: ("⚫", "Invisible"),
    }
    status_icon, status_label = status_map.get(member.status, ("⚫", "Hors ligne"))

    platforms = []
    if member.desktop_status != discord.Status.offline: platforms.append("🖥️")
    if member.mobile_status  != discord.Status.offline: platforms.append("📱")
    if member.web_status     != discord.Status.offline: platforms.append("🌐")
    platform_str = "  ".join(platforms) if platforms else "—"

    activity_str = "—"
    if member.activities:
        for act in member.activities:
            if isinstance(act, discord.Spotify):
                activity_str = f"🎵 **{act.title}** — {act.artist}"
                break
            elif isinstance(act, discord.Streaming):
                activity_str = f"🔴 [{act.name}]({act.url})" if act.url else f"🔴 {act.name}"
                break
            elif isinstance(act, discord.Game):
                activity_str = f"🎮 {act.name}"
                break
            elif isinstance(act, discord.CustomActivity) and act.name:
                activity_str = f"💬 {act.name}"
                break
            elif isinstance(act, discord.Activity):
                activity_str = f"🕹️ {act.name}"
                break

    if member.voice and member.voice.channel:
        vc = member.voice.channel
        vc_link = f"https://discord.com/channels/{ctx.guild.id}/{vc.id}"
        voice_str = f"[🔊 **{vc.name}**]({vc_link})  ·  `{len(vc.members)}` membre(s)"
    else:
        voice_str = "*Pas en vocal*"

    created_ts = int(member.created_at.timestamp())
    joined_ts  = int(member.joined_at.timestamp()) if member.joined_at else None

    roles = [r for r in reversed(member.roles) if r != ctx.guild.default_role]
    if roles:
        roles_str = "  ".join(r.mention for r in roles[:12])
        if len(roles) > 12:
            roles_str += f"  *+{len(roles)-12}*"
    else:
        roles_str = "*Aucun rôle*"

    embed_color = member.color if member.color.value else discord.Color(0x2b2d31)

    e = discord.Embed(color=embed_color, timestamp=datetime.utcnow())
    e.set_author(name=member.display_name, icon_url=member.display_avatar.url)
    e.set_thumbnail(url=member.display_avatar.url)

    e.add_field(name="👤  Compte",       value=f"`@{member.name}`  ·  `{member.id}`", inline=False)
    e.add_field(
        name="📋  Informations",
        value=(
            f"**Surnom :** {member.display_name}\n"
            f"**Mention :** {member.mention}\n"
            f"**Bot :** {'Oui' if member.bot else 'Non'}"
        ),
        inline=True,
    )
    e.add_field(
        name="📡  Activité / Statut",
        value=(
            f"**Statut :** {status_icon} {status_label}\n"
            f"**Plateforme :** {platform_str}\n"
            f"**Activité :** {activity_str}"
        ),
        inline=True,
    )
    e.add_field(name="​", value="", inline=False)
    e.add_field(name="🎙️  Vocal", value=voice_str, inline=False)

    dates_val = f"**Créé :** <t:{created_ts}:D>  ·  <t:{created_ts}:R>\n"
    if joined_ts:
        dates_val += f"**Rejoint :** <t:{joined_ts}:D>  ·  <t:{joined_ts}:R>"
    e.add_field(name="📅  Dates", value=dates_val, inline=False)
    e.add_field(name=f"🏷️  Rôles  [{len(roles)}]", value=roles_str, inline=False)

    set_footer(e, ctx.author)
    await ctx.reply(embed=e)


@bot.command(name="snipe")
async def snipe_cmd(ctx):
    if maintenance and not is_sys_plus(ctx.author.id):
        return await ctx.reply(embed=embed_warn("Le bot est en **maintenance**."))

    data = snipe_cache.get(ctx.channel.id)

    try:
        await ctx.message.delete()
    except Exception:
        pass

    if not data:
        e = embed_warn("Aucun message supprimé récemment dans ce salon.")
        set_footer(e)
        msg = await ctx.send(embed=e)
        await asyncio.sleep(3)
        try: await msg.delete()
        except: pass
        return

    deleted_ts = int(data["deleted_at"].timestamp())
    e = discord.Embed(
        description=f">>> {data['content']}",
        color=0x2b2d31,
        timestamp=datetime.utcnow(),
    )
    e.set_author(name=data["author"], icon_url=data["author_icon"])
    e.set_footer(text=f"🗑️  Supprimé  ·  {datetime.utcfromtimestamp(deleted_ts).strftime('%H:%M:%S')}")

    msg = await ctx.send(embed=e)
    await asyncio.sleep(3)
    try: await msg.delete()
    except: pass


# ══════════════════════════════════════════════════════════════════════
#  &help
# ══════════════════════════════════════════════════════════════════════
@bot.command(name="help")
async def help_cmd(ctx):
    e = discord.Embed(title="📖  Commandes disponibles", color=C["dark"], timestamp=datetime.utcnow())
    if maintenance:
        e.description = "> 🔴 **Maintenance active.** Seuls les Sys+ ont accès aux commandes."

    if is_sys_plus(ctx.author.id):
        e.add_field(
            name="⭐  Sys+  [ & ]",
            value=(
                "`&wl`  `&wlpanel`  `&restartpanel`  `&maintenance`\n"
                "`&clear`  `&derank`  `&lock`  `&renew`  `&dmall`\n"
                "`/addrole`  `/removerole`\n"
                "*+ toutes les commandes `=` et `/`*"
            ),
            inline=False,
        )
    if has_wl_sys(ctx.author.id):
        e.add_field(
            name="⚡  WL Sys  [ = ]",
            value="`=follow`  `=pvsys`  *(+ toutes les commandes VoiceVIP)*",
            inline=False,
        )
    if has_voicevip(ctx.author.id):
        e.add_field(
            name="🎤  VoiceVIP  [ = ]",
            value="`=pv`  `=acces`  `=join`  `=mv`  `=pvlist`  `=menotte`",
            inline=False,
        )
    if has_server(ctx.author.id):
        e.add_field(
            name="🌐  Server  [ = / ]",
            value="`=laisse`  `=mp`  `/dog-add`  `/dog-del`  `/wakeup`  `/snap`  `/tipeu`",
            inline=False,
        )

    e.add_field(
        name="🍃  Liberté  [ = ]",
        value="`=ui`  `=snipe`",
        inline=False,
    )

    if not e.fields:
        e.description = "> Tu n'as accès à aucune commande."

    e.set_thumbnail(url=ctx.guild.icon.url if ctx.guild.icon else None)
    set_footer(e, ctx.author)
    await ctx.reply(embed=e)

# ══════════════════════════════════════════════════════════════════════
#  &lock  (verrouille @everyone ET le rôle civil)
# ══════════════════════════════════════════════════════════════════════
@bot.command(name="lock")
@check_sys_plus()
async def lock_cmd(ctx, channel: discord.TextChannel = None):
    channel  = channel or ctx.channel
    everyone = ctx.guild.default_role
    civil    = ctx.guild.get_role(CIVIL_ROLE_ID)

    if channel.id in locked_channels:
        # ── Déverrouillage ──
        saved = locked_channels.pop(channel.id)
        for target, ow in saved.items():
            if ow is None:
                await channel.set_permissions(target, overwrite=None)
            else:
                await channel.set_permissions(target, overwrite=ow)
        e = embed_ok(title="Salon déverrouillé", desc=f"{channel.mention} est de nouveau accessible à tous.")
        set_footer(e, ctx.author); await ctx.reply(embed=e)
        asyncio.create_task(send_log(
            ctx.guild, ctx.author, "lock", "Salon déverrouillé",
            [("⌨️ Commande", "`&lock`"), ("📌 Salon", channel.mention)],
        ))
        return

    # ── Verrouillage ──
    saved_overwrites = {}
    existing_targets = list(channel.overwrites.keys())

    # Sauvegarder et verrouiller les overwrites existants (hors @everyone, civil, bots)
    blocked_targets = {everyone}
    if civil:
        blocked_targets.add(civil)

    for target in existing_targets:
        if target in blocked_targets:
            continue
        is_bot_member = isinstance(target, discord.Member) and target.bot
        is_bot_role   = isinstance(target, discord.Role) and target.managed
        if is_bot_member or is_bot_role:
            continue

        current_ow = channel.overwrites_for(target)
        saved_overwrites[target] = current_ow if not current_ow.is_empty() else None

        new_ow = discord.PermissionOverwrite.from_pair(
            current_ow.pair()[0], current_ow.pair()[1]
        ) if not current_ow.is_empty() else discord.PermissionOverwrite()
        new_ow.send_messages               = False
        new_ow.send_messages_in_threads    = False
        new_ow.create_public_threads       = False
        new_ow.create_private_threads      = False
        new_ow.add_reactions               = False
        new_ow.use_application_commands    = False
        await channel.set_permissions(target, overwrite=new_ow)

    # Sauvegarder les overwrites de @everyone et civil avant de les écraser
    for role in [everyone, civil]:
        if role is None:
            continue
        current_ow = channel.overwrites_for(role)
        saved_overwrites[role] = current_ow if not current_ow.is_empty() else None

    locked_channels[channel.id] = saved_overwrites

    # Appliquer le verrou sur @everyone et le rôle civil
    lock_ow = discord.PermissionOverwrite(
        send_messages=False,
        send_messages_in_threads=False,
        create_public_threads=False,
        create_private_threads=False,
        add_reactions=False,
        use_application_commands=False,
    )
    await channel.set_permissions(everyone, overwrite=lock_ow)
    if civil:
        await channel.set_permissions(civil, overwrite=lock_ow)

    # Autoriser les Sys+ et WL Sys à écrire
    allowed_uids = set(SYS_PLUS_IDS)
    for uid, wls in whitelisted.items():
        if "sys" in wls:
            allowed_uids.add(uid)

    for uid in allowed_uids:
        member = ctx.guild.get_member(uid)
        if member:
            await channel.set_permissions(member,
                send_messages=True,
                send_messages_in_threads=True,
                create_public_threads=True,
                create_private_threads=True,
                add_reactions=True,
                use_application_commands=True,
            )

    e = discord.Embed(
        title="🔒  Salon verrouillé",
        description=(
            f"{channel.mention} est désormais **en lecture seule**.\n"
            "Seuls les **Sys+** et **WL Sys** peuvent écrire.\n\n"
            "Refais `&lock` pour déverrouiller."
        ),
        color=C["maint"], timestamp=datetime.utcnow()
    )
    set_footer(e, ctx.author); await ctx.reply(embed=e)
    asyncio.create_task(send_log(
        ctx.guild, ctx.author, "lock", "Salon verrouillé (lecture seule)",
        [("⌨️ Commande", "`&lock`"), ("📌 Salon", channel.mention)],
    ))
    if channel != ctx.channel:
        try:
            await channel.send(embed=discord.Embed(
                description="🔒  Ce salon est **en lecture seule** — seuls les Sys+ peuvent écrire.",
                color=C["maint"]
            ))
        except: pass

# ══════════════════════════════════════════════════════════════════════
#  &renew
# ══════════════════════════════════════════════════════════════════════
@bot.command(name="renew")
@check_sys_plus()
async def renew_cmd(ctx, channel: discord.TextChannel = None):
    channel    = channel or ctx.channel
    name       = channel.name
    topic      = channel.topic
    position   = channel.position
    category   = channel.category
    slowmode   = channel.slowmode_delay
    nsfw       = channel.is_nsfw()
    overwrites = channel.overwrites

    await channel.delete(reason=f"&renew par {ctx.author}")

    new_ch = await ctx.guild.create_text_channel(
        name=name, topic=topic, category=category,
        slowmode_delay=slowmode, nsfw=nsfw, overwrites=overwrites,
        reason=f"&renew par {ctx.author}"
    )
    try: await new_ch.edit(position=position)
    except: pass

    e = embed_ok(title="Salon renouvelé", desc=f"{new_ch.mention} a été recréé proprement.")
    set_footer(e, ctx.author)
    await new_ch.send(embed=e)
    asyncio.create_task(send_log(
        ctx.guild, ctx.author, "renew", "Salon renouvelé (recréé)",
        [
            ("⌨️ Commande",  "`&renew`"),
            ("📌 Salon",     f"`#{name}`"),
            ("📂 Catégorie", f"`{category.name if category else 'Aucune'}`"),
        ],
    ))

# ══════════════════════════════════════════════════════════════════════
#  &dmall
# ══════════════════════════════════════════════════════════════════════
@bot.command(name="dmall")
@check_sys_plus()
async def dmall_cmd(ctx, *, message: str = None):
    if not message:
        return await ctx.reply(embed=embed_err(
            "Usage : `&dmall message [ID_rôle]`\n"
            "> Écris `{user}` dans le message → remplacé par le ping de chaque destinataire\n"
            "> Ajoute un **ID de rôle** à la fin pour cibler uniquement ses membres\n"
            "> Exemple : `&dmall salut {user} ! 123456789012345678`"
        ))

    role_filter: discord.Role | None = None
    words = message.split()
    if words and words[-1].isdigit() and len(words[-1]) >= 17:
        role_filter = ctx.guild.get_role(int(words[-1]))
        if role_filter:
            message = " ".join(words[:-1]).strip()

    if role_filter:
        members = [m for m in role_filter.members if not m.bot]
        scope_txt = f"les membres avec le rôle {role_filter.mention}"
    else:
        members = [m for m in ctx.guild.members if not m.bot]
        scope_txt = "tous les membres du serveur"

    if not members:
        return await ctx.reply(embed=embed_warn("Aucun membre trouvé pour cet envoi."))

    preview = message.replace("{user}", members[0].mention if members else "@quelqu'un")

    confirm_e = discord.Embed(
        title="📨  Confirmer l'envoi",
        description=(
            f"Tu vas envoyer un DM à **{len(members)}** membres ({scope_txt}).\n\n"
            f"**Message brut :**\n> {message[:300]}\n\n"
            f"**Aperçu (premier destinataire) :**\n> {preview[:300]}\n\n"
            "Clique **Confirmer** pour lancer l'envoi."
        ),
        color=C["warn"], timestamp=datetime.utcnow()
    )
    if role_filter:
        confirm_e.add_field(name="🎭 Rôle ciblé", value=role_filter.mention, inline=True)
    set_footer(confirm_e, ctx.author)

    class ConfirmView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=30)
            self.confirmed = False

        @discord.ui.button(label="✅ Confirmer", style=discord.ButtonStyle.green)
        async def confirm(self, interaction, button):
            if interaction.user.id != ctx.author.id:
                return await interaction.response.send_message(embed=embed_err("Ce n'est pas ton panel."), ephemeral=True)
            self.confirmed = True
            for item in self.children: item.disabled = True
            await interaction.response.edit_message(view=self)
            self.stop()

        @discord.ui.button(label="❌ Annuler", style=discord.ButtonStyle.red)
        async def cancel(self, interaction, button):
            if interaction.user.id != ctx.author.id:
                return await interaction.response.send_message(embed=embed_err("Ce n'est pas ton panel."), ephemeral=True)
            for item in self.children: item.disabled = True
            await interaction.response.edit_message(view=self)
            self.stop()

    view = ConfirmView()
    confirm_msg = await ctx.reply(embed=confirm_e, view=view)
    await view.wait()

    if not view.confirmed:
        return await confirm_msg.edit(embed=embed_warn("Envoi annulé."), view=None)

    progress_e = discord.Embed(
        title="📨  Envoi en cours…",
        description=f"Envoi à **{len(members)}** membres…",
        color=C["info"], timestamp=datetime.utcnow()
    )
    set_footer(progress_e, ctx.author)
    progress_msg = await ctx.send(embed=progress_e)

    ok_count   = 0
    fail_count = 0

    for m in members:
        personalized = message.replace("{user}", m.mention)
        try:
            await m.send(personalized)
            ok_count += 1
        except (discord.Forbidden, discord.HTTPException):
            fail_count += 1
        await asyncio.sleep(0.7)

    result_e = discord.Embed(title="📨  DM Global terminé", color=C["ok"], timestamp=datetime.utcnow())
    result_e.add_field(name="✅ Envoyés",  value=f"`{ok_count}`",  inline=True)
    result_e.add_field(name="❌ Échoués", value=f"`{fail_count}`", inline=True)
    if role_filter:
        result_e.add_field(name="🎭 Rôle ciblé", value=role_filter.mention, inline=True)
    result_e.add_field(name="📝 Message", value=f"```{message[:200]}```", inline=False)
    set_footer(result_e, ctx.author)
    await progress_msg.edit(embed=result_e)

    asyncio.create_task(send_log(
        ctx.guild, ctx.author, "dmall",
        "DM Global envoyé",
        [
            ("⌨️ Commande",  "`&dmall`"),
            ("🎯 Scope",     role_filter.mention if role_filter else "*Tout le serveur*"),
            ("✅ Envoyés",   f"`{ok_count}`"),
            ("❌ Échoués",   f"`{fail_count}`"),
            ("📝 Message",   f"```{message[:200]}```", False),
        ],
    ))

# ══════════════════════════════════════════════════════════════════════
#  LANCEMENT
# ══════════════════════════════════════════════════════════════════════
bot.run(os.environ["TOKEN"])
