import os
import json
import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import random
import time
from datetime import datetime, timedelta

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
CIVIL_ROLE_ID  = 1564722577060929546

# ── Palette DA ────────────────────────────────────────────────────────
C = {
    "ok":       0x43B581,   # vert doux
    "error":    0xF04747,   # rouge vif
    "warn":     0xFAA61A,   # ambre
    "info":     0x7289DA,   # bleu discord
    "sys":      0xFF73FA,   # rose sys+
    "orange":   0xFF7043,   # orange chaud
    "maint":    0xFFB347,   # orange maintenance
    "dark":     0x23272A,   # fond sombre
    "purple":   0xA855F7,   # violet
    "teal":     0x00BFA5,   # turquoise
    "log":      0x2C2F33,   # gris logs
    "gold":     0xF1C40F,   # or
    "rose":     0xFF4081,   # rose vif
    "navy":     0x3F51B5,   # bleu marine
    "mint":     0x26A69A,   # vert menthe
}

SEP = "┄" * 35  # séparateur visuel (jamais de —)

# ══════════════════════════════════════════════════════════════════════
#  EMBED FACTORY  (nouvelle DA)
# ══════════════════════════════════════════════════════════════════════
def _base(color: int) -> discord.Embed:
    return discord.Embed(color=color, timestamp=datetime.utcnow())

def embed_ok(desc: str = None, title: str = None) -> discord.Embed:
    e = _base(C["ok"])
    e.title       = f"✦  {title}" if title else "✦  Succès"
    e.description = desc
    return e

def embed_err(desc: str = None, title: str = None) -> discord.Embed:
    e = _base(C["error"])
    e.title       = f"✗  {title}" if title else "✗  Erreur"
    e.description = desc
    return e

def embed_warn(desc: str = None, title: str = None) -> discord.Embed:
    e = _base(C["warn"])
    e.title       = f"◈  {title}" if title else "◈  Attention"
    e.description = desc
    return e

def embed_info(desc: str = None, title: str = None, color: int = None) -> discord.Embed:
    e = _base(color or C["info"])
    if title: e.title = title
    if desc:  e.description = desc
    return e

def embed_sys(desc: str = None, title: str = None) -> discord.Embed:
    e = _base(C["sys"])
    if title: e.title = f"⬡  {title}"
    if desc:  e.description = desc
    return e

def footer(embed: discord.Embed, user: discord.Member = None) -> discord.Embed:
    now = datetime.utcnow().strftime("%d/%m/%Y  %H:%M")
    if user:
        embed.set_footer(
            text=f"Shotojo  ·  {now}  ·  {user.display_name}",
            icon_url=user.display_avatar.url,
        )
    else:
        embed.set_footer(text=f"Shotojo  ·  {now}")
    return embed

def footer_log(embed: discord.Embed, guild: discord.Guild, author_id: int) -> discord.Embed:
    embed.set_footer(
        text=f"Shotojo Logs  ·  auteur {author_id}",
        icon_url=guild.icon.url if guild.icon else None,
    )
    return embed

# ══════════════════════════════════════════════════════════════════════
#  WHITELIST  I/O
# ══════════════════════════════════════════════════════════════════════
def load_wl() -> dict:
    if os.path.exists(WL_FILE):
        try:
            with open(WL_FILE) as f:
                return {int(k): v for k, v in json.load(f).items()}
        except Exception:
            pass
    return {}

def save_wl() -> None:
    with open(WL_FILE, "w") as f:
        json.dump({str(k): v for k, v in whitelisted.items()}, f)

# ══════════════════════════════════════════════════════════════════════
#  SYSTÈME DE LOGS  (DA repensée)
# ══════════════════════════════════════════════════════════════════════
LOG_META = {
    "snap":        ("📸", C["warn"]),
    "snap_give":   ("📸", C["ok"]),
    "snap_refuse": ("📸", C["error"]),
    "laisse":      ("🐕", C["orange"]),
    "dog":         ("🐕", C["orange"]),
    "wakeup":      ("😈", C["rose"]),
    "follow":      ("🏃", C["teal"]),
    "pv":          ("🔒", C["purple"]),
    "menotte":     ("⛓️",  C["navy"]),
    "mp":          ("✉️",  C["log"]),
    "tipeu":       ("🔒", C["navy"]),
    "wl":          ("👥", C["sys"]),
    "derank":      ("🔨", C["orange"]),
    "clear":       ("🗑️",  C["error"]),
    "lock":        ("🔐", C["maint"]),
    "renew":       ("🔄", C["maint"]),
    "maintenance": ("🔧", C["maint"]),
    "addrole":     ("✅", C["ok"]),
    "removerole":  ("❌", C["error"]),
    "acces":       ("🔑", C["purple"]),
    "join":        ("📞", C["teal"]),
    "mv":          ("↗️",  C["teal"]),
    "pvsys":       ("🔒", C["navy"]),
    "dmall":       ("📨", C["info"]),
    "default":     ("📋", C["log"]),
}

async def send_log(
    guild:      discord.Guild,
    author:     discord.Member,
    action_key: str,
    title:      str,
    fields:     list,
    target:     discord.Member = None,
    extra_desc: str = None,
) -> None:
    ch = guild.get_channel(LOG_CHANNEL_ID)
    if not ch:
        return
    icon, color = LOG_META.get(action_key, LOG_META["default"])
    now = datetime.utcnow()
    e = discord.Embed(title=f"{icon}  {title}", color=color, timestamp=now)
    e.set_author(name=f"{author.display_name}  ·  {author.name}", icon_url=author.display_avatar.url)
    e.set_thumbnail(url=author.display_avatar.url)
    e.add_field(name="👤 Exécuté par",  value=f"{author.mention}\n`{author.id}`", inline=True)
    e.add_field(name="🕐 Horodatage",   value=f"<t:{int(now.timestamp())}:F>\n<t:{int(now.timestamp())}:R>", inline=True)
    if target:
        e.add_field(name="🎯 Cible", value=f"{target.mention}\n`{target.id}`", inline=True)
        e.set_image(url=target.display_avatar.url)
    if fields:
        e.add_field(name="\u200b", value="\u200b", inline=False)
    for f in fields:
        name, value = f[0], f[1]
        inline = f[2] if len(f) > 2 else True
        e.add_field(name=name, value=str(value), inline=inline)
    if extra_desc:
        e.add_field(name="\u200b", value=extra_desc, inline=False)
    footer_log(e, guild, author.id)
    try:
        await ch.send(embed=e)
    except Exception:
        pass

# ══════════════════════════════════════════════════════════════════════
#  STOCKAGE EN MÉMOIRE
# ══════════════════════════════════════════════════════════════════════
whitelisted:     dict  = load_wl()
private_vocs:    dict  = {}   # ch_id -> {owner, type}
pv_access:       dict  = {}   # ch_id -> set(member_id)
pv_violations:   dict  = {}   # member_id -> int (compteur d'intrusions)
follow_active:   dict  = {}   # follower_id -> target_id
laisse_active:   dict  = {}   # owner_id -> (target_id, new_nick, old_nick)
dog_active:      dict  = {}   # owner_id -> (target_id, new_nick, old_nick)
menotte_active:  dict  = {}   # owner_id -> (target_id, channel_id)
wakeup_active:   set   = set()
wakeup_cd:       dict  = {}
dog_cd:          dict  = {}
menotte_cd:      dict  = {}
locked_nicks:    set   = set()
locked_channels: dict  = {}
maintenance:     bool  = False
snipe_cache:     dict  = {}   # ch_id -> {content, author, author_icon, deleted_at}

WL_LABELS = {
    "voicevip":  ("🎤", "VoiceVIP",  C["purple"]),
    "server":    ("🌐", "Server",    C["teal"]),
    "sys":       ("⚡", "WL Sys",    C["info"]),
    "privilege": ("👑", "Privilege", C["sys"]),
}

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

# Messages de protection
MSG_OWNER = (
    "🫵💀  Frérot, j'ai crée le bot et t'essayes de me toucher ?\n"
    "La prochaine c TO 24h, tu feras un ticket pour te faire unto. 🎟️"
)
MSG_SYS = "🚫⚡  N'essaye plus jamais de toucher un **Sys+** ! 😤"

async def protection_check(ctx, target: discord.Member) -> bool:
    if target.id == OWNER_ID and not is_owner(ctx.author.id):
        await ctx.reply(embed=embed_err(MSG_OWNER))
        return False
    if is_sys_plus(target.id) and not is_sys_plus(ctx.author.id):
        await ctx.reply(embed=embed_err(MSG_SYS))
        return False
    return True

async def protection_check_i(i: discord.Interaction, target: discord.Member) -> bool:
    if target.id == OWNER_ID and not is_owner(i.user.id):
        await i.channel.send(embed=embed_err(f"{i.user.mention}  {MSG_OWNER}"))
        return False
    if is_sys_plus(target.id) and not is_sys_plus(i.user.id):
        await i.channel.send(embed=embed_err(f"{i.user.mention}  {MSG_SYS}"))
        return False
    return True

def check_sys_plus():
    async def pred(ctx):
        if not is_sys_plus(ctx.author.id):
            return False
        return True
    return commands.check(pred)

def check_server():
    async def pred(ctx):
        if maintenance and not is_sys_plus(ctx.author.id):
            await ctx.reply(embed=embed_warn("Le bot est en **maintenance**. Reviens plus tard."))
            return False
        if not has_server(ctx.author.id):
            return False
        return True
    return commands.check(pred)

def check_voicevip():
    async def pred(ctx):
        if maintenance and not is_sys_plus(ctx.author.id):
            await ctx.reply(embed=embed_warn("Le bot est en **maintenance**. Reviens plus tard."))
            return False
        if not has_voicevip(ctx.author.id):
            return False
        return True
    return commands.check(pred)

def check_wl_sys():
    async def pred(ctx):
        if maintenance and not is_sys_plus(ctx.author.id):
            await ctx.reply(embed=embed_warn("Le bot est en **maintenance**. Reviens plus tard."))
            return False
        if not has_wl_sys(ctx.author.id):
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
        footer(e)
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
        activity=discord.Activity(type=discord.ActivityType.watching, name="Shotojo 🌸  #🇯🇵"),
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
        try:
            await after.edit(nick="S")
        except Exception:
            pass

