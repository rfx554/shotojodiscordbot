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
    "ok":       0x57F287,   # vert Discord
    "error":    0xED4245,   # rouge Discord
    "warn":     0xFEE75C,   # jaune Discord
    "info":     0x5865F2,   # bleu Discord (blurple)
    "sys":      0xEB459E,   # rose vif  -> Sys+
    "orange":   0xFF6B35,   # orange    -> derank / actions lourdes
    "maint":    0xFFA500,   # orange clair -> maintenance
    "dark":     0x2B2D31,   # quasi-noir -> panels
    "purple":   0x9B59B6,   # violet    -> VoiceVIP
    "teal":     0x1ABC9C,   # turquoise -> Server WL
}

def ts():
    """Timestamp Discord court."""
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

# ── Chargement WL ─────────────────────────────────────────────────────
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
        await ctx.reply(embed=embed_err("Les **Sys+** sont intouchables. Oublie ca. 😂"))
        return False
    return True

async def protection_check_i(i: discord.Interaction, target: discord.Member) -> bool:
    if target.id == OWNER_ID and not is_owner(i.user.id):
        await i.channel.send(embed=embed_err(f"{i.user.mention} T'as vraiment essayé de me touch ? 💀"))
        return False
    if is_sys_plus(target.id) and not is_sys_plus(i.user.id):
        await i.channel.send(embed=embed_err(f"{i.user.mention} Les **Sys+** sont intouchables. Oublie ca. 😂"))
        return False
    return True

def check_sys_plus():
    async def pred(ctx):
        if not is_sys_plus(ctx.author.id):
            await ctx.reply(embed=embed_err("Commande reservee aux **Sys+**."))
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
    print(f"[OK] {bot.user} connecte (ID: {bot.user.id})")
    await bot.change_presence(
        status=discord.Status.online,
        activity=discord.Activity(type=discord.ActivityType.watching, name="Shotojo 🌸 #🇯🇵")
    )

@bot.event
async def on_member_update(before, after):
    if after.id in locked_nicks and after.nick != "S":
        try: await after.edit(nick="S")
        except: pass

@bot.event
async def on_voice_state_update(member, before, after):
    guild = member.guild

    # Follow
    for fid, tid in list(follow_active.items()):
        if member.id == tid and after.channel and after.channel != before.channel:
            follower = guild.get_member(fid)
            if follower and follower.voice and follower.voice.channel != after.channel:
                try: await follower.move_to(after.channel)
                except: pass

    # Dog
    for oid, (cid, _, _) in list(dog_active.items()):
        if member.id == oid and after.channel and after.channel != before.channel:
            cible = guild.get_member(cid)
            if cible:
                try: await cible.move_to(after.channel)
                except: pass

    # Menotte
    for oid, (cid, ch_id) in list(menotte_active.items()):
        if member.id == cid and before.channel and before.channel.id == ch_id and after.channel != before.channel:
            locked_ch = guild.get_channel(ch_id)
            if locked_ch:
                async def remmenotter(m=member, ch=locked_ch):
                    await asyncio.sleep(0.3)
                    try: await m.move_to(ch)
                    except: pass
                asyncio.create_task(remmenotter())

    # Vocal privee - entree
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
                "normal":  "🔒 Vocal privee",
                "sys":     "🔒 Vocal privee Sys",
                "sysplus": "🔒 Vocal privee Sys+",
            }
            try:
                await member.move_to(None)
                e = embed_err(title=labels.get(pv_type, "Vocal privee"), desc="Tu n'as pas acces a ce salon vocal.")
                set_footer(e)
                await member.send(embed=e)
            except: pass

    # Vocal privee - sortie owner
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
            title="🔧  Maintenance activee",
            description="Toutes les commandes sont **bloquees** pour les non-Sys+.\nLe bot reviendra bientot.",
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
        e = embed_ok(title="Maintenance desactivee", desc="Le bot est de retour, tout est disponible.")
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
            await i.response.send_message(embed=embed_err("Ce panel ne t'appartient pas."), ephemeral=True)
            return False
        return True

    async def give(self, i: discord.Interaction, wl: str):
        icon, label, color = WL_LABELS[wl]
        lst = whitelisted.setdefault(self.target.id, [])
        if wl in lst:
            return await i.response.send_message(
                embed=embed_warn(f"{self.target.mention} a deja la **{label}**."), ephemeral=True)
        lst.append(wl)
        save_wl()
        e = discord.Embed(
            title=f"{icon}  WL attribuee",
            description=f"{self.target.mention} vient de recevoir la **{label}**.",
            color=color, timestamp=datetime.utcnow()
        )
        e.set_thumbnail(url=self.target.display_avatar.url)
        set_footer(e, i.user)
        await i.response.send_message(embed=e)
        try:
            dm = discord.Embed(
                title=f"{icon}  Nouvelle whitelist !",
                description=f"Tu as recu la **{label}** sur **{i.guild.name}**.",
                color=color, timestamp=datetime.utcnow()
            )
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
    e = discord.Embed(
        title="📋  Panel Whitelist",
        color=C["dark"],
        timestamp=datetime.utcnow()
    )
    e.set_author(name=member.display_name, icon_url=member.display_avatar.url)
    e.add_field(name="WL actuelles", value=wl_display, inline=False)
    e.set_thumbnail(url=member.display_avatar.url)
    set_footer(e, ctx.author)
    await ctx.reply(embed=e, view=WLView(member, ctx.author.id))

