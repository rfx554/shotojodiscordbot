import os
import json
import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import random
import time

# ════════════════════════════════════════════════════════════════
#  CONFIGURATION
# ════════════════════════════════════════════════════════════════
OWNER_ID = 1419320803199029402  # secret, invulnérable à tous

SYS_PLUS_IDS = {
    1419320803199029402,
    1514099294611701842,
}

WL_FILE = "whitelisted.json"

def load_wl():
    if os.path.exists(WL_FILE):
        try:
            with open(WL_FILE, "r") as f:
                data = json.load(f)
                return {int(k): v for k, v in data.items()}
        except: pass
    return {}

def save_wl():
    with open(WL_FILE, "w") as f:
        json.dump({str(k): v for k, v in whitelisted.items()}, f)

# ════════════════════════════════════════════════════════════════
#  STOCKAGE MÉMOIRE
# ════════════════════════════════════════════════════════════════
whitelisted   = load_wl()
private_vocs  = {}
pv_access     = {}
follow_active = {}
laisse_active = {}
dog_active    = {}
menotte_active= {}
wakeup_active = set()
wakeup_cd     = {}
dog_cd        = {}
menotte_cd    = {}
locked_nicks  = set()
maintenance   = False  # ← mode maintenance

# ════════════════════════════════════════════════════════════════
#  PRÉFIXES
# ════════════════════════════════════════════════════════════════
async def get_prefix(bot, message):
    return ["&", "="]

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=get_prefix, intents=intents, help_command=None)
tree = bot.tree

# ════════════════════════════════════════════════════════════════
#  HELPERS / CHECKS
# ════════════════════════════════════════════════════════════════
def is_owner(uid):    return uid == OWNER_ID
def is_sys_plus(uid): return uid in SYS_PLUS_IDS
def is_sys(uid):      return uid in SYS_PLUS_IDS or "sys" in whitelisted.get(uid, []) or bool(whitelisted.get(uid))
def has_wl(uid, t):   return uid in SYS_PLUS_IDS or t in whitelisted.get(uid, [])

def has_voicevip(uid):
    return uid in SYS_PLUS_IDS or "voicevip" in whitelisted.get(uid, []) or "sys" in whitelisted.get(uid, [])

def has_server(uid):
    return uid in SYS_PLUS_IDS or "server" in whitelisted.get(uid, [])

def has_wl_sys(uid):
    return uid in SYS_PLUS_IDS or "sys" in whitelisted.get(uid, [])

async def protection_check(ctx, target: discord.Member) -> bool:
    if target.id == OWNER_ID and not is_owner(ctx.author.id):
        await ctx.reply("J'ai codé ce bot et tu oses me toucher ? 💀😭")
        return False
    if is_sys_plus(target.id) and not is_sys_plus(ctx.author.id):
        await ctx.reply("Plus jamais de ta vie tu touches aux Sys+ ! 😂🤣")
        return False
    return True

async def protection_check_i(i: discord.Interaction, target: discord.Member) -> bool:
    if target.id == OWNER_ID and not is_owner(i.user.id):
        await i.channel.send(f"{i.user.mention} J'ai codé ce bot et tu oses me toucher ? 💀😭")
        return False
    if is_sys_plus(target.id) and not is_sys_plus(i.user.id):
        await i.channel.send(f"{i.user.mention} Plus jamais de ta vie tu touches aux Sys+ ! 😂🤣")
        return False
    return True

def check_sys_plus():
    async def pred(ctx):
        if not is_sys_plus(ctx.author.id):
            await ctx.reply(embed=discord.Embed(description="❌ Réservé aux **Sys+**.", color=0xFF0000))
            return False
        return True
    return commands.check(pred)

def check_voicevip():
    async def pred(ctx):
        if maintenance and not is_sys_plus(ctx.author.id):
            await ctx.reply(embed=discord.Embed(description="🔧 Le bot est en **maintenance**.", color=0xFFA500))
            return False
        if not has_voicevip(ctx.author.id):
            await ctx.reply(embed=discord.Embed(description="❌ Tu n'as pas la **VoiceVIP**.", color=0xFF0000))
            return False
        return True
    return commands.check(pred)

def check_server():
    async def pred(ctx):
        if maintenance and not is_sys_plus(ctx.author.id):
            await ctx.reply(embed=discord.Embed(description="🔧 Le bot est en **maintenance**.", color=0xFFA500))
            return False
        if not has_server(ctx.author.id):
            await ctx.reply(embed=discord.Embed(description="❌ Tu n'as pas la **Server WL**.", color=0xFF0000))
            return False
        return True
    return commands.check(pred)

def check_wl_sys():
    async def pred(ctx):
        if maintenance and not is_sys_plus(ctx.author.id):
            await ctx.reply(embed=discord.Embed(description="🔧 Le bot est en **maintenance**.", color=0xFFA500))
            return False
        if not has_wl_sys(ctx.author.id):
            await ctx.reply(embed=discord.Embed(description="❌ Tu n'as pas la **WL Sys**.", color=0xFF0000))
            return False
        return True
    return commands.check(pred)

# ════════════════════════════════════════════════════════════════
#  MIDDLEWARE MAINTENANCE (prefix commands)
# ════════════════════════════════════════════════════════════════
@bot.before_invoke
async def before_any_command(ctx):
    # &maintenance est toujours accessible aux Sys+
    if ctx.command and ctx.command.name == "maintenance":
        return
    if maintenance and not is_sys_plus(ctx.author.id):
        await ctx.reply(embed=discord.Embed(
            title="🔧 Maintenance",
            description="Le bot est actuellement en **maintenance**.\nReviens un peu plus tard !",
            color=0xFFA500))
        raise commands.CheckFailure("maintenance")

# ════════════════════════════════════════════════════════════════
#  EVENTS
# ════════════════════════════════════════════════════════════════
@bot.event
async def on_ready():
    await tree.sync()
    print(f"✅ {bot.user} connecté (ID: {bot.user.id})")
    await bot.change_presence(
        status=discord.Status.online,
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="Shotojo 🌸 #🇯🇵",
            state="Nous vous préparons de grandes choses"
        )
    )

@bot.event
async def on_member_update(before, after):
    if after.id in locked_nicks:
        if after.nick != "S":
            try: await after.edit(nick="S")
            except: pass

