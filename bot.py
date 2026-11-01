import os
import re
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
ROLES_FILE     = "saved_roles.json"
PROTECT_FILE   = "protected_users.json"
LOG_CHANNEL_ID = 1558616294788698293
CIVIL_ROLE_ID  = 1564722577060929546
OG_ROLE_ID     = 1558499311237468280   # ← rôle OG → WL server automatique

# ── Palette DA ────────────────────────────────────────────────────────
C = {
    "ok":       0x43B581,
    "error":    0xF04747,
    "warn":     0xFAA61A,
    "info":     0x7289DA,
    "sys":      0xFF73FA,
    "orange":   0xFF7043,
    "maint":    0xFFB347,
    "dark":     0x23272A,
    "purple":   0xA855F7,
    "teal":     0x00BFA5,
    "log":      0x2C2F33,
    "gold":     0xF1C40F,
    "rose":     0xFF4081,
    "navy":     0x3F51B5,
    "mint":     0x26A69A,
}

SEP = "┄" * 35

# ══════════════════════════════════════════════════════════════════════
#  EMBED FACTORY
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
#  ANCIENS RÔLES (derank / rerank)  I/O
# ══════════════════════════════════════════════════════════════════════
def load_saved_roles() -> dict:
    if os.path.exists(ROLES_FILE):
        try:
            with open(ROLES_FILE) as f:
                return {int(k): v for k, v in json.load(f).items()}
        except Exception:
            pass
    return {}

def save_saved_roles() -> None:
    with open(ROLES_FILE, "w") as f:
        json.dump({str(k): v for k, v in saved_roles.items()}, f)

# ══════════════════════════════════════════════════════════════════════
#  UTILISATEURS PROTÉGÉS  I/O   { membre_protégé : sys+ qui l'a protégé }
# ══════════════════════════════════════════════════════════════════════
def load_protected() -> dict:
    if os.path.exists(PROTECT_FILE):
        try:
            with open(PROTECT_FILE) as f:
                return {int(k): v for k, v in json.load(f).items()}
        except Exception:
            pass
    return {}

def save_protected() -> None:
    with open(PROTECT_FILE, "w") as f:
        json.dump({str(k): v for k, v in protected_users.items()}, f)

# ══════════════════════════════════════════════════════════════════════
#  SYSTÈME DE LOGS
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
    "rerank":      ("🔄", C["ok"]),
    "protect":     ("🛡️", C["teal"]),
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
    "wl_masse":    ("👥", C["sys"]),
    "og_auto_wl":  ("⭐", C["gold"]),
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
saved_roles:     dict  = load_saved_roles()
protected_users: dict  = load_protected()
private_vocs:    dict  = {}
pv_access:       dict  = {}
pv_violations:   dict  = {}
follow_active:   dict  = {}
laisse_active:   dict  = {}
dog_active:      dict  = {}
menotte_active:  dict  = {}
wakeup_active:   set   = set()
wakeup_cd:       dict  = {}
dog_cd:          dict  = {}
menotte_cd:      dict  = {}
locked_nicks:    set   = set()
locked_channels: dict  = {}
maintenance:     bool  = False
snipe_cache:     dict  = {}

WL_LABELS = {
    "voicevip":  ("🎤", "VoiceVIP",  C["purple"]),
    "server":    ("🌐", "Server",    C["teal"]),
    "sys":       ("⚡", "WL Sys",    C["info"]),
    "privilege": ("👑", "Privilege", C["sys"]),
}

# ══════════════════════════════════════════════════════════════════════
#  OG ROLE AUTO-WL  helpers
# ══════════════════════════════════════════════════════════════════════

def _has_og_role(member: discord.Member) -> bool:
    return any(r.id == OG_ROLE_ID for r in member.roles)

def _ensure_og_wl(member: discord.Member) -> bool:
    """Donne la WL server à un membre OG si il ne l'a pas déjà. Retourne True si ajoutée."""
    if member.bot:
        return False
    lst = whitelisted.setdefault(member.id, [])
    if "server" not in lst:
        lst.append("server")
        return True
    return False

def _count_og_wl(guild: discord.Guild) -> int:
    """Nombre de membres qui ont la WL server grâce au rôle OG (approximatif : membres avec rôle OG)."""
    role = guild.get_role(OG_ROLE_ID)
    if not role:
        return 0
    return sum(1 for m in role.members if not m.bot)

# ══════════════════════════════════════════════════════════════════════
#  BOT
# ══════════════════════════════════════════════════════════════════════
def prefixes_for(user_id: int) -> list:
    return ["&", "="] if is_sys_plus(user_id) else ["="]

async def get_prefix(bot, message):
    return prefixes_for(message.author.id)

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