@bot.event
async def on_voice_state_update(member, before, after):
    guild = member.guild

    # ── Follow ──
    for fid, tid in list(follow_active.items()):
        if member.id == tid and after.channel and after.channel != before.channel:
            follower = guild.get_member(fid)
            if follower and follower.voice and follower.voice.channel != after.channel:
                try:
                    await follower.move_to(after.channel)
                except Exception:
                    pass

    # ── Dog ──
    for oid, (cid, _, _) in list(dog_active.items()):
        if member.id == oid and after.channel and after.channel != before.channel:
            cible = guild.get_member(cid)
            if cible:
                try:
                    await cible.move_to(after.channel)
                except Exception:
                    pass

    # ── Menotte ──
    for oid, (cid, ch_id) in list(menotte_active.items()):
        if (
            member.id == cid
            and before.channel
            and before.channel.id == ch_id
            and after.channel != before.channel
        ):
            locked_ch = guild.get_channel(ch_id)
            if locked_ch:
                async def _remmenotter(m=member, ch=locked_ch):
                    await asyncio.sleep(0.3)
                    try:
                        await m.move_to(ch)
                    except Exception:
                        pass
                asyncio.create_task(_remmenotter())

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
            # 1. Éjecter immédiatement
            try:
                await member.move_to(None)
            except Exception:
                pass

            # 2. Incrémenter les violations
            count = pv_violations.get(member.id, 0) + 1
            pv_violations[member.id] = count

            labels = {
                "normal":  "🔒 Vocal privée",
                "sys":     "🔒 Vocal privée Sys",
                "sysplus": "🔒 Vocal privée Sys+",
            }
            label = labels.get(pv_type, "Vocal privée")

            if count == 1:
                # 1ère tentative : DM d'avertissement uniquement
                try:
                    e = discord.Embed(
                        title=f"⛔  {label}",
                        description=(
                            "Tu n'as **pas accès** à ce salon vocal.\n"
                            "⚠️  Une prochaine tentative entraînera un **timeout**."
                        ),
                        color=C["error"],
                        timestamp=datetime.utcnow(),
                    )
                    footer(e)
                    await member.send(embed=e)
                except Exception:
                    pass
            else:
                # 2ème tentative et plus : timeout progressif
                timeout_minutes = min(count - 1, 60)
                until = discord.utils.utcnow() + timedelta(minutes=timeout_minutes)
                try:
                    await member.timeout(until, reason=f"Intrusion vocal privée (tentative #{count})")
                except Exception:
                    pass
                try:
                    e = discord.Embed(
                        title=f"⛔  {label}",
                        description=(
                            f"Tu as reçu un **timeout de {timeout_minutes} minute(s)**\n"
                            f"pour tentative d'intrusion dans une vocal privée.\n"
                            f"*(tentative n°{count})*"
                        ),
                        color=C["error"],
                        timestamp=datetime.utcnow(),
                    )
                    footer(e)
                    await member.send(embed=e)
                except Exception:
                    pass

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
        await bot.change_presence(
            status=discord.Status.do_not_disturb,
            activity=discord.Game("🔧  Maintenance en cours"),
        )
        e = embed_warn(
            title="Maintenance activée",
            desc="Toutes les commandes sont **bloquées** pour les non-Sys+.",
        )
    else:
        await bot.change_presence(
            status=discord.Status.online,
            activity=discord.Activity(type=discord.ActivityType.watching, name="Shotojo 🌸  #🇯🇵"),
        )
        e = embed_ok(title="Maintenance désactivée", desc="Le bot est de retour !")
    footer(e, ctx.author)
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
#  &wl
# ══════════════════════════════════════════════════════════════════════
class WLView(discord.ui.View):
    def __init__(self, target: discord.Member, invoker: discord.Member):
        super().__init__(timeout=60)
        self.target  = target
        self.invoker = invoker

    async def interaction_check(self, i: discord.Interaction) -> bool:
        if i.user.id != self.invoker.id:
            await i.response.send_message(
                embed=embed_err("Ce panel ne t'appartient pas."), ephemeral=True
            )
            return False
        return True

    async def _give(self, i: discord.Interaction, wl: str):
        icon, label, color = WL_LABELS[wl]
        lst = whitelisted.setdefault(self.target.id, [])
        if wl in lst:
            return await i.response.send_message(
                embed=embed_warn(f"{self.target.mention} a déjà la **{label}**."), ephemeral=True
            )
        lst.append(wl)
        save_wl()
        e = discord.Embed(
            title=f"{icon}  WL attribuée",
            description=f"{self.target.mention} vient de recevoir la **{label}**.",
            color=color,
            timestamp=datetime.utcnow(),
        )
        e.set_thumbnail(url=self.target.display_avatar.url)
        footer(e, i.user)
        await i.response.send_message(embed=e)
        asyncio.create_task(send_log(
            i.guild, self.invoker, "wl", f"WL attribuée  {label}",
            [("⌨️ Commande", "`&wl`"), ("🏷️ WL", f"`{wl}`  {icon}"), ("📋 Label", label)],
            target=self.target,
        ))
        try:
            dm = discord.Embed(
                title=f"{icon}  Nouvelle whitelist !",
                description=f"Tu as reçu la **{label}** sur **{i.guild.name}**.",
                color=color, timestamp=datetime.utcnow(),
            )
            dm.set_thumbnail(url=i.guild.icon.url if i.guild.icon else None)
            footer(dm)
            await self.target.send(embed=dm)
        except Exception:
            pass

    @discord.ui.button(label="🎤 VoiceVIP",  style=discord.ButtonStyle.blurple)
    async def voicevip(self, i, b):  await self._give(i, "voicevip")
    @discord.ui.button(label="🌐 Server",    style=discord.ButtonStyle.green)
    async def server(self, i, b):    await self._give(i, "server")
    @discord.ui.button(label="⚡ WL Sys",    style=discord.ButtonStyle.grey)
    async def wl_sys(self, i, b):    await self._give(i, "sys")
    @discord.ui.button(label="👑 Privilege", style=discord.ButtonStyle.red)
    async def privilege(self, i, b): await self._give(i, "privilege")


@bot.command(name="wl")
@check_sys_plus()
async def wl_cmd(ctx, member: discord.Member = None):
    if not member:
        return await ctx.reply(embed=embed_err("Usage : `&wl @membre`"))
    wls = whitelisted.get(member.id, [])
    wl_display = "  ".join(
        f"{WL_LABELS[w][0]} `{w}`" for w in wls if w in WL_LABELS
    ) or "*Aucune*"
    e = discord.Embed(
        title="◈  Panel Whitelist",
        color=C["dark"],
        timestamp=datetime.utcnow(),
    )
    e.set_author(name=member.display_name, icon_url=member.display_avatar.url)
    e.add_field(name="WL actuelles", value=wl_display, inline=False)
    e.set_thumbnail(url=member.display_avatar.url)
    footer(e, ctx.author)
    await ctx.reply(embed=e, view=WLView(member, ctx.author))

# ══════════════════════════════════════════════════════════════════════
#  &wlpanel  — tableau de bord avec boutons par entrée
# ══════════════════════════════════════════════════════════════════════

def _wlpanel_embed(guild: discord.Guild) -> discord.Embed:
    """Embed principal du tableau de bord."""
    total_wl = sum(len(v) for v in whitelisted.values())

    vvip = sum(1 for v in whitelisted.values() if "voicevip" in v) + len(SYS_PLUS_IDS)
    srv  = sum(1 for v in whitelisted.values() if "server"   in v) + len(SYS_PLUS_IDS)
    sys_ = sum(1 for v in whitelisted.values() if "sys"      in v) + len(SYS_PLUS_IDS)
    priv = sum(1 for v in whitelisted.values() if "privilege" in v)

    status_line = "🔴  **MAINTENANCE**" if maintenance else "🟢  **Opérationnel**"

    e = discord.Embed(
        title="⬡  Tableau de bord  ·  Sys+",
        description=f"{status_line}\n\n`{SEP}`",
        color=C["maint"] if maintenance else C["dark"],
        timestamp=datetime.utcnow(),
    )

    # Colonne WL
    e.add_field(
        name="🏷️  Whitelists",
        value=(
            f"🎤 VoiceVIP  ·  `{vvip}`\n"
            f"🌐 Server    ·  `{srv}`\n"
            f"⚡ WL Sys   ·  `{sys_}`\n"
            f"👑 Privilege ·  `{priv}`\n"
            f"**Total       ·  `{total_wl}`**"
        ),
        inline=True,
    )

    # Colonne activités
    e.add_field(
        name="⚡  Actifs",
        value=(
            f"🔒 Vocaux privés  ·  `{len(private_vocs)}`\n"
            f"🐕 Laisses         ·  `{len(laisse_active)}`\n"
            f"🐕 Dogs            ·  `{len(dog_active)}`\n"
            f"🏃 Follows         ·  `{len(follow_active)}`\n"
            f"⛓️  Menottes        ·  `{len(menotte_active)}`\n"
            f"😈 Wakeups         ·  `{len(wakeup_active)}`\n"
            f"🔒 Tipeus          ·  `{len(locked_nicks)}`"
        ),
        inline=True,
    )

    e.add_field(name="\u200b", value=f"`{SEP}`", inline=False)
    footer(e)
    return e


# ── Vues par catégorie ────────────────────────────────────────────────

class PVListView(discord.ui.View):
    """Un bouton 🔓 par vocal privée."""
    def __init__(self, guild: discord.Guild, entries: list):
        super().__init__(timeout=120)
        self.guild = guild
        for ch_id, info in entries:
            ch = guild.get_channel(ch_id)
            ow = guild.get_member(info["owner"])
            label = f"🔓  #{ch.name if ch else ch_id}  [{info['type']}]"[:80]
            btn = _make_pv_btn(label, ch_id, ow, self)
            self.add_item(btn)

def _make_pv_btn(label, ch_id, owner, view):
    btn = discord.ui.Button(label=label, style=discord.ButtonStyle.red)
    async def callback(interaction: discord.Interaction):
        if not is_sys_plus(interaction.user.id):
            return await interaction.response.send_message(embed=embed_err("Réservé aux Sys+."), ephemeral=True)
        private_vocs.pop(ch_id, None)
        pv_access.pop(ch_id, None)
        ch = view.guild.get_channel(ch_id)
        e = embed_ok(f"**#{ch.name if ch else ch_id}** est maintenant publique.")
        footer(e, interaction.user)
        await interaction.response.edit_message(embed=e, view=None)
        if owner:
            try:
                dm = embed_warn(
                    f"Ta vocal privée **#{ch.name if ch else ch_id}** a été **déprivatisée** par un Sys+."
                )
                footer(dm)
                await owner.send(embed=dm)
            except Exception:
                pass
        asyncio.create_task(send_log(
            view.guild, interaction.user, "pv", "Vocal déprivatisée via panel",
            [("⌨️ Commande", "`&wlpanel`"), ("🔊 Salon", f"`{ch.name if ch else ch_id}`")],
        ))
    btn.callback = callback
    return btn