@bot.event
async def on_voice_state_update(member, before, after):
    guild = member.guild

    for fid, tid in list(follow_active.items()):
        if member.id == tid and after.channel and after.channel != before.channel:
            follower = guild.get_member(fid)
            if follower and follower.voice and follower.voice.channel != after.channel:
                try: await follower.move_to(after.channel)
                except: pass

    for oid, (cid, _, _) in list(dog_active.items()):
        if member.id == oid and after.channel and after.channel != before.channel:
            cible = guild.get_member(cid)
            if cible:
                try: await cible.move_to(after.channel)
                except: pass

    for oid, (cid, ch_id) in list(menotte_active.items()):
        if member.id == cid and before.channel and before.channel.id == ch_id and after.channel != before.channel:
            locked_ch = guild.get_channel(ch_id)
            if locked_ch:
                async def remmenotter(m=member, ch=locked_ch):
                    await asyncio.sleep(0.3)
                    try: await m.move_to(ch)
                    except: pass
                asyncio.create_task(remmenotter())

    if after.channel and after.channel.id in private_vocs:
        ch_id = after.channel.id
        pv_info = private_vocs[ch_id]
        owner_id = pv_info["owner"]
        pv_type = pv_info["type"]
        allowed = pv_access.get(ch_id, set()) | {owner_id}

        if member.id in allowed or is_owner(member.id) or is_sys_plus(member.id):
            pass
        elif pv_type == "normal":
            if has_wl_sys(member.id):
                pass
            else:
                try:
                    await member.move_to(None)
                    await member.send(embed=discord.Embed(
                        title="🔒 Vocal privée", description="Cette vocal est privée.", color=0xFF0000))
                except: pass
        elif pv_type == "sys":
            try:
                await member.move_to(None)
                await member.send(embed=discord.Embed(
                    title="🔒 Vocal privée Sys", description="Cette vocal est privée (Sys).", color=0xFF0000))
            except: pass
        elif pv_type == "sysplus":
            try:
                await member.move_to(None)
                await member.send(embed=discord.Embed(
                    title="🔒 Vocal privée Sys+", description="Cette vocal est privée (Sys+).", color=0xFF0000))
            except: pass

    if before.channel and before.channel.id in private_vocs:
        ch_id = before.channel.id
        if private_vocs[ch_id]["owner"] == member.id:
            private_vocs.pop(ch_id, None)
            pv_access.pop(ch_id, None)

# ════════════════════════════════════════════════════════════════
#  &maintenance - Sys+ uniquement
# ════════════════════════════════════════════════════════════════
@bot.command(name="maintenance")
@check_sys_plus()
async def maintenance_cmd(ctx):
    global maintenance
    maintenance = not maintenance
    if maintenance:
        await bot.change_presence(
            status=discord.Status.do_not_disturb,
            activity=discord.Game("🔧 Maintenance en cours")
        )
        await ctx.reply(embed=discord.Embed(
            title="🔧 Maintenance activée",
            description="Le bot est en **maintenance**.\nToutes les commandes sont bloquées pour les non-Sys+.",
            color=0xFFA500))
    else:
        await bot.change_presence(
            status=discord.Status.online,
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="Shotojo 🌸 #🇯🇵",
                state="Nous vous préparons de grandes choses"
            )
        )
        await ctx.reply(embed=discord.Embed(
            title="✅ Maintenance désactivée",
            description="Le bot est de retour, toutes les commandes sont disponibles.",
            color=0x00FF7F))

# ════════════════════════════════════════════════════════════════
#  &wl - Panel whitelist (Sys+)
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
        lst = whitelisted.setdefault(self.target.id, [])
        if wl in lst:
            return await i.response.send_message(f"⚠️ Déjà **{label}**.", ephemeral=True)
        lst.append(wl)
        save_wl()
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

    @discord.ui.button(label="⚡ WL Sys", style=discord.ButtonStyle.grey)
    async def wl_sys(self, i, b): await self.give(i, "sys", "WL Sys")

    @discord.ui.button(label="👑 Privilege", style=discord.ButtonStyle.red)
    async def privilege(self, i, b): await self.give(i, "privilege", "Privilege")

@bot.command(name="wl")
@check_sys_plus()
async def wl_cmd(ctx, member: discord.Member = None):
    if not member:
        return await ctx.reply(embed=discord.Embed(description="❌ `&wl @membre`", color=0xFF0000))
    wls = whitelisted.get(member.id, [])
    embed = discord.Embed(title=f"📋 Whitelist - {member.display_name}", color=0x5865F2)
    embed.add_field(name="WL actuelles", value=", ".join(wls) if wls else "Aucune")
    embed.set_thumbnail(url=member.display_avatar.url)
    await ctx.reply(embed=embed, view=WLView(member, ctx.author.id))

# ════════════════════════════════════════════════════════════════
#  &voicevip - Panel gestion (Sys+)
# ════════════════════════════════════════════════════════════════
class PVSubPanel(discord.ui.View):
    def __init__(self, guild): super().__init__(timeout=60); self.guild = guild

    @discord.ui.button(label="🔓 Retirer une voc privée", style=discord.ButtonStyle.red)
    async def remove_pv(self, i, b):
        if not private_vocs:
            return await i.response.send_message("Aucune voc privée.", ephemeral=True)
        opts = [discord.SelectOption(
            label=f"#{self.guild.get_channel(cid).name if self.guild.get_channel(cid) else cid} [{info['type']}]",
            value=str(cid)) for cid, info in private_vocs.items()]
        v = discord.ui.View(); v.add_item(PVRemoveSelect(opts, self.guild))
        await i.response.send_message("Choisis :", view=v, ephemeral=True)

    @discord.ui.button(label="📋 Voir toutes", style=discord.ButtonStyle.grey)
    async def list_pv(self, i, b):
        if not private_vocs:
            return await i.response.send_message("Aucune.", ephemeral=True)
        lines = []
        for cid, info in private_vocs.items():
            ch = self.guild.get_channel(cid)
            ow = self.guild.get_member(info["owner"])
            lines.append(f"**#{ch.name if ch else cid}** [{info['type']}] - {ow.display_name if ow else info['owner']}")
        await i.response.send_message("\n".join(lines), ephemeral=True)

class PVRemoveSelect(discord.ui.Select):
    def __init__(self, opts, guild): super().__init__(placeholder="Choisis...", options=opts); self.guild = guild
    async def callback(self, i):
        cid = int(self.values[0])
        private_vocs.pop(cid, None); pv_access.pop(cid, None)
        ch = self.guild.get_channel(cid)
        await i.response.send_message(f"✅ **#{ch.name if ch else cid}** déprivatisée.", ephemeral=True)