MSG_OWNER = (
    "🫵💀  Frérot, j'ai crée le bot et t'essayes de me toucher ?\n"
    "La prochaine c TO 24h, tu feras un ticket pour te faire unto. 🎟️"
)
MSG_SYS = "🚫⚡  N'essaye plus jamais de toucher un **Sys+** ! 😤"
MSG_PROTECT = "🛡️  {user} est un **utilisateur protégé par un Fondateur**.\nTu ne peux pas le toucher."

async def protection_check(ctx, target: discord.Member) -> bool:
    if target.id == OWNER_ID and not is_owner(ctx.author.id):
        await ctx.reply(embed=embed_err(MSG_OWNER))
        return False
    if is_sys_plus(target.id) and not is_sys_plus(ctx.author.id):
        await ctx.reply(embed=embed_err(MSG_SYS))
        return False
    if target.id in protected_users and not is_sys_plus(ctx.author.id):
        await ctx.reply(embed=embed_err(MSG_PROTECT.format(user=target.mention)))
        return False
    return True

async def _deny_i(i: discord.Interaction, text: str) -> None:
    e = embed_err(text)
    if not i.response.is_done():
        await i.response.send_message(embed=e)
    else:
        await i.channel.send(embed=e)

async def protection_check_i(i: discord.Interaction, target: discord.Member) -> bool:
    if target.id == OWNER_ID and not is_owner(i.user.id):
        await _deny_i(i, f"{i.user.mention}  {MSG_OWNER}")
        return False
    if is_sys_plus(target.id) and not is_sys_plus(i.user.id):
        await _deny_i(i, f"{i.user.mention}  {MSG_SYS}")
        return False
    if target.id in protected_users and not is_sys_plus(i.user.id):
        await _deny_i(i, MSG_PROTECT.format(user=target.mention))
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

REPLY_CMDS = {"wl", "derank", "rerank", "laisse", "acces", "join", "menotte", "follow", "mp", "mv"}
_ID_RE = re.compile(r"^(<@!?\d+>|\d{15,21})$")

@bot.event
async def on_message(message: discord.Message):
    if message.author.bot or message.guild is None:
        return

    if message.reference and is_sys_plus(message.author.id):
        content = message.content
        prefix = next((p for p in prefixes_for(message.author.id) if content.startswith(p)), None)
        if prefix:
            parts = content[len(prefix):].split(None, 1)
            if parts and parts[0].lower() in REPLY_CMDS:
                args  = parts[1] if len(parts) > 1 else ""
                first = args.split(None, 1)[0] if args else ""
                if not _ID_RE.match(first):
                    ref = message.reference.resolved
                    if not isinstance(ref, discord.Message):
                        try:
                            ref = await message.channel.fetch_message(message.reference.message_id)
                        except Exception:
                            ref = None
                    if ref is not None:
                        message.content = f"{prefix}{parts[0]} <@{ref.author.id}>" + (f" {args}" if args else "")

    await bot.process_commands(message)


@bot.event
async def on_ready():
    await tree.sync()
    print(f"[OK] {bot.user} connecte (ID: {bot.user.id})")
    await bot.change_presence(
        status=discord.Status.online,
        activity=discord.Activity(type=discord.ActivityType.watching, name="Shotojo 🌸  #🇯🇵"),
    )
    # ── Sync OG WL au démarrage ───────────────────────────────────────
    added_total = 0
    for guild in bot.guilds:
        og_role = guild.get_role(OG_ROLE_ID)
        if not og_role:
            continue
        for member in og_role.members:
            if _ensure_og_wl(member):
                added_total += 1
    if added_total:
        save_wl()
        print(f"[OG-WL] {added_total} membres OG ont reçu la WL server au démarrage.")


@bot.event
async def on_member_update(before: discord.Member, after: discord.Member):
    # ── Rôle OG ajouté → WL server automatique ───────────────────────
    before_roles = {r.id for r in before.roles}
    after_roles  = {r.id for r in after.roles}

    if OG_ROLE_ID in after_roles and OG_ROLE_ID not in before_roles:
        # Le rôle OG vient d'être donné
        if _ensure_og_wl(after):
            save_wl()
            print(f"[OG-WL] WL server auto-donnée à {after} ({after.id})")

    # ── Rôle OG retiré → on retire la WL server (si pas Sys+) ────────
    if OG_ROLE_ID in before_roles and OG_ROLE_ID not in after_roles:
        if not is_sys_plus(after.id):
            lst = whitelisted.get(after.id, [])
            if "server" in lst:
                lst.remove("server")
                if not lst:
                    whitelisted.pop(after.id, None)
                else:
                    whitelisted[after.id] = lst
                save_wl()
                print(f"[OG-WL] WL server retirée à {after} ({after.id}) — rôle OG retiré.")

    # ── Nick lock ─────────────────────────────────────────────────────
    if after.id in locked_nicks and after.nick != "S":
        try:
            await after.edit(nick="S")
        except Exception:
            pass