class LaisseListView(discord.ui.View):
    def __init__(self, guild: discord.Guild, entries: list):
        super().__init__(timeout=120)
        self.guild = guild
        for oid, (cid, new_nick, old_nick) in entries:
            ow = guild.get_member(oid)
            ci = guild.get_member(cid)
            label = f"🔓  {ow.display_name if ow else oid}  >  {ci.display_name if ci else cid}"[:80]
            btn = _make_laisse_btn(label, oid, cid, old_nick, ow, ci, self)
            self.add_item(btn)

def _make_laisse_btn(label, oid, cid, old_nick, owner, target, view):
    btn = discord.ui.Button(label=label, style=discord.ButtonStyle.red)
    async def callback(interaction: discord.Interaction):
        if not is_sys_plus(interaction.user.id):
            return await interaction.response.send_message(embed=embed_err("Réservé aux Sys+."), ephemeral=True)
        laisse_active.pop(oid, None)
        if target:
            try:
                await target.edit(nick=old_nick)
            except Exception:
                pass
        e = embed_ok(f"Laisse retirée entre **{owner.display_name if owner else oid}** et **{target.display_name if target else cid}**.")
        footer(e, interaction.user)
        await interaction.response.edit_message(embed=e, view=None)
        if owner:
            try:
                await owner.send(embed=embed_warn(f"Ta laisse sur **{target.display_name if target else cid}** a été retirée par un Sys+."))
            except Exception:
                pass
    btn.callback = callback
    return btn


class DogListView(discord.ui.View):
    def __init__(self, guild: discord.Guild, entries: list):
        super().__init__(timeout=120)
        self.guild = guild
        for oid, (cid, new_nick, old_nick) in entries:
            ow = guild.get_member(oid)
            ci = guild.get_member(cid)
            label = f"🔓  {ow.display_name if ow else oid}  >  {ci.display_name if ci else cid}"[:80]
            btn = _make_dog_btn(label, oid, cid, old_nick, ow, ci, self)
            self.add_item(btn)

def _make_dog_btn(label, oid, cid, old_nick, owner, target, view):
    btn = discord.ui.Button(label=label, style=discord.ButtonStyle.red)
    async def callback(interaction: discord.Interaction):
        if not is_sys_plus(interaction.user.id):
            return await interaction.response.send_message(embed=embed_err("Réservé aux Sys+."), ephemeral=True)
        dog_active.pop(oid, None)
        if target:
            try:
                await target.edit(nick=old_nick)
            except Exception:
                pass
        e = embed_ok(f"Dog retiré entre **{owner.display_name if owner else oid}** et **{target.display_name if target else cid}**.")
        footer(e, interaction.user)
        await interaction.response.edit_message(embed=e, view=None)
        if owner:
            try:
                await owner.send(embed=embed_warn(f"Ton dog sur **{target.display_name if target else cid}** a été retiré par un Sys+."))
            except Exception:
                pass
    btn.callback = callback
    return btn


class FollowListView(discord.ui.View):
    def __init__(self, guild: discord.Guild, entries: list):
        super().__init__(timeout=120)
        self.guild = guild
        for fid, tid in entries:
            f = guild.get_member(fid)
            t = guild.get_member(tid)
            label = f"🚫  {f.display_name if f else fid}  suit  {t.display_name if t else tid}"[:80]
            btn = _make_follow_btn(label, fid, f, t, self)
            self.add_item(btn)

def _make_follow_btn(label, fid, follower, target, view):
    btn = discord.ui.Button(label=label, style=discord.ButtonStyle.red)
    async def callback(interaction: discord.Interaction):
        if not is_sys_plus(interaction.user.id):
            return await interaction.response.send_message(embed=embed_err("Réservé aux Sys+."), ephemeral=True)
        follow_active.pop(fid, None)
        e = embed_ok(f"Follow retiré pour **{follower.display_name if follower else fid}**.")
        footer(e, interaction.user)
        await interaction.response.edit_message(embed=e, view=None)
        if follower:
            try:
                await follower.send(embed=embed_warn(f"Ton follow sur **{target.display_name if target else 'la cible'}** a été retiré par un Sys+."))
            except Exception:
                pass
    btn.callback = callback
    return btn


class MenotteListView(discord.ui.View):
    def __init__(self, guild: discord.Guild, entries: list):
        super().__init__(timeout=120)
        self.guild = guild
        for oid, (cid, ch_id) in entries:
            ow = guild.get_member(oid)
            ci = guild.get_member(cid)
            ch = guild.get_channel(ch_id)
            label = f"🔓  {ow.display_name if ow else oid}  ⛓  {ci.display_name if ci else cid}"[:80]
            btn = _make_menotte_btn(label, oid, ow, ci, self)
            self.add_item(btn)

def _make_menotte_btn(label, oid, owner, target, view):
    btn = discord.ui.Button(label=label, style=discord.ButtonStyle.red)
    async def callback(interaction: discord.Interaction):
        if not is_sys_plus(interaction.user.id):
            return await interaction.response.send_message(embed=embed_err("Réservé aux Sys+."), ephemeral=True)
        menotte_active.pop(oid, None)
        e = embed_ok(f"Menotte retirée pour **{owner.display_name if owner else oid}**.")
        footer(e, interaction.user)
        await interaction.response.edit_message(embed=e, view=None)
        if owner:
            try:
                await owner.send(embed=embed_warn(f"Ta menotte sur **{target.display_name if target else 'la cible'}** a été retirée par un Sys+."))
            except Exception:
                pass
    btn.callback = callback
    return btn


class WLRemoveView(discord.ui.View):
    def __init__(self, guild: discord.Guild, entries: list):
        super().__init__(timeout=120)
        self.guild = guild
        for uid, wl in entries:
            m = guild.get_member(uid)
            icon = WL_LABELS.get(wl, ("•", wl, 0))[0]
            label = f"❌  {m.display_name if m else uid}  ·  {icon} {wl}"[:80]
            btn = _make_wl_remove_btn(label, uid, wl, m, self)
            self.add_item(btn)

def _make_wl_remove_btn(label, uid, wl, member, view):
    btn = discord.ui.Button(label=label, style=discord.ButtonStyle.red)
    async def callback(interaction: discord.Interaction):
        if not is_sys_plus(interaction.user.id):
            return await interaction.response.send_message(embed=embed_err("Réservé aux Sys+."), ephemeral=True)
        if uid in whitelisted and wl in whitelisted[uid]:
            whitelisted[uid].remove(wl)
            if not whitelisted[uid]:
                del whitelisted[uid]
            save_wl()
        icon, label_name, color = WL_LABELS.get(wl, ("•", wl, C["error"]))
        e = embed_ok(f"La **{label_name}** a été retirée à **{member.display_name if member else uid}**.")
        footer(e, interaction.user)
        await interaction.response.edit_message(embed=e, view=None)
        asyncio.create_task(send_log(
            view.guild, interaction.user, "wl", f"WL retirée  {label_name}",
            [("⌨️ Commande", "`&wlpanel`"), ("🏷️ WL", f"`{wl}`  {icon}"), ("📋 Label", label_name)],
            target=member,
        ))
        if member:
            try:
                dm = discord.Embed(
                    title="🚫  Whitelist retirée",
                    description=f"Ta **{label_name}** t'a été retirée sur **{view.guild.name}**.",
                    color=C["error"], timestamp=datetime.utcnow(),
                )
                footer(dm)
                await member.send(embed=dm)
            except Exception:
                pass
    btn.callback = callback
    return btn


class TipeuListView(discord.ui.View):
    def __init__(self, guild: discord.Guild, entries: list):
        super().__init__(timeout=120)
        self.guild = guild
        for uid in entries:
            m = guild.get_member(uid)
            label = f"🔓  {m.display_name if m else uid}"[:80]
            btn = _make_tipeu_btn(label, uid, m, self)
            self.add_item(btn)

def _make_tipeu_btn(label, uid, member, view):
    btn = discord.ui.Button(label=label, style=discord.ButtonStyle.red)
    async def callback(interaction: discord.Interaction):
        if not is_sys_plus(interaction.user.id):
            return await interaction.response.send_message(embed=embed_err("Réservé aux Sys+."), ephemeral=True)
        locked_nicks.discard(uid)
        if member:
            try:
                await member.edit(nick=None)
            except Exception:
                pass
        e = embed_ok(f"Tipeu retiré pour **{member.display_name if member else uid}**.")
        footer(e, interaction.user)
        await interaction.response.edit_message(embed=e, view=None)
        if member:
            try:
                await member.send(embed=embed_warn("Ton pseudo a été **déverrouillé** par un Sys+."))
            except Exception:
                pass
    btn.callback = callback
    return btn


# ── Tableau de bord principal ─────────────────────────────────────────