class LaisseSubPanel(discord.ui.View):
    def __init__(self, guild): super().__init__(timeout=60); self.guild = guild

    @discord.ui.button(label="🐕 Retirer une laisse", style=discord.ButtonStyle.red)
    async def remove(self, i, b):
        if not laisse_active:
            return await i.response.send_message("Aucune laisse.", ephemeral=True)
        opts = []
        for oid, (cid, nn, on) in laisse_active.items():
            ow = self.guild.get_member(oid); ci = self.guild.get_member(cid)
            opts.append(discord.SelectOption(label=f"{ow.display_name if ow else oid} → {ci.display_name if ci else cid}", value=str(oid)))
        v = discord.ui.View(); v.add_item(LaisseRemoveSelect(opts, self.guild))
        await i.response.send_message("Choisis :", view=v, ephemeral=True)

    @discord.ui.button(label="📋 Voir toutes", style=discord.ButtonStyle.grey)
    async def list_l(self, i, b):
        if not laisse_active:
            return await i.response.send_message("Aucune.", ephemeral=True)
        lines = [f"**{self.guild.get_member(o).display_name if self.guild.get_member(o) else o}** → **{self.guild.get_member(c).display_name if self.guild.get_member(c) else c}**" for o,(c,_,_) in laisse_active.items()]
        await i.response.send_message("\n".join(lines), ephemeral=True)

class LaisseRemoveSelect(discord.ui.Select):
    def __init__(self, opts, guild): super().__init__(placeholder="Choisis...", options=opts); self.guild = guild
    async def callback(self, i):
        oid = int(self.values[0])
        entry = laisse_active.pop(oid, None)
        if entry:
            m = self.guild.get_member(entry[0])
            if m:
                try: await m.edit(nick=entry[2])
                except: pass
        await i.response.send_message("✅ Laisse retirée.", ephemeral=True)

class FollowSubPanel(discord.ui.View):
    def __init__(self, guild): super().__init__(timeout=60); self.guild = guild

    @discord.ui.button(label="🚫 Retirer un follow", style=discord.ButtonStyle.red)
    async def remove(self, i, b):
        if not follow_active:
            return await i.response.send_message("Aucun follow.", ephemeral=True)
        opts = []
        for fid, tid in follow_active.items():
            f = self.guild.get_member(fid); t = self.guild.get_member(tid)
            opts.append(discord.SelectOption(label=f"{f.display_name if f else fid} suit {t.display_name if t else tid}", value=str(fid)))
        v = discord.ui.View(); v.add_item(FollowRemoveSelect(opts))
        await i.response.send_message("Choisis :", view=v, ephemeral=True)

    @discord.ui.button(label="📋 Voir tous", style=discord.ButtonStyle.grey)
    async def list_f(self, i, b):
        if not follow_active:
            return await i.response.send_message("Aucun.", ephemeral=True)
        lines = [f"**{self.guild.get_member(f).display_name if self.guild.get_member(f) else f}** suit **{self.guild.get_member(t).display_name if self.guild.get_member(t) else t}**" for f,t in follow_active.items()]
        await i.response.send_message("\n".join(lines), ephemeral=True)

class FollowRemoveSelect(discord.ui.Select):
    def __init__(self, opts): super().__init__(placeholder="Choisis...", options=opts)
    async def callback(self, i): follow_active.pop(int(self.values[0]), None); await i.response.send_message("✅ Follow retiré.", ephemeral=True)

class WLSubPanel(discord.ui.View):
    def __init__(self, guild): super().__init__(timeout=60); self.guild = guild

    @discord.ui.button(label="❌ Retirer une WL", style=discord.ButtonStyle.red)
    async def remove(self, i, b):
        if not whitelisted:
            return await i.response.send_message("Aucune WL.", ephemeral=True)
        opts = []
        for uid, wls in whitelisted.items():
            m = self.guild.get_member(uid)
            for wl in wls:
                opts.append(discord.SelectOption(label=f"{m.display_name if m else uid} - {wl}", value=f"{uid}:{wl}"))
        v = discord.ui.View(); v.add_item(WLRemoveSelect(opts, self.guild))
        await i.response.send_message("Choisis :", view=v, ephemeral=True)

    @discord.ui.button(label="📋 Voir toutes", style=discord.ButtonStyle.grey)
    async def list_wl(self, i, b):
        if not whitelisted:
            return await i.response.send_message("Aucune.", ephemeral=True)
        lines = []
        for uid, wls in whitelisted.items():
            m = self.guild.get_member(uid)
            lines.append(f"**{m.display_name if m else uid}** : {', '.join(wls)}")
        await i.response.send_message("\n".join(lines), ephemeral=True)

class WLRemoveSelect(discord.ui.Select):
    def __init__(self, opts, guild): super().__init__(placeholder="Choisis...", options=opts); self.guild = guild
    async def callback(self, i):
        uid_s, wl = self.values[0].split(":")
        uid = int(uid_s)
        if uid in whitelisted and wl in whitelisted[uid]:
            whitelisted[uid].remove(wl)
            if not whitelisted[uid]: del whitelisted[uid]
            save_wl()
        m = self.guild.get_member(uid)
        await i.response.send_message(f"✅ WL **{wl}** retirée à **{m.display_name if m else uid}**.", ephemeral=True)
        if m:
            try:
                await m.send(embed=discord.Embed(
                    title="❌ Whitelist retirée",
                    description=f"Ta **{wl}** t'a été retirée sur **{i.guild.name}**.",
                    color=0xFF0000))
            except: pass

class VoiceVIPMainPanel(discord.ui.View):
    def __init__(self, guild): super().__init__(timeout=120); self.guild = guild

    @discord.ui.button(label="🔒 Vocs Privées", style=discord.ButtonStyle.blurple)
    async def pv(self, i, b):
        embed = discord.Embed(title="🔒 Vocs Privées", description=f"{len(private_vocs)} active(s).", color=0x5865F2)
        await i.response.send_message(embed=embed, view=PVSubPanel(self.guild), ephemeral=True)

    @discord.ui.button(label="🐕 Laisses", style=discord.ButtonStyle.blurple)
    async def laisse(self, i, b):
        embed = discord.Embed(title="🐕 Laisses", description=f"{len(laisse_active)} active(s).", color=0x5865F2)
        await i.response.send_message(embed=embed, view=LaisseSubPanel(self.guild), ephemeral=True)

    @discord.ui.button(label="🏃 Follows", style=discord.ButtonStyle.blurple)
    async def follow(self, i, b):
        embed = discord.Embed(title="🏃 Follows", description=f"{len(follow_active)} actif(s).", color=0x5865F2)
        await i.response.send_message(embed=embed, view=FollowSubPanel(self.guild), ephemeral=True)

    @discord.ui.button(label="👥 WL", style=discord.ButtonStyle.blurple)
    async def wl(self, i, b):
        total = sum(len(v) for v in whitelisted.values())
        embed = discord.Embed(title="👥 Whitelists", description=f"{total} WL active(s).", color=0x5865F2)
        await i.response.send_message(embed=embed, view=WLSubPanel(self.guild), ephemeral=True)