@bot.event
async def on_message_delete(message):
    if message.author.bot or not message.content:
        return
    if message.content.strip().lower().startswith(("=snipe", "&snipe")):
        return
    snipe_cache[message.channel.id] = {
        "content":     message.content,
        "author":      str(message.author),
        "author_icon": message.author.display_avatar.url,
        "deleted_at":  datetime.utcnow(),
    }


@bot.event
async def on_voice_state_update(member, before, after):
    guild = member.guild

    for fid, tid in list(follow_active.items()):
        if member.id == tid and after.channel and after.channel != before.channel:
            follower = guild.get_member(fid)
            if follower and follower.voice and follower.voice.channel != after.channel:
                try:
                    await follower.move_to(after.channel)
                except Exception:
                    pass

    for oid, (cid, _, _) in list(dog_active.items()):
        if member.id == oid and after.channel and after.channel != before.channel:
            cible = guild.get_member(cid)
            if cible:
                try:
                    await cible.move_to(after.channel)
                except Exception:
                    pass

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
            try:
                await member.move_to(None)
            except Exception:
                pass

            count = pv_violations.get(member.id, 0) + 1
            pv_violations[member.id] = count

            labels = {
                "normal":  "🔒 Vocal privée",
                "sys":     "🔒 Vocal privée Sys",
                "sysplus": "🔒 Vocal privée Sys+",
            }
            label = labels.get(pv_type, "Vocal privée")

            if count == 1:
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
        return await ctx.reply(embed=embed_err("Usage : `&wl @membre`  (ou réponds à son message avec `&wl`)"))
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
#  &wlpanel  — tableau de bord
# ══════════════════════════════════════════════════════════════════════

def _wlpanel_embed(guild: discord.Guild) -> discord.Embed:
    # Comptage WL manuelles (fichier)
    manual_server = sum(1 for v in whitelisted.values() if "server"   in v)
    manual_vvip   = sum(1 for v in whitelisted.values() if "voicevip" in v)
    manual_sys    = sum(1 for v in whitelisted.values() if "sys"      in v)
    manual_priv   = sum(1 for v in whitelisted.values() if "privilege" in v)

    og_count  = _count_og_wl(guild)            # membres OG non-bot
    sys_bonus = len(SYS_PLUS_IDS)

    vvip_total   = manual_vvip  + sys_bonus
    server_total = manual_server + og_count + sys_bonus  # OG comptés ici
    sys_total    = manual_sys   + sys_bonus
    priv_total   = manual_priv

    total_wl = sum(len(v) for v in whitelisted.values())

    status_line = "🔴  **MAINTENANCE**" if maintenance else "🟢  **Opérationnel**"

    e = discord.Embed(
        title="⬡  Tableau de bord  ·  Sys+",
        description=f"{status_line}\n\n`{SEP}`",
        color=C["maint"] if maintenance else C["dark"],
        timestamp=datetime.utcnow(),
    )

    e.add_field(
        name="🏷️  Whitelists",
        value=(
            f"🎤 VoiceVIP  ·  `{vvip_total}`\n"
            f"🌐 Server    ·  `{server_total}`  *(dont ⭐ OG `{og_count}`)*\n"
            f"⚡ WL Sys   ·  `{sys_total}`\n"
            f"👑 Privilege ·  `{priv_total}`\n"
            f"**Total WL fichier  ·  `{total_wl}`**"
        ),
        inline=True,
    )

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


# ══════════════════════════════════════════════════════════════════════
#  REFONTE PANEL WL — système de retrait paginé avec recherche
# ══════════════════════════════════════════════════════════════════════

PAGE_SIZE = 8   # entrées par page dans le sélecteur WL

def _wl_entries_all() -> list[tuple[int, str]]:
    """Retourne [(uid, wl_key), ...] triés par uid."""
    return sorted(
        [(uid, wl) for uid, wls in whitelisted.items() for wl in wls],
        key=lambda x: x[0],
    )

def _wl_entries_filtered(query: str) -> list[tuple[int, str]]:
    """Filtre les entrées WL par nom d'utilisateur ou ID (query insensible à la casse)."""
    q = query.lower().strip()
    return [
        (uid, wl) for uid, wl in _wl_entries_all()
        if q in str(uid) or q in wl.lower()
    ]