# ══════════════════════════════════════════════════════════════════════
#  SUBPANELS WLPANEL
# ══════════════════════════════════════════════════════════════════════
class PVSubPanel(discord.ui.View):
    def __init__(self, guild): super().__init__(timeout=60); self.guild = guild

    @discord.ui.button(label="🔓 Deprivatiser", style=discord.ButtonStyle.red)
    async def remove_pv(self, i, b):
        if not private_vocs:
            return await i.response.send_message(embed=embed_warn("Aucune vocal privee active."), ephemeral=True)
        opts = [discord.SelectOption(
            label=f"#{self.guild.get_channel(cid).name if self.guild.get_channel(cid) else cid}  [{info['type']}]",
            value=str(cid)) for cid, info in private_vocs.items()]
        v = discord.ui.View(); v.add_item(PVRemoveSelect(opts, self.guild))
        await i.response.send_message(embed=embed_info("Choisis la vocal a deprivatiser :"), view=v, ephemeral=True)

    @discord.ui.button(label="📋 Lister", style=discord.ButtonStyle.grey)
    async def list_pv(self, i, b):
        if not private_vocs:
            return await i.response.send_message(embed=embed_warn("Aucune vocal privee active."), ephemeral=True)
        lines = []
        for cid, info in private_vocs.items():
            ch = self.guild.get_channel(cid)
            ow = self.guild.get_member(info["owner"])
            lines.append(f"> **#{ch.name if ch else cid}**  `{info['type']}`  •  {ow.mention if ow else info['owner']}")
        e = embed_info("\n".join(lines), title=f"🔒 Vocaux prives ({len(private_vocs)})")
        await i.response.send_message(embed=e, ephemeral=True)

class PVRemoveSelect(discord.ui.Select):
    def __init__(self, opts, guild): super().__init__(placeholder="Selectionner...", options=opts); self.guild = guild
    async def callback(self, i):
        cid = int(self.values[0])
        private_vocs.pop(cid, None); pv_access.pop(cid, None)
        ch = self.guild.get_channel(cid)
        await i.response.send_message(embed=embed_ok(f"**#{ch.name if ch else cid}** est maintenant publique."), ephemeral=True)

class LaisseSubPanel(discord.ui.View):
    def __init__(self, guild): super().__init__(timeout=60); self.guild = guild

    @discord.ui.button(label="🔓 Retirer une laisse", style=discord.ButtonStyle.red)
    async def remove(self, i, b):
        if not laisse_active:
            return await i.response.send_message(embed=embed_warn("Aucune laisse active."), ephemeral=True)
        opts = []
        for oid, (cid, _, _) in laisse_active.items():
            ow = self.guild.get_member(oid); ci = self.guild.get_member(cid)
            opts.append(discord.SelectOption(
                label=f"{ow.display_name if ow else oid}  ->  {ci.display_name if ci else cid}", value=str(oid)))
        v = discord.ui.View(); v.add_item(LaisseRemoveSelect(opts, self.guild))
        await i.response.send_message(embed=embed_info("Choisis la laisse a retirer :"), view=v, ephemeral=True)

    @discord.ui.button(label="📋 Lister", style=discord.ButtonStyle.grey)
    async def list_l(self, i, b):
        if not laisse_active:
            return await i.response.send_message(embed=embed_warn("Aucune laisse active."), ephemeral=True)
        lines = [f"> {self.guild.get_member(o).mention if self.guild.get_member(o) else o}  ->  {self.guild.get_member(c).mention if self.guild.get_member(c) else c}" for o,(c,_,_) in laisse_active.items()]
        e = embed_info("\n".join(lines), title=f"🐕 Laisses actives ({len(laisse_active)})")
        await i.response.send_message(embed=e, ephemeral=True)