def build_wlpanel_embed(guild):
    voicevip_p = set()
    server_p   = set()
    sys_p      = set()
    priv_p     = set()

    for uid in SYS_PLUS_IDS:
        voicevip_p.add(uid); server_p.add(uid); sys_p.add(uid)

    for uid, wls in whitelisted.items():
        if "voicevip"  in wls: voicevip_p.add(uid)
        if "server"    in wls: server_p.add(uid)
        if "sys"       in wls: sys_p.add(uid)
        if "privilege" in wls: priv_p.add(uid)

    status = "🔧 **EN MAINTENANCE**" if maintenance else "✅ Opérationnel"
    embed = discord.Embed(title="🎛️ Panel WL - Sys+", color=0xFFA500 if maintenance else 0x5865F2)
    embed.add_field(name="🤖 Statut bot",             value=status,                              inline=False)
    embed.add_field(name="🎤 VoiceVIP",               value=f"**{len(voicevip_p)}** personne(s)", inline=True)
    embed.add_field(name="🌐 Server",                  value=f"**{len(server_p)}** personne(s)",  inline=True)
    embed.add_field(name="⚡ WL Sys",                  value=f"**{len(sys_p)}** personne(s)",     inline=True)
    embed.add_field(name="👑 Privilege",               value=f"**{len(priv_p)}** personne(s)",    inline=True)
    embed.add_field(name="🔒 Vocs privées",            value=str(len(private_vocs)),              inline=True)
    embed.add_field(name="🐕 Laisses actives",         value=str(len(laisse_active)),             inline=True)
    embed.add_field(name="🏃 Follows actifs",          value=str(len(follow_active)),             inline=True)
    embed.set_footer(text="1 personne = 1 comptée par WL même si elle en a plusieurs")
    return embed

@bot.command(name="wlpanel")
@check_sys_plus()
async def wlpanel_cmd(ctx):
    embed = build_wlpanel_embed(ctx.guild)
    await ctx.reply(embed=embed, view=VoiceVIPMainPanel(ctx.guild))

@bot.command(name="restartpanel")
@check_sys_plus()
async def restartpanel_cmd(ctx):
    embed = build_wlpanel_embed(ctx.guild)
    embed.title = "🔄 Panel WL - Redémarré"
    await ctx.reply(embed=embed, view=VoiceVIPMainPanel(ctx.guild))

# ════════════════════════════════════════════════════════════════
#  COMMANDES SYS+ (&)
# ════════════════════════════════════════════════════════════════
@bot.command(name="clear")
@check_sys_plus()
async def clear_cmd(ctx, amount: int = 50):
    if amount < 1 or amount > 500:
        return await ctx.reply(embed=discord.Embed(description="❌ Entre 1 et 500.", color=0xFF0000))
    deleted = await ctx.channel.purge(limit=amount + 1)
    msg = await ctx.reply(embed=discord.Embed(description=f"🗑️ **{len(deleted)-1}** message(s) supprimé(s).", color=0x00FF7F))
    await asyncio.sleep(3); await msg.delete()

@bot.command(name="derank")
@check_sys_plus()
async def derank_cmd(ctx, member: discord.Member = None, *, reason: str = "Aucune raison fournie"):
    if not member:
        if ctx.message.reference:
            ref = await ctx.channel.fetch_message(ctx.message.reference.message_id)
            member = ref.author
        else:
            return await ctx.reply(embed=discord.Embed(description="❌ `&derank @membre`", color=0xFF0000))
    if member == ctx.author:
        return await ctx.reply(embed=discord.Embed(description="❌ Tu ne peux pas te derank toi-même.", color=0xFF0000))
    if not await protection_check(ctx, member): return
    if member.top_role >= ctx.guild.me.top_role:
        return await ctx.reply(embed=discord.Embed(description="❌ Rôle trop haut.", color=0xFF0000))
    roles = [r for r in member.roles if r != ctx.guild.default_role and r < ctx.guild.me.top_role]
    if not roles:
        return await ctx.reply(embed=discord.Embed(description=f"⚠️ {member.mention} n'a aucun rôle.", color=0xFFA500))
    await member.remove_roles(*roles, reason=f"Derank par {ctx.author} - {reason}")
    embed = discord.Embed(title="🔨 Derank effectué", color=0xFF4500)
    embed.add_field(name="Membre", value=f"{member.mention}", inline=True)
    embed.add_field(name="Par", value=ctx.author.mention, inline=True)
    embed.add_field(name="Raison", value=reason, inline=False)
    await ctx.reply(embed=embed)
    try:
        await member.send(embed=discord.Embed(title="⚠️ Derank",
            description=f"Tous tes rôles ont été retirés sur **{ctx.guild.name}**.\nRaison : {reason}", color=0xFF4500))
    except: pass