class WLPanelMainView(discord.ui.View):
    def __init__(self, guild: discord.Guild):
        super().__init__(timeout=300)
        self.guild = guild

    async def interaction_check(self, i: discord.Interaction) -> bool:
        if not is_sys_plus(i.user.id):
            await i.response.send_message(embed=embed_err("Réservé aux **Sys+**."), ephemeral=True)
            return False
        return True

    def _cat_embed(self, title: str, color: int, lines: list) -> discord.Embed:
        desc = "\n".join(lines) if lines else "*Aucune entrée active.*"
        e = discord.Embed(title=title, description=desc, color=color, timestamp=datetime.utcnow())
        footer(e)
        return e

    # ── Ligne 0 : vocaux privés ──────────────────────────────────
    @discord.ui.button(label="🔒 Vocaux privés", style=discord.ButtonStyle.blurple, row=0)
    async def btn_pv(self, i: discord.Interaction, b):
        entries = list(private_vocs.items())
        if not entries:
            return await i.response.send_message(
                embed=embed_warn("Aucune vocal privée active."), ephemeral=True
            )
        lines = []
        for ch_id, info in entries:
            ch = self.guild.get_channel(ch_id)
            ow = self.guild.get_member(info["owner"])
            lines.append(
                f"🔒  **#{ch.name if ch else ch_id}**  `{info['type']}`\n"
                f"   › Owner : {ow.mention if ow else info['owner']}"
            )
        view = PVListView(self.guild, entries[:5])  # max 5 boutons Discord
        await i.response.send_message(
            embed=self._cat_embed(f"🔒  Vocaux privés  ({len(entries)})", C["purple"], lines),
            view=view, ephemeral=True,
        )

    # ── Ligne 0 : laisses ────────────────────────────────────────
    @discord.ui.button(label="🐕 Laisses", style=discord.ButtonStyle.blurple, row=0)
    async def btn_laisse(self, i: discord.Interaction, b):
        entries = list(laisse_active.items())
        if not entries:
            return await i.response.send_message(embed=embed_warn("Aucune laisse active."), ephemeral=True)
        lines = []
        for oid, (cid, new_nick, _) in entries:
            ow = self.guild.get_member(oid)
            ci = self.guild.get_member(cid)
            lines.append(
                f"🐕  {ow.mention if ow else oid}  ›  {ci.mention if ci else cid}\n"
                f"   › Pseudo : `{new_nick}`"
            )
        view = LaisseListView(self.guild, entries[:5])
        await i.response.send_message(
            embed=self._cat_embed(f"🐕  Laisses  ({len(entries)})", C["orange"], lines),
            view=view, ephemeral=True,
        )

    # ── Ligne 0 : dogs ───────────────────────────────────────────
    @discord.ui.button(label="🐕 Dogs", style=discord.ButtonStyle.blurple, row=0)
    async def btn_dog(self, i: discord.Interaction, b):
        entries = list(dog_active.items())
        if not entries:
            return await i.response.send_message(embed=embed_warn("Aucun dog actif."), ephemeral=True)
        lines = []
        for oid, (cid, new_nick, _) in entries:
            ow = self.guild.get_member(oid)
            ci = self.guild.get_member(cid)
            lines.append(
                f"🐕  {ow.mention if ow else oid}  ›  {ci.mention if ci else cid}\n"
                f"   › Pseudo : `{new_nick}`"
            )
        view = DogListView(self.guild, entries[:5])
        await i.response.send_message(
            embed=self._cat_embed(f"🐕  Dogs  ({len(entries)})", C["orange"], lines),
            view=view, ephemeral=True,
        )

    # ── Ligne 1 : follows ────────────────────────────────────────
    @discord.ui.button(label="🏃 Follows", style=discord.ButtonStyle.blurple, row=1)
    async def btn_follow(self, i: discord.Interaction, b):
        entries = list(follow_active.items())
        if not entries:
            return await i.response.send_message(embed=embed_warn("Aucun follow actif."), ephemeral=True)
        lines = []
        for fid, tid in entries:
            f = self.guild.get_member(fid)
            t = self.guild.get_member(tid)
            lines.append(f"🏃  {f.mention if f else fid}  suit  {t.mention if t else tid}")
        view = FollowListView(self.guild, entries[:5])
        await i.response.send_message(
            embed=self._cat_embed(f"🏃  Follows  ({len(entries)})", C["teal"], lines),
            view=view, ephemeral=True,
        )

    # ── Ligne 1 : menottes ───────────────────────────────────────
    @discord.ui.button(label="⛓️ Menottes", style=discord.ButtonStyle.blurple, row=1)
    async def btn_menotte(self, i: discord.Interaction, b):
        entries = list(menotte_active.items())
        if not entries:
            return await i.response.send_message(embed=embed_warn("Aucune menotte active."), ephemeral=True)
        lines = []
        for oid, (cid, ch_id) in entries:
            ow = self.guild.get_member(oid)
            ci = self.guild.get_member(cid)
            ch = self.guild.get_channel(ch_id)
            lines.append(
                f"⛓️  {ow.mention if ow else oid}  ›  {ci.mention if ci else cid}\n"
                f"   › Salon : **{ch.name if ch else ch_id}**"
            )
        view = MenotteListView(self.guild, entries[:5])
        await i.response.send_message(
            embed=self._cat_embed(f"⛓️  Menottes  ({len(entries)})", C["navy"], lines),
            view=view, ephemeral=True,
        )

    # ── Ligne 1 : tipeus ─────────────────────────────────────────
    @discord.ui.button(label="🔒 Tipeus", style=discord.ButtonStyle.blurple, row=1)
    async def btn_tipeu(self, i: discord.Interaction, b):
        entries = list(locked_nicks)
        if not entries:
            return await i.response.send_message(embed=embed_warn("Aucun tipeu actif."), ephemeral=True)
        lines = []
        for uid in entries:
            m = self.guild.get_member(uid)
            lines.append(f"🔒  {m.mention if m else uid}  ›  pseudo `S` verrouillé")
        view = TipeuListView(self.guild, entries[:5])
        await i.response.send_message(
            embed=self._cat_embed(f"🔒  Tipeus  ({len(entries)})", C["navy"], lines),
            view=view, ephemeral=True,
        )

    # ── Ligne 2 : whitelists ─────────────────────────────────────
    @discord.ui.button(label="👥 Whitelists", style=discord.ButtonStyle.green, row=2)
    async def btn_wl(self, i: discord.Interaction, b):
        entries = [(uid, wl) for uid, wls in whitelisted.items() for wl in wls]
        if not entries:
            return await i.response.send_message(embed=embed_warn("Aucune WL active."), ephemeral=True)
        lines = []
        for uid, wl in entries:
            m = self.guild.get_member(uid)
            icon = WL_LABELS.get(wl, ("•", wl, 0))[0]
            lines.append(f"{icon}  {m.mention if m else uid}  ·  `{wl}`")
        view = WLRemoveView(self.guild, entries[:5])
        await i.response.send_message(
            embed=self._cat_embed(f"👥  Whitelists  ({len(entries)})", C["sys"], lines),
            view=view, ephemeral=True,
        )

    # ── Ligne 2 : violations PV ──────────────────────────────────
    @discord.ui.button(label="⚠️ Violations PV", style=discord.ButtonStyle.grey, row=2)
    async def btn_violations(self, i: discord.Interaction, b):
        if not pv_violations:
            return await i.response.send_message(embed=embed_warn("Aucune violation enregistrée."), ephemeral=True)
        lines = []
        for uid, count in pv_violations.items():
            m = self.guild.get_member(uid)
            lines.append(f"⚠️  {m.mention if m else uid}  ·  `{count}` tentative(s)")
        pv_violations.clear()
        e = self._cat_embed(f"⚠️  Violations PV  (reset effectué)", C["warn"], lines)
        await i.response.send_message(embed=e, ephemeral=True)

    # ── Ligne 2 : wakeups actifs ─────────────────────────────────
    @discord.ui.button(label="😈 Stop wakeups", style=discord.ButtonStyle.red, row=2)
    async def btn_wakeup(self, i: discord.Interaction, b):
        if not wakeup_active:
            return await i.response.send_message(embed=embed_warn("Aucun wakeup actif."), ephemeral=True)
        ids_before = set(wakeup_active)
        wakeup_active.clear()
        lines = [f"😈  `{uid}`" for uid in ids_before]
        e = embed_ok(f"Tous les wakeups stoppés.\n\n" + "\n".join(lines))
        footer(e, i.user)
        await i.response.send_message(embed=e, ephemeral=True)

    # ── Ligne 3 : rafraîchir ─────────────────────────────────────
    @discord.ui.button(label="🔄 Rafraîchir", style=discord.ButtonStyle.grey, row=3)
    async def btn_refresh(self, i: discord.Interaction, b):
        await i.response.edit_message(embed=_wlpanel_embed(self.guild), view=self)


@bot.command(name="wlpanel")
@check_sys_plus()
async def wlpanel_cmd(ctx):
    await ctx.reply(embed=_wlpanel_embed(ctx.guild), view=WLPanelMainView(ctx.guild))


@bot.command(name="restartpanel")
@check_sys_plus()
async def restartpanel_cmd(ctx):
    e = _wlpanel_embed(ctx.guild)
    e.title = "🔄  Panel redémarré"
    await ctx.reply(embed=e, view=WLPanelMainView(ctx.guild))

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
    footer(e, ctx.author)
    msg = await ctx.send(embed=e)
    asyncio.create_task(send_log(
        ctx.guild, ctx.author, "clear", "Clear salon",
        [("⌨️ Commande", "`&clear`"), ("🗑️ Messages", f"`{count}`"), ("📌 Salon", ctx.channel.mention)],
    ))
    await asyncio.sleep(1.5)
    try:
        await msg.delete()
    except Exception:
        pass


@bot.command(name="derank")
@check_sys_plus()
async def derank_cmd(ctx, member: discord.Member = None, *, reason: str = "Aucune raison fournie"):
    if not member:
        if ctx.message.reference:
            ref = await ctx.channel.fetch_message(ctx.message.reference.message_id)
            member = ref.author
        else:
            return await ctx.reply(embed=embed_err("Usage : `&derank @membre [raison]`"))
    if member == ctx.author:
        return await ctx.reply(embed=embed_err("Tu ne peux pas te derank toi-même."))
    if not await protection_check(ctx, member):
        return
    if member.top_role >= ctx.guild.me.top_role:
        return await ctx.reply(embed=embed_err("Son rôle est trop haut pour moi."))
    roles = [r for r in member.roles if r != ctx.guild.default_role and r < ctx.guild.me.top_role]
    if not roles:
        return await ctx.reply(embed=embed_warn(f"{member.mention} n'a aucun rôle à retirer."))
    roles_txt = "  ".join(r.mention for r in roles)
    await member.remove_roles(*roles, reason=f"Derank par {ctx.author}  {reason}")
    e = discord.Embed(
        title="🔨  Derank exécuté",
        color=C["orange"],
        timestamp=datetime.utcnow(),
    )
    e.set_author(name=member.display_name, icon_url=member.display_avatar.url)
    e.set_thumbnail(url=member.display_avatar.url)
    e.add_field(name="Membre", value=member.mention,     inline=True)
    e.add_field(name="Par",    value=ctx.author.mention, inline=True)
    e.add_field(name="Raison", value=f"*{reason}*",      inline=False)
    footer(e, ctx.author)
    await ctx.reply(embed=e)
    asyncio.create_task(send_log(
        ctx.guild, ctx.author, "derank", "Derank exécuté",
        [("⌨️ Commande", "`&derank`"), ("⚠️ Raison", f"*{reason}*", False), ("🎭 Rôles", roles_txt, False)],
        target=member,
    ))
    try:
        dm = discord.Embed(
            title="⚠️  Tu as été derank",
            description=f"Tous tes rôles ont été retirés sur **{ctx.guild.name}**.\n\n> *{reason}*",
            color=C["orange"], timestamp=datetime.utcnow(),
        )
        footer(dm)
        await member.send(embed=dm)
    except Exception:
        pass