class LaisseRemoveSelect(discord.ui.Select):
    def __init__(self, opts, guild): super().__init__(placeholder="Selectionner...", options=opts); self.guild = guild
    async def callback(self, i):
        oid   = int(self.values[0])
        entry = laisse_active.pop(oid, None)
        if entry:
            m = self.guild.get_member(entry[0])
            if m:
                try: await m.edit(nick=entry[2])
                except: pass
        await i.response.send_message(embed=embed_ok("Laisse retiree avec succes."), ephemeral=True)

class FollowSubPanel(discord.ui.View):
    def __init__(self, guild): super().__init__(timeout=60); self.guild = guild

    @discord.ui.button(label="🚫 Retirer un follow", style=discord.ButtonStyle.red)
    async def remove(self, i, b):
        if not follow_active:
            return await i.response.send_message(embed=embed_warn("Aucun follow actif."), ephemeral=True)
        opts = []
        for fid, tid in follow_active.items():
            f = self.guild.get_member(fid); t = self.guild.get_member(tid)
            opts.append(discord.SelectOption(
                label=f"{f.display_name if f else fid}  suit  {t.display_name if t else tid}", value=str(fid)))
        v = discord.ui.View(); v.add_item(FollowRemoveSelect(opts))
        await i.response.send_message(embed=embed_info("Choisis le follow a retirer :"), view=v, ephemeral=True)

    @discord.ui.button(label="📋 Lister", style=discord.ButtonStyle.grey)
    async def list_f(self, i, b):
        if not follow_active:
            return await i.response.send_message(embed=embed_warn("Aucun follow actif."), ephemeral=True)
        lines = [f"> {self.guild.get_member(f).mention if self.guild.get_member(f) else f}  suit  {self.guild.get_member(t).mention if self.guild.get_member(t) else t}" for f,t in follow_active.items()]
        e = embed_info("\n".join(lines), title=f"🏃 Follows actifs ({len(follow_active)})")
        await i.response.send_message(embed=e, ephemeral=True)

class FollowRemoveSelect(discord.ui.Select):
    def __init__(self, opts): super().__init__(placeholder="Selectionner...", options=opts)
    async def callback(self, i):
        follow_active.pop(int(self.values[0]), None)
        await i.response.send_message(embed=embed_ok("Follow retire avec succes."), ephemeral=True)

class WLSubPanel(discord.ui.View):
    def __init__(self, guild): super().__init__(timeout=60); self.guild = guild

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
                    label=f"{m.display_name if m else uid}  -  {icon} {wl}", value=f"{uid}:{wl}"))
        v = discord.ui.View(); v.add_item(WLRemoveSelect(opts, self.guild))
        await i.response.send_message(embed=embed_info("Choisis la WL a retirer :"), view=v, ephemeral=True)

    @discord.ui.button(label="📋 Lister", style=discord.ButtonStyle.grey)
    async def list_wl(self, i, b):
        if not whitelisted:
            return await i.response.send_message(embed=embed_warn("Aucune WL active."), ephemeral=True)
        lines = []
        for uid, wls in whitelisted.items():
            m = self.guild.get_member(uid)
            badges = "  ".join(f"{WL_LABELS.get(w,('•',w,0))[0]} `{w}`" for w in wls)
            lines.append(f"> **{m.display_name if m else uid}**  ->  {badges}")
        e = embed_info("\n".join(lines), title="👥 Whitelists actives")
        await i.response.send_message(embed=e, ephemeral=True)

class WLRemoveSelect(discord.ui.Select):
    def __init__(self, opts, guild): super().__init__(placeholder="Selectionner...", options=opts); self.guild = guild
    async def callback(self, i):
        uid_s, wl = self.values[0].split(":")
        uid = int(uid_s)
        if uid in whitelisted and wl in whitelisted[uid]:
            whitelisted[uid].remove(wl)
            if not whitelisted[uid]: del whitelisted[uid]
            save_wl()
        m    = self.guild.get_member(uid)
        icon, label, color = WL_LABELS.get(wl, ("•", wl, C["error"]))
        e = embed_ok(f"La **{label}** a ete retiree a **{m.display_name if m else uid}**.")
        set_footer(e, i.user)
        await i.response.send_message(embed=e, ephemeral=True)
        if m:
            try:
                dm = discord.Embed(
                    title=f"🚫  Whitelist retiree",
                    description=f"Ta **{label}** t'a ete retiree sur **{i.guild.name}**.",
                    color=C["error"], timestamp=datetime.utcnow()
                )
                dm.set_thumbnail(url=i.guild.icon.url if i.guild.icon else None)
                set_footer(dm)
                await m.send(embed=dm)
            except: pass