# ════════════════════════════════════════════════════════════════
#  /addrole - Ajouter un rôle (Sys+)
# ════════════════════════════════════════════════════════════════
@tree.command(name="addrole", description="Ajouter un rôle à un membre ou à tout le serveur (Sys+)")
@app_commands.describe(
    role="Le rôle à ajouter",
    tous="Ajouter à tous les membres du serveur ?",
    membre="Le membre cible (ignoré si 'tous' est activé)"
)
async def addrole_slash(
    i: discord.Interaction,
    role: discord.Role,
    tous: bool,
    membre: discord.Member = None
):
    if not is_sys_plus(i.user.id):
        return await i.response.send_message(
            embed=discord.Embed(description="❌ Réservé aux **Sys+**.", color=0xFF0000),
            ephemeral=True
        )
    if maintenance and not is_sys_plus(i.user.id):
        return await i.response.send_message("🔧 Le bot est en **maintenance**.", ephemeral=True)

    # Vérif hiérarchie du rôle
    if role >= i.guild.me.top_role:
        return await i.response.send_message(
            embed=discord.Embed(description="❌ Ce rôle est trop haut pour moi.", color=0xFF0000),
            ephemeral=True
        )

    if tous:
        await i.response.defer(thinking=True)
        members = [m for m in i.guild.members if not m.bot and role not in m.roles]
        ok, fail = 0, 0
        for m in members:
            try:
                await m.add_roles(role, reason=f"/addrole tous - par {i.user}")
                ok += 1
            except:
                fail += 1
        embed = discord.Embed(
            title="✅ Rôle ajouté - Tous les membres",
            color=0x00FF7F
        )
        embed.add_field(name="Rôle", value=role.mention, inline=True)
        embed.add_field(name="Réussi", value=str(ok), inline=True)
        embed.add_field(name="Échoué", value=str(fail), inline=True)
        embed.set_footer(text=f"Par {i.user.display_name}")
        await i.followup.send(embed=embed)

    else:
        if not membre:
            return await i.response.send_message(
                embed=discord.Embed(description="❌ Précise un membre ou active **tous**.", color=0xFF0000),
                ephemeral=True
            )
        if not await protection_check_i(i, membre):
            return
        if role in membre.roles:
            return await i.response.send_message(
                embed=discord.Embed(description=f"⚠️ {membre.mention} a déjà ce rôle.", color=0xFFA500),
                ephemeral=True
            )
        try:
            await membre.add_roles(role, reason=f"/addrole - par {i.user}")
            embed = discord.Embed(
                title="✅ Rôle ajouté",
                color=0x00FF7F
            )
            embed.add_field(name="Membre", value=membre.mention, inline=True)
            embed.add_field(name="Rôle", value=role.mention, inline=True)
            embed.set_footer(text=f"Par {i.user.display_name}")
            await i.response.send_message(embed=embed)
        except discord.Forbidden:
            await i.response.send_message(
                embed=discord.Embed(description="❌ Impossible d'ajouter ce rôle.", color=0xFF0000),
                ephemeral=True
            )

# ════════════════════════════════════════════════════════════════
#  /removerole - Retirer un rôle (Sys+)
# ════════════════════════════════════════════════════════════════
@tree.command(name="removerole", description="Retirer un rôle à un membre ou à tout le serveur (Sys+)")
@app_commands.describe(
    role="Le rôle à retirer",
    tous="Retirer à tous les membres du serveur ?",
    membre="Le membre cible (ignoré si 'tous' est activé)"
)
async def removerole_slash(
    i: discord.Interaction,
    role: discord.Role,
    tous: bool,
    membre: discord.Member = None
):
    if not is_sys_plus(i.user.id):
        return await i.response.send_message(
            embed=discord.Embed(description="❌ Réservé aux **Sys+**.", color=0xFF0000),
            ephemeral=True
        )
    if maintenance and not is_sys_plus(i.user.id):
        return await i.response.send_message("🔧 Le bot est en **maintenance**.", ephemeral=True)

    if role >= i.guild.me.top_role:
        return await i.response.send_message(
            embed=discord.Embed(description="❌ Ce rôle est trop haut pour moi.", color=0xFF0000),
            ephemeral=True
        )

    if tous:
        await i.response.defer(thinking=True)
        members = [m for m in i.guild.members if not m.bot and role in m.roles]
        ok, fail = 0, 0
        for m in members:
            try:
                await m.remove_roles(role, reason=f"/removerole tous - par {i.user}")
                ok += 1
            except:
                fail += 1
        embed = discord.Embed(
            title="✅ Rôle retiré - Tous les membres",
            color=0xFF4500
        )
        embed.add_field(name="Rôle", value=role.mention, inline=True)
        embed.add_field(name="Réussi", value=str(ok), inline=True)
        embed.add_field(name="Échoué", value=str(fail), inline=True)
        embed.set_footer(text=f"Par {i.user.display_name}")
        await i.followup.send(embed=embed)

    else:
        if not membre:
            return await i.response.send_message(
                embed=discord.Embed(description="❌ Précise un membre ou active **tous**.", color=0xFF0000),
                ephemeral=True
            )
        if not await protection_check_i(i, membre):
            return
        if role not in membre.roles:
            return await i.response.send_message(
                embed=discord.Embed(description=f"⚠️ {membre.mention} n'a pas ce rôle.", color=0xFFA500),
                ephemeral=True
            )
        try:
            await membre.remove_roles(role, reason=f"/removerole - par {i.user}")
            embed = discord.Embed(
                title="✅ Rôle retiré",
                color=0xFF4500
            )
            embed.add_field(name="Membre", value=membre.mention, inline=True)
            embed.add_field(name="Rôle", value=role.mention, inline=True)
            embed.set_footer(text=f"Par {i.user.display_name}")
            await i.response.send_message(embed=embed)
        except discord.Forbidden:
            await i.response.send_message(
                embed=discord.Embed(description="❌ Impossible de retirer ce rôle.", color=0xFF0000),
                ephemeral=True
            )

# ════════════════════════════════════════════════════════════════
#  COMMANDES VOICEVIP (=)
# ════════════════════════════════════════════════════════════════
@bot.command(name="laisse")
@check_voicevip()
async def laisse_cmd(ctx, member: discord.Member = None):
    if not member:
        return await ctx.reply(embed=discord.Embed(description="❌ `=laisse @membre`", color=0xFF0000))
    if not await protection_check(ctx, member): return
    oid = ctx.author.id
    if oid in laisse_active and laisse_active[oid][0] == member.id:
        _, nn, on = laisse_active.pop(oid)
        try: await member.edit(nick=on)
        except: pass
        return await ctx.reply(embed=discord.Embed(description=f"🔓 Laisse retirée à {member.mention}.", color=0xFFA500))
    if oid in laisse_active:
        return await ctx.reply(embed=discord.Embed(description="❌ Tu as déjà une laisse active.", color=0xFF0000))
    for o, (cid, _, _) in laisse_active.items():
        if cid == member.id:
            return await ctx.reply("cette personne as déjà la laisse de quelqu'un d'autre sale flocko.")
    old = member.display_name
    new = f"{old}(🐕de {ctx.author.display_name})"
    try: await member.edit(nick=new)
    except discord.Forbidden:
        return await ctx.reply(embed=discord.Embed(description="❌ Impossible de changer le pseudo.", color=0xFF0000))
    laisse_active[oid] = (member.id, new, old)
    await ctx.reply(embed=discord.Embed(description=f"🐕 {member.mention} est maintenant sous ta laisse.", color=0x00FF7F))