# ══════════════════════════════════════════════════════════════════════
#  /addrole  /removerole
# ══════════════════════════════════════════════════════════════════════
@tree.command(name="addrole", description="Ajouter un rôle à un membre ou à tout le serveur (Sys+)")
@app_commands.describe(role="Le rôle à ajouter", tous="Ajouter à tous les membres ?", membre="Le membre cible")
async def addrole_slash(i: discord.Interaction, role: discord.Role, tous: bool, membre: discord.Member = None):
    if not is_sys_plus(i.user.id):
        return
    if role >= i.guild.me.top_role:
        return await i.response.send_message(embed=embed_err("Ce rôle est trop haut pour moi."), ephemeral=True)
    if tous:
        await i.response.defer(thinking=True)
        targets = [m for m in i.guild.members if not m.bot and role not in m.roles]
        ok, fail = 0, 0
        for m in targets:
            try:
                await m.add_roles(role, reason=f"/addrole tous  {i.user}")
                ok += 1
            except Exception:
                fail += 1
        e = discord.Embed(title="✦  Rôle ajouté  ·  Serveur entier", color=C["ok"], timestamp=datetime.utcnow())
        e.add_field(name="Rôle",   value=role.mention, inline=True)
        e.add_field(name="✅ OK",  value=f"`{ok}`",    inline=True)
        e.add_field(name="❌ KO",  value=f"`{fail}`",  inline=True)
        footer(e, i.user)
        await i.followup.send(embed=e)
        asyncio.create_task(send_log(
            i.guild, i.user, "addrole", "Rôle ajouté  Serveur entier",
            [("⌨️ Commande", "`/addrole`"), ("🎭 Rôle", role.mention), ("✅", f"`{ok}`"), ("❌", f"`{fail}`")],
        ))
    else:
        if not membre:
            return await i.response.send_message(embed=embed_err("Précise un membre ou active **tous**."), ephemeral=True)
        if not await protection_check_i(i, membre):
            return
        if role in membre.roles:
            return await i.response.send_message(embed=embed_warn(f"{membre.mention} a déjà ce rôle."), ephemeral=True)
        try:
            await membre.add_roles(role, reason=f"/addrole  {i.user}")
            e = embed_ok(title="Rôle ajouté")
            e.add_field(name="Membre", value=membre.mention, inline=True)
            e.add_field(name="Rôle",   value=role.mention,   inline=True)
            footer(e, i.user)
            await i.response.send_message(embed=e)
            asyncio.create_task(send_log(
                i.guild, i.user, "addrole", "Rôle ajouté",
                [("⌨️ Commande", "`/addrole`"), ("🎭 Rôle", role.mention)],
                target=membre,
            ))
        except discord.Forbidden:
            await i.response.send_message(embed=embed_err("Impossible d'ajouter ce rôle."), ephemeral=True)


@tree.command(name="removerole", description="Retirer un rôle à un membre ou à tout le serveur (Sys+)")
@app_commands.describe(role="Le rôle à retirer", tous="Retirer à tous les membres ?", membre="Le membre cible")
async def removerole_slash(i: discord.Interaction, role: discord.Role, tous: bool, membre: discord.Member = None):
    if not is_sys_plus(i.user.id):
        return
    if role >= i.guild.me.top_role:
        return await i.response.send_message(embed=embed_err("Ce rôle est trop haut pour moi."), ephemeral=True)
    if tous:
        await i.response.defer(thinking=True)
        targets = [m for m in i.guild.members if not m.bot and role in m.roles]
        ok, fail = 0, 0
        for m in targets:
            try:
                await m.remove_roles(role, reason=f"/removerole tous  {i.user}")
                ok += 1
            except Exception:
                fail += 1
        e = discord.Embed(title="✦  Rôle retiré  ·  Serveur entier", color=C["orange"], timestamp=datetime.utcnow())
        e.add_field(name="Rôle",   value=role.mention, inline=True)
        e.add_field(name="✅ OK",  value=f"`{ok}`",    inline=True)
        e.add_field(name="❌ KO",  value=f"`{fail}`",  inline=True)
        footer(e, i.user)
        await i.followup.send(embed=e)
        asyncio.create_task(send_log(
            i.guild, i.user, "removerole", "Rôle retiré  Serveur entier",
            [("⌨️ Commande", "`/removerole`"), ("🎭 Rôle", role.mention), ("✅", f"`{ok}`"), ("❌", f"`{fail}`")],
        ))
    else:
        if not membre:
            return await i.response.send_message(embed=embed_err("Précise un membre ou active **tous**."), ephemeral=True)
        if not await protection_check_i(i, membre):
            return
        if role not in membre.roles:
            return await i.response.send_message(embed=embed_warn(f"{membre.mention} n'a pas ce rôle."), ephemeral=True)
        try:
            await membre.remove_roles(role, reason=f"/removerole  {i.user}")
            e = discord.Embed(title="✦  Rôle retiré", color=C["orange"], timestamp=datetime.utcnow())
            e.add_field(name="Membre", value=membre.mention, inline=True)
            e.add_field(name="Rôle",   value=role.mention,   inline=True)
            footer(e, i.user)
            await i.response.send_message(embed=e)
            asyncio.create_task(send_log(
                i.guild, i.user, "removerole", "Rôle retiré",
                [("⌨️ Commande", "`/removerole`"), ("🎭 Rôle", role.mention)],
                target=membre,
            ))
        except discord.Forbidden:
            await i.response.send_message(embed=embed_err("Impossible de retirer ce rôle."), ephemeral=True)

# ══════════════════════════════════════════════════════════════════════
#  COMMANDES VOICEVIP  (=)
# ══════════════════════════════════════════════════════════════════════
@bot.command(name="laisse")
@check_server()
async def laisse_cmd(ctx, member: discord.Member = None):
    if not member:
        return await ctx.reply(embed=embed_err("Usage : `=laisse @membre`"))
    if not await protection_check(ctx, member):
        return
    oid = ctx.author.id
    if oid in laisse_active and laisse_active[oid][0] == member.id:
        _, nn, on = laisse_active.pop(oid)
        try:
            await member.edit(nick=on)
        except Exception:
            pass
        e = embed_warn(f"Laisse retirée à {member.mention}.")
        footer(e, ctx.author)
        await ctx.reply(embed=e)
        asyncio.create_task(send_log(
            ctx.guild, ctx.author, "laisse", "Laisse retirée",
            [("⌨️ Commande", "`=laisse`"), ("📝 Pseudo restauré", f"`{on}`")],
            target=member,
        ))
        return
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
    footer(e, ctx.author)
    await ctx.reply(embed=e)
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
        private_vocs.pop(cid)
        pv_access.pop(cid, None)
        e = embed_ok("Vocal rendue **publique**.")
        footer(e, ctx.author)
        await ctx.reply(embed=e)
        asyncio.create_task(send_log(
            ctx.guild, ctx.author, "pv", "Vocal rendue publique",
            [("⌨️ Commande", "`=pv`"), ("🔊 Salon", f"`{ch.name}`")],
        ))
        return
    user_pvs = [c for c, info in private_vocs.items() if info["owner"] == ctx.author.id]
    max_pvs  = 99 if is_sys_plus(ctx.author.id) else 2
    if len(user_pvs) >= max_pvs:
        return await ctx.reply(embed=embed_err(f"Tu as déjà **{max_pvs}** vocal(s) privée(s) max."))
    pv_type = "sysplus" if is_sys_plus(ctx.author.id) else ("sys" if has_wl_sys(ctx.author.id) else "normal")
    private_vocs[cid] = {"owner": ctx.author.id, "type": pv_type}
    pv_access[cid]    = set()
    labels = {"normal": "normale", "sys": "Sys", "sysplus": "Sys+"}
    e = discord.Embed(
        title=f"🔒  Vocal privée  [{labels[pv_type]}]",
        description=f"**{ch.name}** est maintenant privée.",
        color=C["purple"], timestamp=datetime.utcnow(),
    )
    footer(e, ctx.author)
    await ctx.reply(embed=e)
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
        e = embed_warn(f"Accès retiré à **{member.display_name}**.")
        footer(e, ctx.author)
        await ctx.reply(embed=e)
        asyncio.create_task(send_log(
            ctx.guild, ctx.author, "acces", "Accès PV retiré",
            [("⌨️ Commande", "`=acces`"), ("🔊 Vocal", f"`{ctx.author.voice.channel.name}`")],
            target=member,
        ))
        return
    acc.add(member.id)
    e = embed_ok(f"**{member.display_name}** peut rejoindre ta vocal privée.")
    footer(e, ctx.author)
    await ctx.reply(embed=e)
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
    if not await protection_check(ctx, member):
        return
    if not member.voice:
        return await ctx.reply(embed=embed_err("Cette personne n'est pas en vocal."))
    if not ctx.author.voice:
        return await ctx.reply(embed=embed_err("Tu n'es pas en vocal."))
    ch_name = member.voice.channel.name
    try:
        await ctx.author.move_to(member.voice.channel)
        e = embed_ok(f"Rejoint **{ch_name}**.")
        footer(e, ctx.author)
        await ctx.reply(embed=e)
        asyncio.create_task(send_log(
            ctx.guild, ctx.author, "join", "Join vocal",
            [("⌨️ Commande", "`=join`"), ("🔊 Salon", f"`{ch_name}`")],
            target=member,
        ))
    except discord.Forbidden:
        await ctx.reply(embed=embed_err("Impossible de te déplacer."))