# ══════════════════════════════════════════════════════════════════════
#  PANEL PRINCIPAL - &wlpanel
# ══════════════════════════════════════════════════════════════════════
class VoiceVIPMainPanel(discord.ui.View):
    def __init__(self, guild): super().__init__(timeout=120); self.guild = guild

    @discord.ui.button(label="🔒 Vocs Privees", style=discord.ButtonStyle.blurple, row=0)
    async def pv(self, i, b):
        e = embed_info(f"**{len(private_vocs)}** vocal(s) privee(s) active(s).", title="🔒 Vocaux Prives", color=C["purple"])
        await i.response.send_message(embed=e, view=PVSubPanel(self.guild), ephemeral=True)

    @discord.ui.button(label="🐕 Laisses", style=discord.ButtonStyle.blurple, row=0)
    async def laisse(self, i, b):
        e = embed_info(f"**{len(laisse_active)}** laisse(s) active(s).", title="🐕 Laisses", color=C["orange"])
        await i.response.send_message(embed=e, view=LaisseSubPanel(self.guild), ephemeral=True)

    @discord.ui.button(label="🏃 Follows", style=discord.ButtonStyle.blurple, row=0)
    async def follow(self, i, b):
        e = embed_info(f"**{len(follow_active)}** follow(s) actif(s).", title="🏃 Follows", color=C["teal"])
        await i.response.send_message(embed=e, view=FollowSubPanel(self.guild), ephemeral=True)

    @discord.ui.button(label="👥 Whitelists", style=discord.ButtonStyle.blurple, row=0)
    async def wl(self, i, b):
        total = sum(len(v) for v in whitelisted.values())
        e = embed_info(f"**{total}** WL active(s) au total.", title="👥 Whitelists", color=C["sys"])
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
    status_txt  = "**EN MAINTENANCE**" if maintenance else "**Operationnel**"

    e = discord.Embed(
        title="🎛️  Panel de controle - Sys+",
        color=C["maint"] if maintenance else C["dark"],
        timestamp=datetime.utcnow()
    )
    e.add_field(name=f"{status_icon} Statut", value=status_txt, inline=False)
    e.add_field(name="🎤 VoiceVIP",    value=f"`{len(voicevip_p)}` membres", inline=True)
    e.add_field(name="🌐 Server",      value=f"`{len(server_p)}` membres",   inline=True)
    e.add_field(name="⚡ WL Sys",      value=f"`{len(sys_p)}` membres",      inline=True)
    e.add_field(name="👑 Privilege",   value=f"`{len(priv_p)}` membres",     inline=True)
    e.add_field(name="🔒 Vocs priv.",  value=f"`{len(private_vocs)}`",       inline=True)
    e.add_field(name="🐕 Laisses",     value=f"`{len(laisse_active)}`",      inline=True)
    e.add_field(name="🏃 Follows",     value=f"`{len(follow_active)}`",      inline=True)
    e.add_field(name="\u200b", value="\u200b", inline=True)
    set_footer(e)
    return e

@bot.command(name="wlpanel")
@check_sys_plus()
async def wlpanel_cmd(ctx):
    await ctx.reply(embed=build_wlpanel_embed(ctx.guild), view=VoiceVIPMainPanel(ctx.guild))

@bot.command(name="restartpanel")
@check_sys_plus()
async def restartpanel_cmd(ctx):
    e = build_wlpanel_embed(ctx.guild)
    e.title = "🔄  Panel redémarre"
    await ctx.reply(embed=e, view=VoiceVIPMainPanel(ctx.guild))

# ══════════════════════════════════════════════════════════════════════
#  COMMANDES SYS+ - &clear / &derank
# ══════════════════════════════════════════════════════════════════════
@bot.command(name="clear")
@check_sys_plus()
async def clear_cmd(ctx, amount: int = 50):
    if not 1 <= amount <= 500:
        return await ctx.reply(embed=embed_err("Le montant doit etre entre **1** et **500**."))
    deleted = await ctx.channel.purge(limit=amount + 1)
    e = embed_ok(f"**{len(deleted)-1}** message(s) supprime(s).")
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
        return await ctx.reply(embed=embed_err("Tu ne peux pas te derank toi-meme."))
    if not await protection_check(ctx, member): return
    if member.top_role >= ctx.guild.me.top_role:
        return await ctx.reply(embed=embed_err("Son role est trop haut pour moi."))
    roles = [r for r in member.roles if r != ctx.guild.default_role and r < ctx.guild.me.top_role]
    if not roles:
        return await ctx.reply(embed=embed_warn(f"{member.mention} n'a aucun role a retirer."))
    await member.remove_roles(*roles, reason=f"Derank par {ctx.author} - {reason}")
    e = discord.Embed(title="🔨  Derank execute", color=C["orange"], timestamp=datetime.utcnow())
    e.set_author(name=member.display_name, icon_url=member.display_avatar.url)
    e.add_field(name="Membre", value=member.mention,    inline=True)
    e.add_field(name="Par",    value=ctx.author.mention, inline=True)
    e.add_field(name="Raison", value=f"*{reason}*",     inline=False)
    set_footer(e, ctx.author)
    await ctx.reply(embed=e)
    try:
        dm = discord.Embed(
            title="⚠️  Tu as ete derank",
            description=f"Tous tes roles ont ete retires sur **{ctx.guild.name}**.\n\n> *{reason}*",
            color=C["orange"], timestamp=datetime.utcnow()
        )
        set_footer(dm)
        await member.send(embed=dm)
    except: pass