class WLRemovePaginatedView(discord.ui.View):
    """
    Panel de retrait WL avec :
    - recherche par ID / nom de WL
    - pagination par pages de PAGE_SIZE
    - sélecteur pour choisir l'entrée à retirer
    """

    def __init__(self, guild: discord.Guild, invoker: discord.Member, query: str = ""):
        super().__init__(timeout=180)
        self.guild   = guild
        self.invoker = invoker
        self.query   = query
        self.page    = 0
        self._rebuild()

    # ── helpers ──────────────────────────────────────────────────────

    def _entries(self) -> list[tuple[int, str]]:
        if self.query:
            return _wl_entries_filtered(self.query)
        return _wl_entries_all()

    def _max_page(self) -> int:
        return max(0, (len(self._entries()) - 1) // PAGE_SIZE)

    def _page_entries(self) -> list[tuple[int, str]]:
        entries = self._entries()
        start   = self.page * PAGE_SIZE
        return entries[start:start + PAGE_SIZE]

    def _rebuild(self):
        """Reconstruit les composants selon la page courante."""
        self.clear_items()
        page_entries = self._page_entries()
        entries_all  = self._entries()
        total        = len(entries_all)
        max_page     = self._max_page()

        # ── Sélecteur d'entrée ────────────────────────────────────────
        if page_entries:
            options = []
            for uid, wl in page_entries:
                m    = self.guild.get_member(uid)
                icon = WL_LABELS.get(wl, ("•", wl, 0))[0]
                name = m.display_name if m else f"ID {uid}"
                options.append(discord.SelectOption(
                    label=f"{icon} {wl}  ·  {name}"[:100],
                    value=f"{uid}|{wl}",
                    description=f"ID : {uid}"[:100],
                    emoji=None,
                ))
            sel = discord.ui.Select(
                placeholder=f"Choisir une WL à retirer  (p.{self.page+1}/{max_page+1})",
                options=options,
                custom_id="wl_remove_select",
            )
            sel.callback = self._on_select
            self.add_item(sel)

        # ── Navigation ───────────────────────────────────────────────
        prev_btn = discord.ui.Button(
            label="◀", style=discord.ButtonStyle.grey,
            disabled=(self.page == 0), row=1,
        )
        prev_btn.callback = self._prev
        self.add_item(prev_btn)

        count_btn = discord.ui.Button(
            label=f"{self.page+1} / {max_page+1}  ({total} entrées)",
            style=discord.ButtonStyle.grey, disabled=True, row=1,
        )
        self.add_item(count_btn)

        next_btn = discord.ui.Button(
            label="▶", style=discord.ButtonStyle.grey,
            disabled=(self.page >= max_page), row=1,
        )
        next_btn.callback = self._next
        self.add_item(next_btn)

        # ── Recherche ────────────────────────────────────────────────
        search_btn = discord.ui.Button(
            label=f"🔍 Recherche{' : ' + self.query if self.query else ''}",
            style=discord.ButtonStyle.blurple if self.query else discord.ButtonStyle.grey,
            row=2,
        )
        search_btn.callback = self._open_search
        self.add_item(search_btn)

        if self.query:
            clear_btn = discord.ui.Button(label="✖ Effacer filtre", style=discord.ButtonStyle.red, row=2)
            clear_btn.callback = self._clear_search
            self.add_item(clear_btn)

        close_btn = discord.ui.Button(label="✕ Fermer", style=discord.ButtonStyle.danger, row=3)
        close_btn.callback = self._close
        self.add_item(close_btn)

    def _build_embed(self) -> discord.Embed:
        entries = self._entries()
        total   = len(entries)
        if total == 0:
            desc = "*Aucune WL trouvée.*" if self.query else "*Aucune WL enregistrée.*"
        else:
            lines = []
            for uid, wl in self._page_entries():
                m    = self.guild.get_member(uid)
                icon = WL_LABELS.get(wl, ("•", wl, 0))[0]
                name = m.mention if m else f"`{uid}`"
                lines.append(f"{icon} `{wl}`  ·  {name}")
            desc = "\n".join(lines)
            if self.query:
                desc = f"🔍 Filtre : `{self.query}`\n\n" + desc

        e = discord.Embed(
            title=f"👥  Gestion WL  ·  {total} entrée(s)",
            description=desc,
            color=C["sys"],
            timestamp=datetime.utcnow(),
        )
        footer(e, self.invoker)
        return e

    # ── callbacks ────────────────────────────────────────────────────

    async def interaction_check(self, i: discord.Interaction) -> bool:
        if i.user.id != self.invoker.id:
            await i.response.send_message(embed=embed_err("Ce panel ne t'appartient pas."), ephemeral=True)
            return False
        if not is_sys_plus(i.user.id):
            await i.response.send_message(embed=embed_err("Réservé aux Sys+."), ephemeral=True)
            return False
        return True

    async def _on_select(self, i: discord.Interaction):
        value    = i.data["values"][0]
        uid_str, wl = value.split("|", 1)
        uid = int(uid_str)
        m = self.guild.get_member(uid)

        if uid in whitelisted and wl in whitelisted[uid]:
            whitelisted[uid].remove(wl)
            if not whitelisted[uid]:
                del whitelisted[uid]
            save_wl()

        icon, label_name, color = WL_LABELS.get(wl, ("•", wl, C["error"]))
        name_display = m.display_name if m else f"ID {uid}"

        # On remet page à 0 si elle dépasse
        if self.page > self._max_page():
            self.page = max(0, self._max_page())

        self._rebuild()
        confirm = discord.Embed(
            title=f"{icon}  WL retirée",
            description=f"**{label_name}** retirée à **{name_display}**.",
            color=C["error"], timestamp=datetime.utcnow(),
        )
        footer(confirm, i.user)
        await i.response.edit_message(embed=self._build_embed(), view=self)
        await i.followup.send(embed=confirm, ephemeral=True)

        asyncio.create_task(send_log(
            self.guild, i.user, "wl", f"WL retirée  {label_name}",
            [("⌨️ Commande", "`&wlpanel`"), ("🏷️ WL", f"`{wl}`  {icon}"), ("📋 Label", label_name)],
            target=m,
        ))
        if m:
            try:
                dm = discord.Embed(
                    title="🚫  Whitelist retirée",
                    description=f"Ta **{label_name}** t'a été retirée sur **{self.guild.name}**.",
                    color=C["error"], timestamp=datetime.utcnow(),
                )
                footer(dm)
                await m.send(embed=dm)
            except Exception:
                pass

    async def _prev(self, i: discord.Interaction):
        self.page = max(0, self.page - 1)
        self._rebuild()
        await i.response.edit_message(embed=self._build_embed(), view=self)

    async def _next(self, i: discord.Interaction):
        self.page = min(self._max_page(), self.page + 1)
        self._rebuild()
        await i.response.edit_message(embed=self._build_embed(), view=self)

    async def _open_search(self, i: discord.Interaction):
        await i.response.send_modal(_WLSearchModal(self))

    async def _clear_search(self, i: discord.Interaction):
        self.query = ""
        self.page  = 0
        self._rebuild()
        await i.response.edit_message(embed=self._build_embed(), view=self)

    async def _close(self, i: discord.Interaction):
        await i.response.defer()
        await i.delete_original_response()
        self.stop()


class _WLSearchModal(discord.ui.Modal, title="Rechercher une WL"):
    query = discord.ui.TextInput(
        label="ID du membre ou nom de WL",
        placeholder="ex: 123456789 ou server ou voicevip",
        max_length=50, required=True,
    )

    def __init__(self, parent: WLRemovePaginatedView):
        super().__init__()
        self._parent = parent

    async def on_submit(self, i: discord.Interaction):
        self._parent.query = self.query.value.strip()
        self._parent.page  = 0
        self._parent._rebuild()
        await i.response.edit_message(
            embed=self._parent._build_embed(),
            view=self._parent,
        )


# ══════════════════════════════════════════════════════════════════════
#  Vues secondaires (PV, Laisse, Dog, Follow, Menotte, Tipeu)
# ══════════════════════════════════════════════════════════════════════

class PVListView(discord.ui.View):
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


# ══════════════════════════════════════════════════════════════════════
#  WL MASSE PAR RÔLE  (select défilant)
# ══════════════════════════════════════════════════════════════════════

def _find_role(guild: discord.Guild, text: str):
    text = text.strip()
    if not text:
        return None
    m = re.search(r"\d{15,21}", text)
    if m:
        r = guild.get_role(int(m.group()))
        if r:
            return r
    t = text.lower()
    roles = [r for r in guild.roles if r != guild.default_role]
    for r in roles:
        if r.name.lower() == t:
            return r
    cands = [r for r in roles if t in r.name.lower()]
    cands.sort(key=lambda r: r.position, reverse=True)
    return cands[0] if cands else None


class WLMasseTypeSelect(discord.ui.Select):
    def __init__(self, guild: discord.Guild):
        self.guild = guild
        options = [
            discord.SelectOption(label="🎤 VoiceVIP",  value="voicevip",  description="Accès aux vocaux privés"),
            discord.SelectOption(label="🌐 Server",    value="server",    description="Commandes server (dog, snap, wakeup...)"),
            discord.SelectOption(label="⚡ WL Sys",    value="sys",       description="Commandes WL Sys (follow, pvsys...)"),
            discord.SelectOption(label="👑 Privilege", value="privilege", description="Whitelist Privilege"),
        ]
        super().__init__(
            placeholder="Quelle WL donner ?",
            options=options,
            min_values=1,
            max_values=1,
        )

    async def callback(self, interaction: discord.Interaction):
        if not is_sys_plus(interaction.user.id):
            return await interaction.response.send_message(embed=embed_err("Réservé aux Sys+."), ephemeral=True)

        guild = self.guild
        wl = self.values[0]
        icon, label, color = WL_LABELS[wl]

        def prompt(extra: str = "") -> discord.Embed:
            e = discord.Embed(
                title=f"{icon}  WL masse  ·  {label}",
                description=(
                    f"{extra}"
                    "**À quel rôle donner cette WL ?**\n"
                    "Écris dans ce salon son **nom** ou son **ID** (60 secondes).\n"
                    "*Évite de le mentionner pour ne pas ping tout le rôle.*\n"
                    "Écris `annuler` pour stopper."
                ),
                color=color, timestamp=datetime.utcnow(),
            )
            footer(e, interaction.user)
            return e

        await interaction.response.edit_message(embed=prompt(), view=None)

        def check(m: discord.Message):
            return m.author.id == interaction.user.id and m.channel.id == interaction.channel_id

        role = None
        while role is None:
            try:
                msg = await bot.wait_for("message", check=check, timeout=60)
            except asyncio.TimeoutError:
                return await interaction.edit_original_response(
                    embed=embed_warn("Temps écoulé, relance depuis le panel."), view=None
                )
            content = msg.content.strip()
            found = msg.role_mentions[0] if msg.role_mentions else None
            try:
                await msg.delete()
            except Exception:
                pass
            if content.lower() in ("annuler", "cancel", "stop"):
                return await interaction.edit_original_response(
                    embed=embed_warn("WL masse annulée."), view=None
                )
            role = found or _find_role(guild, content)
            if role is None:
                await interaction.edit_original_response(
                    embed=prompt(f"❌ Rôle **{discord.utils.escape_markdown(content[:50])}** introuvable, réessaie.\n\n"),
                    view=None,
                )

        members = [m for m in role.members if not m.bot]
        if not members:
            return await interaction.edit_original_response(
                embed=embed_warn(f"Le rôle **{role.name}** n'a aucun membre."), view=None
            )

        ok_count, skip_count = 0, 0
        for m in members:
            lst = whitelisted.setdefault(m.id, [])
            if wl not in lst:
                lst.append(wl)
                ok_count += 1
            else:
                skip_count += 1
        save_wl()

        e = discord.Embed(
            title=f"{icon}  WL masse  ·  {label}",
            description=(
                f"Rôle ciblé : {role.mention}\n"
                f"**{ok_count}** membre(s) ont reçu la **{label}**.\n"
                f"**{skip_count}** l'avaient déjà."
            ),
            color=color, timestamp=datetime.utcnow(),
        )
        e.set_thumbnail(url=guild.icon.url if guild.icon else None)
        footer(e, interaction.user)
        await interaction.edit_original_response(embed=e, view=None)

        asyncio.create_task(send_log(
            guild, interaction.user, "wl_masse", f"WL masse  {label}",
            [
                ("⌨️ Commande", "`&wlpanel`"),
                ("🏷️ WL",       f"`{wl}`  {icon}"),
                ("🎭 Rôle",      f"{role.mention}  `{role.id}`"),
                ("✅ Attribuées", f"`{ok_count}`"),
                ("⏭️ Déjà WL",   f"`{skip_count}`"),
            ],
        ))

        async def _notify():
            for m in members:
                if wl in whitelisted.get(m.id, []):
                    try:
                        dm = discord.Embed(
                            title=f"{icon}  Nouvelle whitelist !",
                            description=f"Tu as reçu la **{label}** sur **{guild.name}**.",
                            color=color, timestamp=datetime.utcnow(),
                        )
                        dm.set_thumbnail(url=guild.icon.url if guild.icon else None)
                        footer(dm)
                        await m.send(embed=dm)
                    except Exception:
                        pass
                    await asyncio.sleep(0.5)
        asyncio.create_task(_notify())


class WLMasseView(discord.ui.View):
    def __init__(self, guild: discord.Guild):
        super().__init__(timeout=120)
        self.add_item(WLMasseTypeSelect(guild))


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
        view = PVListView(self.guild, entries[:5])
        await i.response.send_message(
            embed=self._cat_embed(f"🔒  Vocaux privés  ({len(entries)})", C["purple"], lines),
            view=view, ephemeral=True,
        )

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
                f"🐕  {ow.display_name if ow else oid}  ›  {ci.display_name if ci else cid}\n"
                f"   › Pseudo : `{new_nick}`"
            )
        view = DogListView(self.guild, entries[:5])
        await i.response.send_message(
            embed=self._cat_embed(f"🐕  Dogs  ({len(entries)})", C["orange"], lines),
            view=view, ephemeral=True,
        )

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

    @discord.ui.button(label="👥 Gérer les WL", style=discord.ButtonStyle.green, row=2)
    async def btn_wl(self, i: discord.Interaction, b):
        """Nouveau panel paginé avec recherche."""
        view = WLRemovePaginatedView(self.guild, i.user)
        await i.response.send_message(embed=view._build_embed(), view=view, ephemeral=True)

    @discord.ui.button(label="🎭 WL par rôle", style=discord.ButtonStyle.green, row=2)
    async def btn_wl_masse(self, i: discord.Interaction, b):
        e = discord.Embed(
            title="🎭  WL masse  ·  Par rôle",
            description=(
                "Choisis d'abord la **WL** à attribuer.\n"
                "Je te demanderai ensuite le **rôle** (nom ou ID) dans le salon."
            ),
            color=C["sys"],
            timestamp=datetime.utcnow(),
        )
        footer(e, i.user)
        await i.response.send_message(embed=e, view=WLMasseView(self.guild), ephemeral=True)

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

    @discord.ui.button(label="😈 Stop wakeups", style=discord.ButtonStyle.red, row=3)
    async def btn_wakeup(self, i: discord.Interaction, b):
        if not wakeup_active:
            return await i.response.send_message(embed=embed_warn("Aucun wakeup actif."), ephemeral=True)
        ids_before = set(wakeup_active)
        wakeup_active.clear()
        lines = [f"😈  `{uid}`" for uid in ids_before]
        e = embed_ok(f"Tous les wakeups stoppés.\n\n" + "\n".join(lines))
        footer(e, i.user)
        await i.response.send_message(embed=e, ephemeral=True)

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
#  &clear / &derank / &rerank
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
    roles = [
        r for r in member.roles
        if r != ctx.guild.default_role and not r.managed and r < ctx.guild.me.top_role
    ]
    if not roles:
        return await ctx.reply(embed=embed_warn(f"{member.mention} n'a aucun rôle à retirer."))
    roles_txt = "  ".join(r.mention for r in roles)

    prev = saved_roles.get(member.id, [])
    saved_roles[member.id] = list(dict.fromkeys(prev + [r.id for r in roles]))
    save_saved_roles()

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