@bot.command(name="mv")
@check_voicevip()
async def mv_cmd(ctx, member: discord.Member = None, channel: discord.VoiceChannel = None):
    if not member or not channel:
        return await ctx.reply(embed=embed_err("Usage : `=mv @membre #vocal`"))
    if not await protection_check(ctx, member):
        return
    try:
        await member.move_to(channel)
        e = embed_ok(f"**{member.display_name}** déplacé dans **{channel.name}**.")
        footer(e, ctx.author)
        await ctx.reply(embed=e)
        asyncio.create_task(send_log(
            ctx.guild, ctx.author, "mv", "Move vocal",
            [("⌨️ Commande", "`=mv`"), ("🔊 Destination", f"`{channel.name}`")],
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
        ch  = ctx.guild.get_channel(cid)
        ow  = ctx.guild.get_member(info["owner"])
        acc = [ctx.guild.get_member(u) for u in pv_access.get(cid, set())]
        acc_str = "  ".join(m.display_name for m in acc if m) or "*Personne*"
        e.add_field(
            name=f"#{ch.name if ch else cid}  [{info['type']}]",
            value=f"Owner : {ow.mention if ow else info['owner']}\nAccès : {acc_str}",
            inline=False,
        )
    footer(e, ctx.author)
    await ctx.reply(embed=e)


@bot.command(name="menotte")
@check_voicevip()
async def menotte_cmd(ctx, member: discord.Member = None):
    if not member:
        return await ctx.reply(embed=embed_err("Usage : `=menotte @membre`"))
    if not await protection_check(ctx, member):
        return
    oid = ctx.author.id
    now = time.time()
    if oid in menotte_active and menotte_active[oid][0] == member.id:
        menotte_active.pop(oid)
        e = embed_warn(f"Menotte retirée à {member.mention}.")
        footer(e, ctx.author)
        await ctx.reply(embed=e)
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
    ch_id   = member.voice.channel.id
    ch_name = member.voice.channel.name
    menotte_active[oid] = (member.id, ch_id)
    menotte_cd[oid]     = now
    e = discord.Embed(
        title="⛓️  Menotte posée",
        description=f"{member.mention} est menotté dans **{ch_name}**.",
        color=C["navy"], timestamp=datetime.utcnow(),
    )
    footer(e, ctx.author)
    await ctx.reply(embed=e)
    asyncio.create_task(send_log(
        ctx.guild, ctx.author, "menotte", "Menotte posée",
        [("⌨️ Commande", "`=menotte`"), ("🔊 Salon", f"`{ch_name}`")],
        target=member,
    ))

# ══════════════════════════════════════════════════════════════════════
#  COMMANDES WL SYS  (=)
# ══════════════════════════════════════════════════════════════════════
@bot.command(name="follow")
@check_wl_sys()
async def follow_cmd(ctx, member: discord.Member = None):
    if not member:
        return await ctx.reply(embed=embed_err("Usage : `=follow @membre`"))
    if not await protection_check(ctx, member):
        return
    if ctx.author.id in follow_active and follow_active[ctx.author.id] == member.id:
        follow_active.pop(ctx.author.id)
        e = embed_warn(f"Follow sur **{member.display_name}** retiré.")
        footer(e, ctx.author)
        await ctx.reply(embed=e)
        asyncio.create_task(send_log(
            ctx.guild, ctx.author, "follow", "Follow retiré",
            [("⌨️ Commande", "`=follow`")],
            target=member,
        ))
        return
    follow_active[ctx.author.id] = member.id
    e = embed_ok(f"Tu suis maintenant **{member.display_name}** en vocal. 🏃")
    footer(e, ctx.author)
    await ctx.reply(embed=e)
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
    cid = ctx.author.voice.channel.id
    ch  = ctx.author.voice.channel
    if cid in private_vocs and private_vocs[cid]["owner"] == ctx.author.id:
        private_vocs.pop(cid)
        pv_access.pop(cid, None)
        e = embed_ok("PV Sys désactivée, vocal publique.")
        footer(e, ctx.author)
        await ctx.reply(embed=e)
        asyncio.create_task(send_log(
            ctx.guild, ctx.author, "pvsys", "PV Sys désactivée",
            [("⌨️ Commande", "`=pvsys`"), ("🔊 Salon", f"`{ch.name}`")],
        ))
        return
    user_pvs = [c for c, info in private_vocs.items() if info["owner"] == ctx.author.id]
    if len(user_pvs) >= 2 and not is_sys_plus(ctx.author.id):
        return await ctx.reply(embed=embed_err("Maximum **2** vocaux privés."))
    private_vocs[cid] = {"owner": ctx.author.id, "type": "sys"}
    pv_access[cid]    = set()
    e = discord.Embed(
        title="🔒  Vocal privée Sys",
        description=f"**{ch.name}** est maintenant en PV Sys.",
        color=C["navy"], timestamp=datetime.utcnow(),
    )
    footer(e, ctx.author)
    await ctx.reply(embed=e)
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
        return
    if not member or not message:
        return await ctx.reply(embed=embed_err("Usage : `=mp @membre message`"))
    if not await protection_check(ctx, member):
        return
    try:
        await member.send(message)
        e = embed_ok(f"Message envoyé anonymement à {member.mention}.")
        footer(e, ctx.author)
        await ctx.reply(embed=e)
        asyncio.create_task(send_log(
            ctx.guild, ctx.author, "mp", "MP anonyme envoyé",
            [("⌨️ Commande", "`=mp`"), ("✉️ Message", f"```{message[:200]}```", False)],
            target=member,
        ))
    except discord.Forbidden:
        await ctx.reply(embed=embed_err("Impossible d'envoyer le MP (DMs fermés)."))


@tree.command(name="dog-add", description="Dog quelqu'un  ·  il te suit en vocal (Server WL)")
@app_commands.describe(membre="La personne à dog")
async def dog_add(i: discord.Interaction, membre: discord.Member):
    if maintenance and not is_sys_plus(i.user.id):
        return await i.response.send_message(embed=embed_warn("Maintenance."), ephemeral=True)
    if not has_server(i.user.id):
        return
    if not await protection_check_i(i, membre):
        return
    oid = i.user.id
    now = time.time()
    if oid in dog_active and dog_active[oid][0] == membre.id:
        return await i.response.send_message(embed=embed_warn("Cette personne est déjà ton dog."), ephemeral=True)
    if oid in dog_active:
        return await i.response.send_message(embed=embed_err("Tu as déjà un dog actif."), ephemeral=True)
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
    footer(e, i.user)
    await i.response.send_message(embed=e)
    asyncio.create_task(send_log(
        i.guild, i.user, "dog", "Dog activé",
        [("⌨️ Commande", "`/dog-add`"), ("📝 Nouveau pseudo", f"`{new}`"), ("📝 Ancien pseudo", f"`{old}`")],
        target=membre,
    ))


@tree.command(name="dog-del", description="Retirer le dog actif (Server WL)")
async def dog_del(i: discord.Interaction):
    if maintenance and not is_sys_plus(i.user.id):
        return await i.response.send_message(embed=embed_warn("Maintenance."), ephemeral=True)
    if not has_server(i.user.id):
        return
    if i.user.id not in dog_active:
        return await i.response.send_message(embed=embed_err("Tu n'as pas de dog actif."), ephemeral=True)
    cid, new, old = dog_active.pop(i.user.id)
    m = i.guild.get_member(cid)
    if m:
        try:
            await m.edit(nick=old)
        except Exception:
            pass
    e = embed_warn("Dog retiré avec succès.")
    footer(e, i.user)
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
    spam_msg = (
        f"{target.mention} {custom_msg}"
        if custom_msg
        else f"Reveille toi {target.mention} ! C'est {invoker.mention} qui te l'ordonne 😈"
    )
    wakeup_active.add(target.id)
    wakeup_cd[invoker.id] = time.time()
    vcs   = list(guild.voice_channels)
    delay = max(0.1, 1.0 / 3)

    async def _spam():
        for _ in range(duration * 3):
            if target.id not in wakeup_active:
                break
            try:
                await target.send(spam_msg)
            except Exception:
                pass
            await asyncio.sleep(delay)

    asyncio.create_task(_spam())
    end = asyncio.get_event_loop().time() + duration
    while asyncio.get_event_loop().time() < end:
        if target.voice and vcs:
            try:
                await target.move_to(random.choice(vcs))
            except Exception:
                pass
        await asyncio.sleep(0.2)
    try:
        await target.move_to(None)
    except Exception:
        pass
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
        self.target     = target
        self.invoker    = invoker
        self.custom_msg = custom_msg

    async def callback(self, i):
        if self.values[0] == "custom":
            return await i.response.send_modal(
                WakeupCustomDurationModal(self.target, self.invoker, self.custom_msg)
            )
        duration = int(self.values[0])
        await i.response.defer(ephemeral=True)
        e = discord.Embed(
            title="😈  Wakeup lancé !",
            description=f"**Cible :** {self.target.mention}\n**Durée :** `{duration}s`",
            color=C["rose"], timestamp=datetime.utcnow(),
        )
        footer(e, self.invoker)
        await i.followup.send(embed=e, ephemeral=True)
        asyncio.create_task(_run_wakeup(i.guild, self.target, self.invoker, self.custom_msg, duration))
        asyncio.create_task(send_log(
            i.guild, self.invoker, "wakeup", "Wakeup lancé",
            [("⌨️ Commande", "`/wakeup`"), ("⏱️ Durée", f"`{duration}s`"), ("✉️ Message", f"`{self.custom_msg}`" if self.custom_msg else "*Aucun*")],
            target=self.target,
        ))


class WakeupDurationView(discord.ui.View):
    def __init__(self, target, invoker, custom_msg):
        super().__init__(timeout=30)
        self.add_item(WakeupDurationSelect(target, invoker, custom_msg))


class WakeupCustomDurationModal(discord.ui.Modal, title="Durée personnalisée"):
    duree = discord.ui.TextInput(label="Durée en secondes", placeholder="5  600", max_length=4, required=True)

    def __init__(self, target, invoker, custom_msg):
        super().__init__()
        self.target     = target
        self.invoker    = invoker
        self.custom_msg = custom_msg

    async def on_submit(self, i):
        try:
            duration = int(self.duree.value.strip())
            if not 5 <= duration <= 600:
                raise ValueError
        except ValueError:
            return await i.response.send_message(embed=embed_err("Durée invalide (5-600s)."), ephemeral=True)
        await i.response.defer(ephemeral=True)
        e = discord.Embed(
            title="😈  Wakeup lancé !",
            description=f"**Cible :** {self.target.mention}\n**Durée :** `{duration}s`",
            color=C["rose"], timestamp=datetime.utcnow(),
        )
        footer(e, self.invoker)
        await i.followup.send(embed=e, ephemeral=True)
        asyncio.create_task(_run_wakeup(i.guild, self.target, self.invoker, self.custom_msg, duration))
        asyncio.create_task(send_log(
            i.guild, self.invoker, "wakeup", "Wakeup lancé (custom)",
            [("⌨️ Commande", "`/wakeup`"), ("⏱️ Durée", f"`{duration}s`"), ("✉️ Message", f"`{self.custom_msg}`" if self.custom_msg else "*Aucun*")],
            target=self.target,
        ))


class WakeupModal(discord.ui.Modal, title="Wakeup"):
    message = discord.ui.TextInput(label="Message personnalisé (optionnel)", required=False, max_length=200)

    def __init__(self, target, invoker):
        super().__init__()
        self.target  = target
        self.invoker = invoker

    async def on_submit(self, i):
        if not await protection_check_i(i, self.target):
            return
        now = time.time()
        if not is_sys_plus(self.invoker.id):
            last = wakeup_cd.get(self.invoker.id, 0)
            if now - last < 300:
                return await i.response.send_message(
                    embed=embed_warn(f"Cooldown : encore **{int(300-(now-last))}s**."), ephemeral=True
                )
        if self.target.id in wakeup_active:
            return await i.response.send_message(embed=embed_err("Déjà en wakeup."), ephemeral=True)
        custom = self.message.value.strip()
        if is_sys_plus(self.invoker.id):
            e = embed_sys(title="Wakeup Sys+  ·  Durée", desc=f"**Cible :** {self.target.mention}\nChoisis la durée.")
            footer(e, self.invoker)
            await i.response.send_message(embed=e, view=WakeupDurationView(self.target, self.invoker, custom), ephemeral=True)
        else:
            await i.response.defer(ephemeral=True)
            await i.followup.send(embed=embed_ok(f"Wakeup lancé sur {self.target.mention} !"), ephemeral=True)
            asyncio.create_task(_run_wakeup(i.guild, self.target, self.invoker, custom, 10))
            asyncio.create_task(send_log(
                i.guild, self.invoker, "wakeup", "Wakeup lancé",
                [("⌨️ Commande", "`/wakeup`"), ("⏱️ Durée", "`10s` (fixe)"), ("✉️ Message", f"`{custom}`" if custom else "*Aucun*")],
                target=self.target,
            ))


@tree.command(name="wakeup", description="Wakeup un membre (Server WL)")
@app_commands.describe(membre="Le membre à wakeup")
async def wakeup_slash(i, membre: discord.Member):
    if maintenance and not is_sys_plus(i.user.id):
        return await i.response.send_message(embed=embed_warn("Maintenance."), ephemeral=True)
    if not has_server(i.user.id):
        return
    await i.response.send_modal(WakeupModal(membre, i.user))

# ══════════════════════════════════════════════════════════════════════
#  /snap
# ══════════════════════════════════════════════════════════════════════
class SnapResponseModal(discord.ui.Modal, title="Donner mon Snapchat"):
    snap = discord.ui.TextInput(label="Ton Snapchat", placeholder="ton_snap", max_length=50)

    def __init__(self, demandeur: discord.Member, view: "SnapView"):
        super().__init__()
        self.demandeur    = demandeur
        self._parent_view = view

    async def on_submit(self, i: discord.Interaction):
        e = discord.Embed(title="📸  Snap reçu !", color=C["gold"], timestamp=datetime.utcnow())
        e.add_field(name="De",       value=i.user.mention)
        e.add_field(name="Snapchat", value=f"`{self.snap.value}`")
        e.set_thumbnail(url=i.user.display_avatar.url)
        footer(e)
        try:
            await self.demandeur.send(embed=e)
            await i.response.send_message(embed=embed_ok("Snap envoyé ! 📸"), ephemeral=True)
            self._parent_view.disable_all()
            try:
                await self._parent_view.message.edit(view=self._parent_view)
            except Exception:
                pass
            asyncio.create_task(send_log(
                self._parent_view.guild, i.user, "snap_give", "Snap partagé",
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
    async def give_snap(self, i: discord.Interaction, b):
        await i.response.send_modal(SnapResponseModal(self.demandeur, self))

    @discord.ui.button(label="❌  Refuser", style=discord.ButtonStyle.red, custom_id="snap_refuse")
    async def refuse_snap(self, i: discord.Interaction, b):
        try:
            e = discord.Embed(
                title="💀  Snap refusé",
                description=f"La honte, il/elle a refusé ton Snap. 😂💀\n*(refus de **{i.user.display_name}**)*",
                color=C["error"], timestamp=datetime.utcnow(),
            )
            footer(e)
            await self.demandeur.send(embed=e)
        except Exception:
            pass
        await i.response.send_message(embed=embed_ok("Refus envoyé."), ephemeral=True)
        self.disable_all()
        try:
            await self.message.edit(view=self)
        except Exception:
            pass
        asyncio.create_task(send_log(
            self.guild, i.user, "snap_refuse", "Snap refusé",
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
        return
    e = discord.Embed(title="📸  Quelqu'un veut ton Snap !", color=C["gold"], timestamp=datetime.utcnow())
    e.set_author(name=i.user.display_name, icon_url=i.user.display_avatar.url)
    if message:
        e.add_field(name="Message", value=f"*{message}*", inline=False)
    e.set_footer(text="Clique pour partager ton snap  ·  ou refuse directement.")
    view = SnapView(i.user, i.guild)
    try:
        sent = await membre.send(embed=e, view=view)
        view.message = sent
        await i.response.send_message(embed=embed_ok(f"Demande envoyée à {membre.mention} ! 📨"), ephemeral=True)
        asyncio.create_task(send_log(
            i.guild, i.user, "snap", "Snap demandé",
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
        return
    if not await protection_check_i(i, membre):
        return
    if membre.id in locked_nicks:
        locked_nicks.discard(membre.id)
        try:
            await membre.edit(nick=None)
        except Exception:
            pass
        e = embed_warn(f"Pseudo de {membre.mention} déverrouillé.")
        footer(e, i.user)
        await i.response.send_message(embed=e)
        asyncio.create_task(send_log(
            i.guild, i.user, "tipeu", "Tipeu retiré",
            [("⌨️ Commande", "`/tipeu`")],
            target=membre,
        ))
        return
    try:
        old_nick = membre.display_name
        await membre.edit(nick="S")
        locked_nicks.add(membre.id)
        e = discord.Embed(
            title="🔒  Pseudo verrouillé",
            description=f"{membre.mention} renommé **S** et verrouillé.",
            color=C["navy"], timestamp=datetime.utcnow(),
        )
        footer(e, i.user)
        await i.response.send_message(embed=e)
        asyncio.create_task(send_log(
            i.guild, i.user, "tipeu", "Tipeu activé",
            [("⌨️ Commande", "`/tipeu`"), ("📝 Ancien pseudo", f"`{old_nick}`"), ("📝 Nouveau pseudo", "`S`")],
            target=membre,
        ))
    except discord.Forbidden:
        await i.response.send_message(embed=embed_err("Impossible de changer son pseudo."), ephemeral=True)

# ══════════════════════════════════════════════════════════════════════
#  LIBERTÉ  (accessibles à tous)
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
    platform_str = "  ".join(platforms) or "*hors ligne*"

    activity_str = "*Aucune*"
    if member.activities:
        for act in member.activities:
            if isinstance(act, discord.Spotify):
                activity_str = f"🎵 **{act.title}**  ·  {act.artist}"
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

    embed_color = member.color if member.color.value else discord.Color(C["dark"])

    e = discord.Embed(color=embed_color, timestamp=datetime.utcnow())
    e.set_author(name=member.display_name, icon_url=member.display_avatar.url)
    e.set_thumbnail(url=member.display_avatar.url)

    e.add_field(name="👤  Compte",      value=f"`@{member.name}`  ·  `{member.id}`", inline=False)
    e.add_field(
        name="📋  Infos",
        value=(
            f"**Surnom :** {member.display_name}\n"
            f"**Mention :** {member.mention}\n"
            f"**Bot :** {'Oui' if member.bot else 'Non'}"
        ),
        inline=True,
    )
    e.add_field(
        name="📡  Statut",
        value=(
            f"**État :** {status_icon} {status_label}\n"
            f"**Plateforme :** {platform_str}\n"
            f"**Activité :** {activity_str}"
        ),
        inline=True,
    )
    e.add_field(name="\u200b", value="\u200b", inline=False)
    e.add_field(name="🎙️  Vocal",       value=voice_str, inline=False)
    dates_val = f"**Créé :** <t:{created_ts}:D>  ·  <t:{created_ts}:R>\n"
    if joined_ts:
        dates_val += f"**Rejoint :** <t:{joined_ts}:D>  ·  <t:{joined_ts}:R>"
    e.add_field(name="📅  Dates",        value=dates_val, inline=False)
    e.add_field(name=f"🏷️  Rôles  [{len(roles)}]", value=roles_str, inline=False)

    footer(e, ctx.author)
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
        msg = await ctx.send(embed=embed_warn("Aucun message supprimé récemment dans ce salon."))
        await asyncio.sleep(3)
        try:
            await msg.delete()
        except Exception:
            pass
        return
    deleted_ts = int(data["deleted_at"].timestamp())
    e = discord.Embed(
        description=f">>> {data['content']}",
        color=C["dark"],
        timestamp=datetime.utcnow(),
    )
    e.set_author(name=data["author"], icon_url=data["author_icon"])
    e.set_footer(text=f"🗑️  Supprimé  ·  {datetime.utcfromtimestamp(deleted_ts).strftime('%H:%M:%S')}")
    msg = await ctx.send(embed=e)
    await asyncio.sleep(3)
    try:
        await msg.delete()
    except Exception:
        pass

# ══════════════════════════════════════════════════════════════════════
#  &help
# ══════════════════════════════════════════════════════════════════════
@bot.command(name="help")
async def help_cmd(ctx):
    e = discord.Embed(
        title="⬡  Commandes disponibles",
        color=C["dark"],
        timestamp=datetime.utcnow(),
    )
    if maintenance:
        e.description = "> 🔴 **Maintenance active.**  Seuls les Sys+ ont accès."

    if is_sys_plus(ctx.author.id):
        e.add_field(
            name="⭐  Sys+  [ & ]",
            value=(
                "`&wl`  `&wlpanel`  `&restartpanel`  `&maintenance`\n"
                "`&clear`  `&derank`  `&lock`  `&renew`  `&dmall`\n"
                "`/addrole`  `/removerole`\n"
                "*· toutes les commandes `=` et `/`*"
            ),
            inline=False,
        )
    if has_wl_sys(ctx.author.id):
        e.add_field(
            name="⚡  WL Sys  [ = ]",
            value="`=follow`  `=pvsys`  *· + toutes les commandes VoiceVIP*",
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
    footer(e, ctx.author)
    await ctx.reply(embed=e)

# ══════════════════════════════════════════════════════════════════════
#  &lock  (performances : gather pour toutes les permissions)
# ══════════════════════════════════════════════════════════════════════
@bot.command(name="lock")
@check_sys_plus()
async def lock_cmd(ctx, channel: discord.TextChannel = None):
    channel  = channel or ctx.channel
    everyone = ctx.guild.default_role
    civil    = ctx.guild.get_role(CIVIL_ROLE_ID)

    if channel.id in locked_channels:
        # ── Déverrouillage en parallèle ──
        saved = locked_channels.pop(channel.id)
        tasks = []
        for target, ow in saved.items():
            if ow is None:
                tasks.append(channel.set_permissions(target, overwrite=None))
            else:
                tasks.append(channel.set_permissions(target, overwrite=ow))
        await asyncio.gather(*tasks, return_exceptions=True)

        e = embed_ok(title="Salon déverrouillé", desc=f"{channel.mention} est de nouveau accessible à tous.")
        footer(e, ctx.author)
        await ctx.reply(embed=e)
        asyncio.create_task(send_log(
            ctx.guild, ctx.author, "lock", "Salon déverrouillé",
            [("⌨️ Commande", "`&lock`"), ("📌 Salon", channel.mention)],
        ))
        return

    # ── Verrouillage ──
    saved_overwrites = {}
    blocked_roles    = {everyone}
    if civil:
        blocked_roles.add(civil)

    # Sauvegarder les cibles existantes (hors @everyone, civil, bots)
    perm_tasks   = []
    perm_targets = []
    for target in list(channel.overwrites.keys()):
        if target in blocked_roles:
            continue
        if isinstance(target, discord.Member) and target.bot:
            continue
        if isinstance(target, discord.Role) and target.managed:
            continue
        current_ow = channel.overwrites_for(target)
        saved_overwrites[target] = current_ow if not current_ow.is_empty() else None
        new_ow = (
            discord.PermissionOverwrite.from_pair(current_ow.pair()[0], current_ow.pair()[1])
            if not current_ow.is_empty()
            else discord.PermissionOverwrite()
        )
        new_ow.send_messages            = False
        new_ow.send_messages_in_threads = False
        new_ow.create_public_threads    = False
        new_ow.create_private_threads   = False
        new_ow.add_reactions            = False
        new_ow.use_application_commands = False
        perm_tasks.append(channel.set_permissions(target, overwrite=new_ow))

    # Sauvegarder @everyone et civil
    for role in [everyone, civil]:
        if role is None:
            continue
        current_ow = channel.overwrites_for(role)
        saved_overwrites[role] = current_ow if not current_ow.is_empty() else None

    locked_channels[channel.id] = saved_overwrites

    # Verrou sur @everyone et civil
    lock_ow = discord.PermissionOverwrite(
        send_messages=False,
        send_messages_in_threads=False,
        create_public_threads=False,
        create_private_threads=False,
        add_reactions=False,
        use_application_commands=False,
    )
    for role in [everyone, civil]:
        if role:
            perm_tasks.append(channel.set_permissions(role, overwrite=lock_ow))

    # Autoriser Sys+ et WL Sys
    allowed_uids = set(SYS_PLUS_IDS)
    for uid, wls in whitelisted.items():
        if "sys" in wls:
            allowed_uids.add(uid)
    unlock_ow = discord.PermissionOverwrite(
        send_messages=True,
        send_messages_in_threads=True,
        create_public_threads=True,
        create_private_threads=True,
        add_reactions=True,
        use_application_commands=True,
    )
    for uid in allowed_uids:
        m = ctx.guild.get_member(uid)
        if m:
            perm_tasks.append(channel.set_permissions(m, overwrite=unlock_ow))

    # Tout en parallèle
    await asyncio.gather(*perm_tasks, return_exceptions=True)

    e = discord.Embed(
        title="🔐  Salon verrouillé",
        description=(
            f"{channel.mention} est désormais **en lecture seule**.\n"
            "Seuls les **Sys+** et **WL Sys** peuvent écrire.\n\n"
            "Refais `&lock` pour déverrouiller."
        ),
        color=C["maint"], timestamp=datetime.utcnow(),
    )
    footer(e, ctx.author)
    await ctx.reply(embed=e)
    asyncio.create_task(send_log(
        ctx.guild, ctx.author, "lock", "Salon verrouillé",
        [("⌨️ Commande", "`&lock`"), ("📌 Salon", channel.mention)],
    ))
    if channel != ctx.channel:
        try:
            await channel.send(embed=discord.Embed(
                description="🔐  Ce salon est **en lecture seule**  ·  seuls les Sys+ peuvent écrire.",
                color=C["maint"],
            ))
        except Exception:
            pass

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

    await channel.delete(reason=f"&renew  {ctx.author}")
    new_ch = await ctx.guild.create_text_channel(
        name=name, topic=topic, category=category,
        slowmode_delay=slowmode, nsfw=nsfw, overwrites=overwrites,
        reason=f"&renew  {ctx.author}",
    )
    try:
        await new_ch.edit(position=position)
    except Exception:
        pass
    e = embed_ok(title="Salon renouvelé", desc=f"{new_ch.mention} a été recréé proprement.")
    footer(e, ctx.author)
    await new_ch.send(embed=e)
    asyncio.create_task(send_log(
        ctx.guild, ctx.author, "renew", "Salon renouvelé",
        [("⌨️ Commande", "`&renew`"), ("📌 Salon", f"`#{name}`"), ("📂 Catégorie", f"`{category.name if category else 'Aucune'}`")],
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
            "> `{user}` dans le message  ·  remplacé par le ping du destinataire\n"
            "> Ajoute un **ID de rôle** à la fin pour cibler uniquement ses membres"
        ))

    role_filter: discord.Role | None = None
    words = message.split()
    if words and words[-1].isdigit() and len(words[-1]) >= 17:
        role_filter = ctx.guild.get_role(int(words[-1]))
        if role_filter:
            message = " ".join(words[:-1]).strip()

    members = (
        [m for m in role_filter.members if not m.bot]
        if role_filter
        else [m for m in ctx.guild.members if not m.bot]
    )
    scope_txt = f"les membres avec le rôle {role_filter.mention}" if role_filter else "tous les membres"

    if not members:
        return await ctx.reply(embed=embed_warn("Aucun membre trouvé."))

    preview = message.replace("{user}", members[0].mention if members else "@quelqu'un")

    confirm_e = discord.Embed(
        title="📨  Confirmer l'envoi",
        description=(
            f"Tu vas envoyer un DM à **{len(members)}** membres ({scope_txt}).\n\n"
            f"**Message :**\n> {message[:300]}\n\n"
            f"**Aperçu :**\n> {preview[:300]}"
        ),
        color=C["warn"], timestamp=datetime.utcnow(),
    )
    if role_filter:
        confirm_e.add_field(name="🎭 Rôle ciblé", value=role_filter.mention)
    footer(confirm_e, ctx.author)

    class ConfirmView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=30)
            self.confirmed = False

        @discord.ui.button(label="✅ Confirmer", style=discord.ButtonStyle.green)
        async def confirm(self, interaction, button):
            if interaction.user.id != ctx.author.id:
                return await interaction.response.send_message(embed=embed_err("Ce n'est pas ton panel."), ephemeral=True)
            self.confirmed = True
            for item in self.children:
                item.disabled = True
            await interaction.response.edit_message(view=self)
            self.stop()

        @discord.ui.button(label="❌ Annuler", style=discord.ButtonStyle.red)
        async def cancel(self, interaction, button):
            if interaction.user.id != ctx.author.id:
                return await interaction.response.send_message(embed=embed_err("Ce n'est pas ton panel."), ephemeral=True)
            for item in self.children:
                item.disabled = True
            await interaction.response.edit_message(view=self)
            self.stop()

    view = ConfirmView()
    confirm_msg = await ctx.reply(embed=confirm_e, view=view)
    await view.wait()

    if not view.confirmed:
        return await confirm_msg.edit(embed=embed_warn("Envoi annulé."), view=None)

    progress_e = discord.Embed(
        title="📨  Envoi en cours...",
        description=f"Envoi à **{len(members)}** membres...",
        color=C["info"], timestamp=datetime.utcnow(),
    )
    footer(progress_e, ctx.author)
    progress_msg = await ctx.send(embed=progress_e)

    ok_count   = 0
    fail_count = 0
    for m in members:
        try:
            await m.send(message.replace("{user}", m.mention))
            ok_count += 1
        except (discord.Forbidden, discord.HTTPException):
            fail_count += 1
        await asyncio.sleep(0.7)

    result_e = discord.Embed(title="📨  DM Global terminé", color=C["ok"], timestamp=datetime.utcnow())
    result_e.add_field(name="✅ Envoyés",  value=f"`{ok_count}`",  inline=True)
    result_e.add_field(name="❌ Échoués", value=f"`{fail_count}`", inline=True)
    if role_filter:
        result_e.add_field(name="🎭 Rôle", value=role_filter.mention, inline=True)
    result_e.add_field(name="📝 Message", value=f"```{message[:200]}```", inline=False)
    footer(result_e, ctx.author)
    await progress_msg.edit(embed=result_e)

    asyncio.create_task(send_log(
        ctx.guild, ctx.author, "dmall", "DM Global envoyé",
        [
            ("⌨️ Commande", "`&dmall`"),
            ("🎯 Scope",    role_filter.mention if role_filter else "*Tout le serveur*"),
            ("✅ Envoyés",  f"`{ok_count}`"),
            ("❌ Échoués",  f"`{fail_count}`"),
            ("📝 Message",  f"```{message[:200]}```", False),
        ],
    ))

# ══════════════════════════════════════════════════════════════════════
#  LANCEMENT
# ══════════════════════════════════════════════════════════════════════
bot.run(os.environ["TOKEN"])