# ══════════════════════════════════════════════════════════════════════
#  /addrole - Ajouter un role (Sys+)
# ══════════════════════════════════════════════════════════════════════
@tree.command(name="addrole", description="Ajouter un role a un membre ou a tout le serveur (Sys+)")
@app_commands.describe(role="Le role a ajouter", tous="Ajouter a tous les membres ?", membre="Le membre cible")
async def addrole_slash(i: discord.Interaction, role: discord.Role, tous: bool, membre: discord.Member = None):
    if not is_sys_plus(i.user.id):
        return await i.response.send_message(embed=embed_err("Commande reservee aux **Sys+**."), ephemeral=True)
    if role >= i.guild.me.top_role:
        return await i.response.send_message(embed=embed_err("Ce role est trop haut pour moi."), ephemeral=True)

    if tous:
        await i.response.defer(thinking=True)
        targets = [m for m in i.guild.members if not m.bot and role not in m.roles]
        ok, fail = 0, 0
        for m in targets:
            try:    await m.add_roles(role, reason=f"/addrole tous - par {i.user}"); ok += 1
            except: fail += 1
        e = discord.Embed(title="✅  Role ajoute - Serveur entier", color=C["ok"], timestamp=datetime.utcnow())
        e.add_field(name="Role",    value=role.mention, inline=True)
        e.add_field(name="Reussi", value=f"`{ok}`",    inline=True)
        e.add_field(name="Echec",  value=f"`{fail}`",  inline=True)
        set_footer(e, i.user)
        await i.followup.send(embed=e)
    else:
        if not membre:
            return await i.response.send_message(embed=embed_err("Precise un membre ou active **tous**."), ephemeral=True)
        if not await protection_check_i(i, membre): return
        if role in membre.roles:
            return await i.response.send_message(embed=embed_warn(f"{membre.mention} a deja ce role."), ephemeral=True)
        try:
            await membre.add_roles(role, reason=f"/addrole - par {i.user}")
            e = embed_ok(title="Role ajoute")
            e.add_field(name="Membre", value=membre.mention, inline=True)
            e.add_field(name="Role",   value=role.mention,   inline=True)
            set_footer(e, i.user)
            await i.response.send_message(embed=e)
        except discord.Forbidden:
            await i.response.send_message(embed=embed_err("Impossible d'ajouter ce role."), ephemeral=True)