@bot.command(name="rerank")
@check_sys_plus()
async def rerank_cmd(ctx, member: discord.Member = None):
    if not member:
        return await ctx.reply(embed=embed_err("Usage : `&rerank @membre`  (ou réponds à son message avec `&rerank`)"))
    if not await protection_check(ctx, member):
        return

    ids = saved_roles.get(member.id)
    if not ids:
        return await ctx.reply(embed=embed_warn(f"Aucun ancien rôle enregistré pour {member.mention}."))

    me_top = ctx.guild.me.top_role
    to_add, skipped = [], []
    for rid in ids:
        r = ctx.guild.get_role(rid)
        if r is None or r in member.roles:
            continue
        if r.managed or r >= me_top:
            skipped.append(r)
            continue
        to_add.append(r)

    if to_add:
        try:
            await member.add_roles(*to_add, reason=f"Rerank par {ctx.author}")
        except discord.Forbidden:
            return await ctx.reply(embed=embed_err("Impossible de redonner ces rôles (permissions)."))

    if skipped:
        saved_roles[member.id] = [r.id for r in skipped]
    else:
        saved_roles.pop(member.id, None)
    save_saved_roles()

    e = discord.Embed(title="🔄  Rerank exécuté", color=C["ok"], timestamp=datetime.utcnow())
    e.set_author(name=member.display_name, icon_url=member.display_avatar.url)
    e.set_thumbnail(url=member.display_avatar.url)
    e.add_field(name="Membre", value=member.mention,     inline=True)
    e.add_field(name="Par",    value=ctx.author.mention, inline=True)
    e.add_field(name="🎭 Rôles rendus",
                value="  ".join(r.mention for r in to_add) or "*Aucun*", inline=False)
    if skipped:
        e.add_field(name="⚠️ Non restaurés (trop hauts / gérés)",
                    value="  ".join(r.mention for r in skipped), inline=False)
    footer(e, ctx.author)
    await ctx.reply(embed=e)

    asyncio.create_task(send_log(
        ctx.guild, ctx.author, "rerank", "Rerank exécuté",
        [("⌨️ Commande", "`&rerank`"),
         ("🎭 Rôles", "  ".join(r.mention for r in to_add) or "*Aucun*", False)],
        target=member,
    ))
    try:
        dm = discord.Embed(
            title="🔄  Tes rôles ont été restaurés",
            description=f"Tes anciens rôles t'ont été rendus sur **{ctx.guild.name}**.",
            color=C["ok"], timestamp=datetime.utcnow(),
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

@tree.command(name="rollbackrole", description="Annule un /addrole tous via les logs d'audit (Sys+)")
@app_commands.describe(
    role="Le rôle à retirer",
    minutes="Fenêtre de recherche en minutes (défaut 120)",
    confirmer="False = simulation, True = exécute vraiment",
)
async def rollbackrole_slash(i: discord.Interaction, role: discord.Role, minutes: int = 120, confirmer: bool = False):
    if not is_sys_plus(i.user.id):
        return await i.response.send_message(embed=embed_err("Réservé aux **Sys+**."), ephemeral=True)
    if role >= i.guild.me.top_role:
        return await i.response.send_message(embed=embed_err("Ce rôle est trop haut pour moi."), ephemeral=True)

    await i.response.defer(thinking=True, ephemeral=True)
    since = discord.utils.utcnow() - timedelta(minutes=minutes)

    ids = set()
    try:
        async for en in i.guild.audit_logs(
            limit=None,
            action=discord.AuditLogAction.member_role_update,
            user=i.guild.me,
            after=since,
        ):
            if not (en.reason or "").startswith("/addrole tous"):
                continue
            added = [r.id for r in (getattr(en.after, "roles", None) or [])]
            if role.id in added and en.target is not None:
                ids.add(en.target.id)
    except discord.Forbidden:
        return await i.followup.send(
            embed=embed_err("Il me faut la permission **Voir les logs du serveur**."), ephemeral=True)

    members = [m for uid in ids if (m := i.guild.get_member(uid)) and role in m.roles]

    if not confirmer:
        return await i.followup.send(embed=embed_warn(
            f"**Simulation** : **{len(members)}** membre(s) perdraient {role.mention}.\n"
            f"Compare avec le `✅ OK` de ton /addrole. Si ça colle, relance avec `confirmer: True`."
        ), ephemeral=True)

    ok, fail = 0, 0
    for m in members:
        try:
            await m.remove_roles(role, reason=f"/rollbackrole  {i.user}")
            ok += 1
        except Exception:
            fail += 1

    e = discord.Embed(title="↩️  Rollback effectué", color=C["orange"], timestamp=datetime.utcnow())
    e.add_field(name="Rôle",  value=role.mention, inline=True)
    e.add_field(name="✅ OK", value=f"`{ok}`",    inline=True)
    e.add_field(name="❌ KO", value=f"`{fail}`",  inline=True)
    footer(e, i.user)
    await i.followup.send(embed=e, ephemeral=True)
    asyncio.create_task(send_log(
        i.guild, i.user, "removerole", "Rollback addrole tous",
        [("⌨️ Commande", "`/rollbackrole`"), ("🎭 Rôle", role.mention), ("✅", f"`{ok}`"), ("❌", f"`{fail}`")],
    ))


@tree.command(name="protect-user", description="Protéger un membre (ou retirer sa protection) (Sys+)")
@app_commands.describe(membre="Le membre à protéger  ·  refais la commande pour retirer la protection")
async def protect_user_slash(i: discord.Interaction, membre: discord.Member):
    if not is_sys_plus(i.user.id):
        return await i.response.send_message(embed=embed_err("Réservé aux **Sys+**."), ephemeral=True)
    if membre.bot:
        return await i.response.send_message(embed=embed_err("Impossible de protéger un bot."), ephemeral=True)
    if is_sys_plus(membre.id):
        return await i.response.send_message(
            embed=embed_warn(f"{membre.mention} est un **Sys+**, il est déjà intouchable."), ephemeral=True)

    if membre.id in protected_users:
        protected_users.pop(membre.id, None)
        save_protected()
        e = embed_warn(f"La protection de {membre.mention} a été **retirée**.", title="Protection retirée")
        footer(e, i.user)
        await i.response.send_message(embed=e)
        asyncio.create_task(send_log(
            i.guild, i.user, "protect", "Protection retirée",
            [("⌨️ Commande", "`/protect-user`")], target=membre,
        ))
        return

    protected_users[membre.id] = i.user.id
    save_protected()
    e = discord.Embed(
        title="🛡️  Utilisateur protégé",
        description=f"{membre.mention} est maintenant **protégé par un Fondateur**.\nPersonne (hors Sys+) ne peut le cibler.",
        color=C["teal"], timestamp=datetime.utcnow(),
    )
    e.set_thumbnail(url=membre.display_avatar.url)
    footer(e, i.user)
    await i.response.send_message(embed=e)
    asyncio.create_task(send_log(
        i.guild, i.user, "protect", "Utilisateur protégé",
        [("⌨️ Commande", "`/protect-user`")], target=membre,
    ))


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
    if not await protection_check_i(i, membre):
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
    if not await protection_check_i(i, membre):
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
#  LIBERTÉ
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
                "`&clear`  `&derank`  `&rerank`  `&lock`  `&renew`\n"
                "`/addrole`  `/removerole`  `/rollbackrole`  `/protect-user`\n"
                "*· en répondant à un message, la commande cible son auteur*\n"
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
#  &lock
# ══════════════════════════════════════════════════════════════════════
@bot.command(name="lock")
@check_sys_plus()
async def lock_cmd(ctx, channel: discord.TextChannel = None):
    channel  = channel or ctx.channel
    everyone = ctx.guild.default_role
    civil    = ctx.guild.get_role(CIVIL_ROLE_ID)

    if channel.id in locked_channels:
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

    saved_overwrites = {}
    blocked_roles    = {everyone}
    if civil:
        blocked_roles.add(civil)

    perm_tasks   = []
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

    for role in [everyone, civil]:
        if role is None:
            continue
        current_ow = channel.overwrites_for(role)
        saved_overwrites[role] = current_ow if not current_ow.is_empty() else None

    locked_channels[channel.id] = saved_overwrites

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
#  LANCEMENT
# ══════════════════════════════════════════════════════════════════════
bot.run(os.environ["TOKEN"])