@bot.command(name="pv")
@check_voicevip()
async def pv_cmd(ctx):
    if not ctx.author.voice:
        return await ctx.reply(embed=discord.Embed(description="❌ Tu n'es pas dans une vocal.", color=0xFF0000))
    cid = ctx.author.voice.channel.id
    if cid in private_vocs and private_vocs[cid]["owner"] == ctx.author.id:
        private_vocs.pop(cid); pv_access.pop(cid, None)
        return await ctx.reply(embed=discord.Embed(description="🔓 Vocal rendue **publique**.", color=0x00FF7F))
    user_pvs = [c for c, info in private_vocs.items() if info["owner"] == ctx.author.id]
    max_pvs = 99 if is_sys_plus(ctx.author.id) else 2
    if len(user_pvs) >= max_pvs:
        return await ctx.reply(embed=discord.Embed(
            description=f"❌ Tu as déjà **{max_pvs}** vocal(s) privée(s) max.", color=0xFF0000))
    if is_sys_plus(ctx.author.id):
        pv_type = "sysplus"
    elif has_wl_sys(ctx.author.id):
        pv_type = "sys"
    else:
        pv_type = "normal"
    private_vocs[cid] = {"owner": ctx.author.id, "type": pv_type}
    pv_access[cid] = set()
    labels = {"normal": "🔒 normale", "sys": "🔒 Sys", "sysplus": "🔒 Sys+"}
    await ctx.reply(embed=discord.Embed(
        description=f"{labels[pv_type]} **{ctx.author.voice.channel.name}** est maintenant privée.", color=0x5865F2))

@bot.command(name="acces")
@check_voicevip()
async def acces_cmd(ctx, member: discord.Member = None):
    if not member:
        return await ctx.reply(embed=discord.Embed(description="❌ `=acces @membre`", color=0xFF0000))
    if not ctx.author.voice:
        return await ctx.reply(embed=discord.Embed(description="❌ Tu n'es pas dans une vocal.", color=0xFF0000))
    cid = ctx.author.voice.channel.id
    if cid not in private_vocs or private_vocs[cid]["owner"] != ctx.author.id:
        return await ctx.reply(embed=discord.Embed(description="❌ Ce n'est pas ta vocal privée.", color=0xFF0000))
    acc = pv_access.setdefault(cid, set())
    if member.id in acc:
        acc.discard(member.id)
        return await ctx.reply(embed=discord.Embed(description=f"🔓 Accès retiré à **{member.display_name}**.", color=0xFFA500))
    acc.add(member.id)
    await ctx.reply(embed=discord.Embed(description=f"✅ **{member.display_name}** peut rejoindre ta vocal privée.", color=0x00FF7F))

@bot.command(name="join")
@check_voicevip()
async def join_cmd(ctx, member: discord.Member = None):
    if not member:
        return await ctx.reply(embed=discord.Embed(description="❌ `=join @membre`", color=0xFF0000))
    if not await protection_check(ctx, member): return
    if not member.voice:
        return await ctx.reply(embed=discord.Embed(description="❌ Cette personne n'est pas en vocal.", color=0xFF0000))
    try:
        if ctx.author.voice:
            await ctx.author.move_to(member.voice.channel)
        else:
            return await ctx.reply(embed=discord.Embed(description="❌ Tu n'es pas en vocal.", color=0xFF0000))
        await ctx.reply(embed=discord.Embed(description=f"➡️ Rejoint **{member.voice.channel.name}**.", color=0x00FF7F))
    except discord.Forbidden:
        await ctx.reply(embed=discord.Embed(description="❌ Impossible de te déplacer.", color=0xFF0000))

@bot.command(name="mv")
@check_voicevip()
async def mv_cmd(ctx, member: discord.Member = None, channel: discord.VoiceChannel = None):
    if not member or not channel:
        return await ctx.reply(embed=discord.Embed(description="❌ `=mv @membre #vocal`", color=0xFF0000))
    if not await protection_check(ctx, member): return
    try:
        await member.move_to(channel)
        await ctx.reply(embed=discord.Embed(description=f"✅ **{member.display_name}** déplacé dans **{channel.name}**.", color=0x00FF7F))
    except discord.Forbidden:
        await ctx.reply(embed=discord.Embed(description="❌ Impossible.", color=0xFF0000))

@bot.command(name="pvlist")
@check_voicevip()
async def pvlist_cmd(ctx):
    if not private_vocs:
        return await ctx.reply(embed=discord.Embed(description="Aucune vocal privée active.", color=0xFFA500))
    embed = discord.Embed(title="🔒 Vocaux privés actifs", color=0x5865F2)
    for cid, info in private_vocs.items():
        ch = ctx.guild.get_channel(cid)
        ow = ctx.guild.get_member(info["owner"])
        acc = [ctx.guild.get_member(u) for u in pv_access.get(cid, set())]
        acc_str = ", ".join(m.display_name for m in acc if m) or "Personne"
        embed.add_field(
            name=f"#{ch.name if ch else cid} [{info['type']}]",
            value=f"Owner : {ow.mention if ow else info['owner']}\nAccès : {acc_str}", inline=False)
    await ctx.reply(embed=embed)

@bot.command(name="menotte")
@check_voicevip()
async def menotte_cmd(ctx, member: discord.Member = None):
    if not member:
        return await ctx.reply(embed=discord.Embed(description="❌ `=menotte @membre`", color=0xFF0000))
    if not await protection_check(ctx, member): return
    oid = ctx.author.id
    now = time.time()
    if oid in menotte_active and menotte_active[oid][0] == member.id:
        menotte_active.pop(oid)
        return await ctx.reply(embed=discord.Embed(description=f"🔓 Menotte retirée à {member.mention}.", color=0xFFA500))
    if oid in menotte_active:
        return await ctx.reply(embed=discord.Embed(description="❌ Tu as déjà une menotte active.", color=0xFF0000))
    if not is_sys_plus(oid):
        last = menotte_cd.get(oid, 0)
        if now - last < 120:
            return await ctx.reply(embed=discord.Embed(
                description=f"⏳ Cooldown menotte : encore **{int(120-(now-last))}s**.", color=0xFFA500))
    if not member.voice:
        return await ctx.reply(embed=discord.Embed(description="❌ Ce membre n'est pas en vocal.", color=0xFF0000))
    ch_id = member.voice.channel.id
    menotte_active[oid] = (member.id, ch_id)
    menotte_cd[oid] = now
    await ctx.reply(embed=discord.Embed(
        description=f"⛓️ {member.mention} est menotté dans **{member.voice.channel.name}**.", color=0x5865F2))