# ══════════════════════════════════════════════════════════════════════
#  /removerole - Retirer un role (Sys+)
# ══════════════════════════════════════════════════════════════════════
@tree.command(name="removerole", description="Retirer un role a un membre ou a tout le serveur (Sys+)")
@app_commands.describe(role="Le role a retirer", tous="Retirer a tous les membres ?", membre="Le membre cible")
async def removerole_slash(i: discord.Interaction, role: discord.Role, tous: bool, membre: discord.Member = None):
    if not is_sys_plus(i.user.id):
        return await i.response.send_message(embed=embed_err("Commande reservee aux **Sys+**."), ephemeral=True)
    if role >= i.guild.me.top_role:
        return await i.response.send_message(embed=embed_err("Ce role est trop haut pour moi."), ephemeral=True)

    if tous:
        await i.response.defer(thinking=True)
        targets = [m for m in i.guild.members if not m.bot and role in m.roles]
        ok, fail = 0, 0
        for m in targets:
            try:    await m.remove_roles(role, reason=f"/removerole tous - par {i.user}"); ok += 1
            except: fail += 1
        e = discord.Embed(title="✅  Role retire - Serveur entier", color=C["orange"], timestamp=datetime.utcnow())
        e.add_field(name="Role",    value=role.mention, inline=True)
        e.add_field(name="Reussi", value=f"`{ok}`",    inline=True)
        e.add_field(name="Echec",  value=f"`{fail}`",  inline=True)
        set_footer(e, i.user)
        await i.followup.send(embed=e)
    else:
        if not membre:
            return await i.response.send_message(embed=embed_err("Precise un membre ou active **tous**."), ephemeral=True)
        if not await protection_check_i(i, membre): return
        if role not in membre.roles:
            return await i.response.send_message(embed=embed_warn(f"{membre.mention} n'a pas ce role."), ephemeral=True)
        try:
            await membre.remove_roles(role, reason=f"/removerole - par {i.user}")
            e = discord.Embed(title="✅  Role retire", color=C["orange"], timestamp=datetime.utcnow())
            e.add_field(name="Membre", value=membre.mention, inline=True)
            e.add_field(name="Role",   value=role.mention,   inline=True)
            set_footer(e, i.user)
            await i.response.send_message(embed=e)
        except discord.Forbidden:
            await i.response.send_message(embed=embed_err("Impossible de retirer ce role."), ephemeral=True)

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
        try: await member.edit(nick=on)
        except: pass
        e = embed_warn(f"Laisse retiree a {member.mention}.")
        set_footer(e, ctx.author)
        return await ctx.reply(embed=e)

    if oid in laisse_active:
        return await ctx.reply(embed=embed_err("Tu as deja une laisse active."))
    for o, (cid, _, _) in laisse_active.items():
        if cid == member.id:
            return await ctx.reply(embed=embed_err("Cette personne a deja la laisse de quelqu'un d'autre."))

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
        private_vocs.pop(cid); pv_access.pop(cid, None)
        e = embed_ok("Vocal rendue **publique**.")
        set_footer(e, ctx.author)
        return await ctx.reply(embed=e)

    user_pvs = [c for c, info in private_vocs.items() if info["owner"] == ctx.author.id]
    max_pvs  = 99 if is_sys_plus(ctx.author.id) else 2
    if len(user_pvs) >= max_pvs:
        return await ctx.reply(embed=embed_err(f"Tu as deja **{max_pvs}** vocal(s) privee(s) max."))

    pv_type = "sysplus" if is_sys_plus(ctx.author.id) else ("sys" if has_wl_sys(ctx.author.id) else "normal")
    private_vocs[cid] = {"owner": ctx.author.id, "type": pv_type}
    pv_access[cid]    = set()

    labels = {"normal": "normale", "sys": "Sys", "sysplus": "Sys+"}
    e = discord.Embed(
        title=f"🔒  Vocal privee [{labels[pv_type]}]",
        description=f"**{ctx.author.voice.channel.name}** est maintenant privee.",
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
        return await ctx.reply(embed=embed_err("Ce n'est pas ta vocal privee."))
    acc = pv_access.setdefault(cid, set())
    if member.id in acc:
        acc.discard(member.id)
        e = embed_warn(f"Acces retire a **{member.display_name}**.")
        set_footer(e, ctx.author)
        return await ctx.reply(embed=e)
    acc.add(member.id)
    e = embed_ok(f"**{member.display_name}** peut maintenant rejoindre ta vocal privee.")
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
        await ctx.reply(embed=embed_err("Impossible de te deplacer."))

@bot.command(name="mv")
@check_voicevip()
async def mv_cmd(ctx, member: discord.Member = None, channel: discord.VoiceChannel = None):
    if not member or not channel:
        return await ctx.reply(embed=embed_err("Usage : `=mv @membre #vocal`"))
    if not await protection_check(ctx, member): return
    try:
        await member.move_to(channel)
        e = embed_ok(f"**{member.display_name}** deplace dans **{channel.name}**.")
        set_footer(e, ctx.author)
        await ctx.reply(embed=e)
    except discord.Forbidden:
        await ctx.reply(embed=embed_err("Impossible de deplacer ce membre."))

@bot.command(name="pvlist")
@check_voicevip()
async def pvlist_cmd(ctx):
    if not private_vocs:
        return await ctx.reply(embed=embed_warn("Aucune vocal privee active."))
    e = discord.Embed(title="🔒  Vocaux prives actifs", color=C["purple"], timestamp=datetime.utcnow())
    for cid, info in private_vocs.items():
        ch  = ctx.guild.get_channel(cid)
        ow  = ctx.guild.get_member(info["owner"])
        acc = [ctx.guild.get_member(u) for u in pv_access.get(cid, set())]
        acc_str = ", ".join(m.display_name for m in acc if m) or "*Personne*"
        e.add_field(
            name=f"#{ch.name if ch else cid}  [{info['type']}]",
            value=f"Owner : {ow.mention if ow else info['owner']}\nAcces : {acc_str}",
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
        e = embed_warn(f"Menotte retiree a {member.mention}.")
        set_footer(e, ctx.author)
        return await ctx.reply(embed=e)
    if oid in menotte_active:
        return await ctx.reply(embed=embed_err("Tu as deja une menotte active."))
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
        title="⛓️  Menotte posee",
        description=f"{member.mention} est desormais menotté dans **{member.voice.channel.name}**.",
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
        e = embed_warn(f"Follow sur **{member.display_name}** retire.")
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
        private_vocs.pop(cid); pv_access.pop(cid, None)
        e = embed_ok("PV Sys desactivee, vocal rendue publique.")
        set_footer(e, ctx.author)
        return await ctx.reply(embed=e)
    user_pvs = [c for c, info in private_vocs.items() if info["owner"] == ctx.author.id]
    if len(user_pvs) >= 2 and not is_sys_plus(ctx.author.id):
        return await ctx.reply(embed=embed_err("Maximum **2** vocaux prives."))
    private_vocs[cid] = {"owner": ctx.author.id, "type": "sys"}
    pv_access[cid]    = set()
    e = discord.Embed(
        title="🔒  Vocal privee Sys",
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
        e = embed_ok(f"Message envoye anonymement a {member.mention}.")
        set_footer(e, ctx.author)
        await ctx.reply(embed=e)
    except discord.Forbidden:
        await ctx.reply(embed=embed_err("Impossible d'envoyer le MP (DMs fermes)."))

@tree.command(name="dog-add", description="Dog quelqu'un - il te suit partout en vocal (Server WL)")
@app_commands.describe(membre="La personne a dog")
async def dog_add(i: discord.Interaction, membre: discord.Member):
    if maintenance and not is_sys_plus(i.user.id):
        return await i.response.send_message(embed=embed_warn("Le bot est en **maintenance**."), ephemeral=True)
    if not has_server(i.user.id):
        return await i.response.send_message(embed=embed_err("Tu n'as pas la **Server WL**."), ephemeral=True)
    if not await protection_check_i(i, membre): return
    oid = i.user.id
    now = time.time()
    if oid in dog_active and dog_active[oid][0] == membre.id:
        return await i.response.send_message(embed=embed_warn("Cette personne est deja ton dog."), ephemeral=True)
    if oid in dog_active:
        return await i.response.send_message(embed=embed_err("Tu as deja un dog actif. Fais `/dog-del` d'abord."), ephemeral=True)
    if not is_sys_plus(oid):
        last = dog_cd.get(oid, 0)
        if now - last < 60:
            return await i.response.send_message(embed=embed_warn(f"Cooldown dog : encore **{int(60-(now-last))}s**."), ephemeral=True)
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
        try: await m.edit(nick=old)
        except: pass
    e = embed_warn("Dog retire avec succes.")
    set_footer(e, i.user)
    await i.response.send_message(embed=e)

class WakeupModal(discord.ui.Modal, title="Wakeup"):
    message = discord.ui.TextInput(
        label="Message personnalise (optionnel)",
        placeholder="Laisse vide pour le message par defaut",
        required=False,
        max_length=200
    )
    def __init__(self, target: discord.Member, invoker: discord.Member):
        super().__init__(); self.target = target; self.invoker = invoker

    async def on_submit(self, i: discord.Interaction):
        if not await protection_check_i(i, self.target): return
        now = time.time()
        if not is_sys_plus(self.invoker.id):
            last = wakeup_cd.get(self.invoker.id, 0)
            if now - last < 300:
                return await i.response.send_message(
                    embed=embed_warn(f"Cooldown wakeup : encore **{int(300-(now-last))}s**."), ephemeral=True)
        if self.target.id in wakeup_active:
            return await i.response.send_message(embed=embed_err("Cette personne est deja en wakeup."), ephemeral=True)

        custom   = self.message.value.strip()
        spam_msg = (f"{self.target.mention} {custom}" if custom
                    else f"Reveille toi {self.target.mention} ! C'est {self.invoker.mention} qui te l'ordonne 😈")
        wakeup_active.add(self.target.id)
        wakeup_cd[self.invoker.id] = now

        e = embed_ok(f"Wakeup lance sur {self.target.mention} !")
        set_footer(e, self.invoker)
        await i.response.send_message(embed=e, ephemeral=True)

        async def do_wakeup():
            end = asyncio.get_event_loop().time() + 10
            async def spam():
                for _ in range(20):
                    try: await self.target.send(spam_msg)
                    except: pass
                    await asyncio.sleep(0.5)
            asyncio.create_task(spam())
            vcs = list(i.guild.voice_channels)
            while asyncio.get_event_loop().time() < end:
                if self.target.voice and vcs:
                    try: await self.target.move_to(random.choice(vcs))
                    except: pass
                await asyncio.sleep(0.3)
            try: await self.target.move_to(None)
            except: pass
            wakeup_active.discard(self.target.id)
        asyncio.create_task(do_wakeup())

@tree.command(name="wakeup", description="Wakeup un membre - spam + deplace en vocal (Server WL)")
@app_commands.describe(membre="Le membre a wakeup")
async def wakeup_slash(i: discord.Interaction, membre: discord.Member):
    if maintenance and not is_sys_plus(i.user.id):
        return await i.response.send_message(embed=embed_warn("Le bot est en **maintenance**."), ephemeral=True)
    if not has_server(i.user.id):
        return await i.response.send_message(embed=embed_err("Tu n'as pas la **Server WL**."), ephemeral=True)
    await i.response.send_modal(WakeupModal(membre, i.user))

class SnapResponseModal(discord.ui.Modal, title="Donner mon Snapchat"):
    snap = discord.ui.TextInput(label="Ton Snapchat", placeholder="ton_snap", max_length=50)
    def __init__(self, demandeur: discord.Member):
        super().__init__(); self.demandeur = demandeur

    async def on_submit(self, i: discord.Interaction):
        e = discord.Embed(title="📸  Snap recu !", color=C["warn"], timestamp=datetime.utcnow())
        e.add_field(name="De",       value=i.user.mention)
        e.add_field(name="Snapchat", value=f"`{self.snap.value}`")
        e.set_thumbnail(url=i.user.display_avatar.url)
        set_footer(e)
        try:
            await self.demandeur.send(embed=e)
            await i.response.send_message(embed=embed_ok("Ton snap a ete envoye !"), ephemeral=True)
        except:
            await i.response.send_message(embed=embed_err("Impossible d'envoyer le snap (DMs fermes)."), ephemeral=True)

class SnapView(discord.ui.View):
    def __init__(self, demandeur: discord.Member):
        super().__init__(timeout=300); self.demandeur = demandeur

    @discord.ui.button(label="📸  Donner mon Snap", style=discord.ButtonStyle.blurple)
    async def give_snap(self, i, b):
        await i.response.send_modal(SnapResponseModal(self.demandeur))

@tree.command(name="snap", description="Demander le snap de quelqu'un (Server WL)")
@app_commands.describe(membre="La personne a qui demander", message="Ton petit message (optionnel)")
async def snap_slash(i: discord.Interaction, membre: discord.Member, message: str = ""):
    if maintenance and not is_sys_plus(i.user.id):
        return await i.response.send_message(embed=embed_warn("Le bot est en **maintenance**."), ephemeral=True)
    if not has_server(i.user.id):
        return await i.response.send_message(embed=embed_err("Tu n'as pas la **Server WL**."), ephemeral=True)
    e = discord.Embed(
        title="📸  Quelqu'un veut ton Snap !",
        color=C["warn"], timestamp=datetime.utcnow()
    )
    e.set_author(name=i.user.display_name, icon_url=i.user.display_avatar.url)
    if message:
        e.add_field(name="Message", value=f"*{message}*", inline=False)
    e.set_footer(text="Clique sur le bouton si tu veux partager ton snap.")
    try:
        await membre.send(embed=e, view=SnapView(i.user))
        await i.response.send_message(embed=embed_ok(f"Demande envoyee a {membre.mention} !"), ephemeral=True)
    except:
        await i.response.send_message(embed=embed_err("Impossible d'envoyer le MP (DMs fermes)."), ephemeral=True)

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
        try: await membre.edit(nick=None)
        except: pass
        e = embed_warn(f"Pseudo de {membre.mention} deverrouille.")
        set_footer(e, i.user)
        return await i.response.send_message(embed=e)
    try:
        await membre.edit(nick="S")
        locked_nicks.add(membre.id)
        e = discord.Embed(
            title="🔒  Pseudo verrouille",
            description=f"{membre.mention} a ete renomme **S** et son pseudo est desormais verrouille.",
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
        e.description = "> 🔴 **Maintenance active.** Seuls les Sys+ ont acces aux commandes."

    if is_sys_plus(ctx.author.id):
        e.add_field(
            name="⭐  Sys+  [ & ]",
            value="`&wl`  `&wlpanel`  `&restartpanel`  `&maintenance`  `&clear`  `&derank`\n`/addrole`  `/removerole`\n*+ toutes les commandes = et /*",
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
        e.description = "> Tu n'as acces a aucune commande."

    e.set_thumbnail(url=ctx.guild.icon.url if ctx.guild.icon else None)
    set_footer(e, ctx.author)
    await ctx.reply(embed=e)

# ══════════════════════════════════════════════════════════════════════
#  LANCEMENT
# ══════════════════════════════════════════════════════════════════════
bot.run(os.environ["TOKEN"])