# ════════════════════════════════════════════════════════════════
#  COMMANDES WL SYS (=)
# ════════════════════════════════════════════════════════════════
@bot.command(name="follow")
@check_wl_sys()
async def follow_cmd(ctx, member: discord.Member = None):
    if not member:
        return await ctx.reply(embed=discord.Embed(description="❌ `=follow @membre`", color=0xFF0000))
    if not await protection_check(ctx, member): return
    if ctx.author.id in follow_active and follow_active[ctx.author.id] == member.id:
        follow_active.pop(ctx.author.id)
        return await ctx.reply(embed=discord.Embed(description=f"🚫 Follow sur **{member.display_name}** retiré.", color=0xFFA500))
    follow_active[ctx.author.id] = member.id
    await ctx.reply(embed=discord.Embed(description=f"🏃 Tu suis maintenant **{member.display_name}**.", color=0x00FF7F))

@bot.command(name="pvsys")
@check_wl_sys()
async def pvsys_cmd(ctx):
    if not ctx.author.voice:
        return await ctx.reply(embed=discord.Embed(description="❌ Tu n'es pas dans une vocal.", color=0xFF0000))
    cid = ctx.author.voice.channel.id
    if cid in private_vocs and private_vocs[cid]["owner"] == ctx.author.id:
        private_vocs.pop(cid); pv_access.pop(cid, None)
        return await ctx.reply(embed=discord.Embed(description="🔓 PV Sys désactivée.", color=0x00FF7F))
    user_pvs = [c for c, info in private_vocs.items() if info["owner"] == ctx.author.id]
    if len(user_pvs) >= 2 and not is_sys_plus(ctx.author.id):
        return await ctx.reply(embed=discord.Embed(description="❌ Maximum 2 vocs privées.", color=0xFF0000))
    private_vocs[cid] = {"owner": ctx.author.id, "type": "sys"}
    pv_access[cid] = set()
    await ctx.reply(embed=discord.Embed(
        description=f"🔒 **{ctx.author.voice.channel.name}** est maintenant en **PV Sys**.", color=0x5865F2))

# ════════════════════════════════════════════════════════════════
#  COMMANDES SERVER (= et /slash)
# ════════════════════════════════════════════════════════════════
@bot.command(name="mp")
async def mp_cmd(ctx, member: discord.Member = None, *, message: str = None):
    if maintenance and not is_sys_plus(ctx.author.id):
        return await ctx.reply(embed=discord.Embed(description="🔧 Le bot est en **maintenance**.", color=0xFFA500))
    if not has_server(ctx.author.id):
        return await ctx.reply(embed=discord.Embed(description="❌ Tu n'as pas la **Server WL**.", color=0xFF0000))
    if not member or not message:
        return await ctx.reply(embed=discord.Embed(description="❌ `=mp @membre message`", color=0xFF0000))
    if not await protection_check(ctx, member): return
    try:
        await member.send(message)
        await ctx.reply(embed=discord.Embed(description=f"✅ Message envoyé anonymement à {member.mention}.", color=0x00FF7F))
    except discord.Forbidden:
        await ctx.reply(embed=discord.Embed(description="❌ Impossible d'envoyer le MP (DMs fermés).", color=0xFF0000))

@tree.command(name="dog-add", description="Dog quelqu'un - le suit partout en voc (Server WL)")
@app_commands.describe(membre="La personne à dog")
async def dog_add(i: discord.Interaction, membre: discord.Member):
    if maintenance and not is_sys_plus(i.user.id):
        return await i.response.send_message("🔧 Le bot est en **maintenance**.", ephemeral=True)
    if not has_server(i.user.id):
        return await i.response.send_message("❌ Tu n'as pas la **Server WL**.", ephemeral=True)
    if not await protection_check_i(i, membre): return
    oid = i.user.id
    now = time.time()
    if oid in dog_active and dog_active[oid][0] == membre.id:
        return await i.response.send_message("⚠️ Cette personne est déjà ton dog.", ephemeral=True)
    if oid in dog_active:
        return await i.response.send_message("❌ Tu as déjà un dog actif. Fais `/dog-del` d'abord.", ephemeral=True)
    if not is_sys_plus(oid):
        last = dog_cd.get(oid, 0)
        if now - last < 60:
            return await i.response.send_message(f"⏳ Cooldown dog : encore **{int(60-(now-last))}s**.", ephemeral=True)
    old = membre.display_name
    new = f"{old}(🐕de {i.user.display_name})"
    try:
        await membre.edit(nick=new)
    except discord.Forbidden:
        return await i.response.send_message("❌ Impossible de changer le pseudo.", ephemeral=True)
    dog_active[oid] = (membre.id, new, old)
    dog_cd[oid] = now
    await i.response.send_message(embed=discord.Embed(
        description=f"🐕 **{membre.display_name}** est maintenant ton dog.", color=0x00FF7F))

@tree.command(name="dog-del", description="Retirer le dog (Server WL)")
async def dog_del(i: discord.Interaction):
    if maintenance and not is_sys_plus(i.user.id):
        return await i.response.send_message("🔧 Le bot est en **maintenance**.", ephemeral=True)
    if not has_server(i.user.id):
        return await i.response.send_message("❌ Tu n'as pas la **Server WL**.", ephemeral=True)
    oid = i.user.id
    if oid not in dog_active:
        return await i.response.send_message("❌ Tu n'as pas de dog actif.", ephemeral=True)
    cid, new, old = dog_active.pop(oid)
    m = i.guild.get_member(cid)
    if m:
        try: await m.edit(nick=old)
        except: pass
    await i.response.send_message(embed=discord.Embed(description="🔓 Dog retiré.", color=0xFFA500))

class WakeupModal(discord.ui.Modal, title="Wakeup"):
    message = discord.ui.TextInput(
        label="Message (optionnel)",
        placeholder="Laisse vide pour le message par défaut",
        required=False,
        max_length=200)
    def __init__(self, target: discord.Member, invoker: discord.Member):
        super().__init__(); self.target = target; self.invoker = invoker

    async def on_submit(self, i: discord.Interaction):
        if not await protection_check_i(i, self.target): return
        now = time.time()
        if not is_sys_plus(self.invoker.id):
            last = wakeup_cd.get(self.invoker.id, 0)
            if now - last < 300:
                return await i.response.send_message(f"⏳ Cooldown : encore **{int(300-(now-last))}s**.", ephemeral=True)
        if self.target.id in wakeup_active:
            return await i.response.send_message("❌ Déjà en wakeup.", ephemeral=True)
        custom = self.message.value.strip()
        spam_msg = f"{self.target.mention} {custom}" if custom else f"Réveille toi {self.target.mention} ! C'est {self.invoker.mention} qui te l'ordonne"
        wakeup_active.add(self.target.id)
        wakeup_cd[self.invoker.id] = now
        await i.response.send_message(f"✅ Wakeup lancé sur {self.target.mention} !", ephemeral=True)
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

@tree.command(name="wakeup", description="Wakeup un membre (Server WL)")
@app_commands.describe(membre="Le membre à wakeup")
async def wakeup_slash(i: discord.Interaction, membre: discord.Member):
    if maintenance and not is_sys_plus(i.user.id):
        return await i.response.send_message("🔧 Le bot est en **maintenance**.", ephemeral=True)
    if not has_server(i.user.id):
        return await i.response.send_message("❌ Tu n'as pas la **Server WL**.", ephemeral=True)
    await i.response.send_modal(WakeupModal(membre, i.user))

class SnapResponseModal(discord.ui.Modal, title="Donner mon Snap"):
    snap = discord.ui.TextInput(label="Ton Snapchat", placeholder="ton_snap", max_length=50)
    def __init__(self, demandeur: discord.Member):
        super().__init__(); self.demandeur = demandeur
    async def on_submit(self, i: discord.Interaction):
        embed = discord.Embed(title="📸 Snap reçu !", color=0xFFFC00)
        embed.add_field(name="De", value=i.user.mention)
        embed.add_field(name="Snapchat", value=f"`{self.snap.value}`")
        try:
            await self.demandeur.send(embed=embed)
            await i.response.send_message("✅ Ton snap a été envoyé !", ephemeral=True)
        except:
            await i.response.send_message("❌ Impossible d'envoyer le snap (DMs fermés).", ephemeral=True)

class SnapView(discord.ui.View):
    def __init__(self, demandeur: discord.Member):
        super().__init__(timeout=300); self.demandeur = demandeur
    @discord.ui.button(label="📸 Donner mon Snap", style=discord.ButtonStyle.blurple)
    async def give_snap(self, i, b):
        await i.response.send_modal(SnapResponseModal(self.demandeur))

@tree.command(name="snap", description="Demander le snap de quelqu'un (Server WL)")
@app_commands.describe(membre="La personne à qui demander", message="Ton petit message")
async def snap_slash(i: discord.Interaction, membre: discord.Member, message: str = ""):
    if maintenance and not is_sys_plus(i.user.id):
        return await i.response.send_message("🔧 Le bot est en **maintenance**.", ephemeral=True)
    if not has_server(i.user.id):
        return await i.response.send_message("❌ Tu n'as pas la **Server WL**.", ephemeral=True)
    embed = discord.Embed(title="📸 Quelqu'un veut ton Snap !", color=0xFFFC00)
    embed.add_field(name="De la part de", value=i.user.mention, inline=False)
    if message:
        embed.add_field(name="Message", value=message, inline=False)
    embed.set_footer(text="Clique sur le bouton si tu veux donner ton snap.")
    try:
        await membre.send(embed=embed, view=SnapView(i.user))
        await i.response.send_message(f"✅ Demande de snap envoyée à {membre.mention} !", ephemeral=True)
    except:
        await i.response.send_message("❌ Impossible d'envoyer le MP (DMs fermés).", ephemeral=True)

@tree.command(name="tipeu", description="Rename en S et lock le pseudo (Server WL)")
@app_commands.describe(membre="La cible")
async def tipeu_slash(i: discord.Interaction, membre: discord.Member):
    if maintenance and not is_sys_plus(i.user.id):
        return await i.response.send_message("🔧 Le bot est en **maintenance**.", ephemeral=True)
    if not has_server(i.user.id):
        return await i.response.send_message("❌ Tu n'as pas la **Server WL**.", ephemeral=True)
    if not await protection_check_i(i, membre): return
    if membre.id in locked_nicks:
        locked_nicks.discard(membre.id)
        try: await membre.edit(nick=None)
        except: pass
        return await i.response.send_message(embed=discord.Embed(
            description=f"🔓 Pseudo de {membre.mention} déverrouillé.", color=0xFFA500))
    try:
        await membre.edit(nick="S")
        locked_nicks.add(membre.id)
        await i.response.send_message(embed=discord.Embed(
            description=f"🔒 {membre.mention} renommé **S** et pseudo verrouillé.", color=0x5865F2))
    except discord.Forbidden:
        await i.response.send_message("❌ Impossible de changer le pseudo.", ephemeral=True)

# ════════════════════════════════════════════════════════════════
#  &help / =help
# ════════════════════════════════════════════════════════════════
@bot.command(name="help")
async def help_cmd(ctx):
    embed = discord.Embed(title="📖 Commandes", color=0x5865F2)
    if maintenance:
        embed.description = "🔧 **Le bot est en maintenance.** Seuls les Sys+ peuvent utiliser les commandes."
    if is_sys_plus(ctx.author.id):
        embed.add_field(name="⭐ Sys+ (&)", value="`&wl` `&wlpanel` `&restartpanel` `&maintenance` `&clear` `&derank` `/addrole`\n*+ toutes les commandes `=` et `/`*", inline=False)
    if has_voicevip(ctx.author.id):
        embed.add_field(name="🎤 VoiceVIP (=)", value="`=laisse` `=pv` `=acces` `=join` `=mv` `=pvlist` `=menotte`", inline=False)
    if has_wl_sys(ctx.author.id):
        embed.add_field(name="⚡ WL Sys (=)", value="`=follow` `=pvsys` + toutes les commandes VoiceVIP", inline=False)
    if has_server(ctx.author.id):
        embed.add_field(name="🌐 Server (= et /)", value="`=mp id message` `/dog-add` `/dog-del` `/wakeup` `/snap` `/tipeu`", inline=False)
    if not embed.fields:
        embed.description = "Tu n'as accès à aucune commande."
    embed.set_footer(text="Refais la même commande pour toggle • Sys+ = invulnérables")
    await ctx.reply(embed=embed)

# ════════════════════════════════════════════════════════════════
#  LANCEMENT
# ════════════════════════════════════════════════════════════════
bot.run(os.environ["TOKEN"])
