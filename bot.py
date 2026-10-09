import discord
from discord.ext import commands
import asyncio

# ── Configuration ──────────────────────────────────────────────
PREFIX = "&"

SYS_PLUS = {
    1419320803199029402,
    1514099294611701842,
}
# ───────────────────────────────────────────────────────────────

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)


# ── Vérification Sys+ ──────────────────────────────────────────
def is_sys_plus():
    async def predicate(ctx):
        if ctx.author.id not in SYS_PLUS:
            await ctx.send(
                embed=discord.Embed(
                    description="❌ Tu n'es pas **Sys+**. Accès refusé.",
                    color=0xFF0000,
                )
            )
            return False
        return True
    return commands.check(predicate)


# ── Événement prêt ─────────────────────────────────────────────
@bot.event
async def on_ready():
    print(f"✅ Bot connecté en tant que {bot.user} (ID: {bot.user.id})")
    await bot.change_presence(activity=discord.Activity(
        type=discord.ActivityType.watching, name="Sys+ | &help"
    ))


# ── &clear ─────────────────────────────────────────────────────
@bot.command(name="clear")
@is_sys_plus()
async def clear(ctx, amount: int = 50):
    if amount < 1 or amount > 500:
        return await ctx.send(
            embed=discord.Embed(
                description="❌ Le nombre doit être entre **1** et **500**.",
                color=0xFF0000,
            )
        )

    # +1 pour supprimer aussi le message de commande
    deleted = await ctx.channel.purge(limit=amount + 1)
    count = len(deleted) - 1  # on ne compte pas la commande elle-même

    confirm = await ctx.send(
        embed=discord.Embed(
            description=f"🗑️ **{count}** message(s) supprimé(s).",
            color=0x00FF7F,
        )
    )
    await asyncio.sleep(3)
    await confirm.delete()


@clear.error
async def clear_error(ctx, error):
    if isinstance(error, commands.BadArgument):
        await ctx.send(
            embed=discord.Embed(
                description="❌ Utilisation : `&clear [nombre]`",
                color=0xFF0000,
            )
        )


# ── &derank ────────────────────────────────────────────────────
@bot.command(name="derank")
@is_sys_plus()
async def derank(ctx, member: discord.Member = None, *, reason: str = "Aucune raison fournie"):
    # Si pas de membre en argument → on cherche dans le message référencé
    if member is None:
        if ctx.message.reference:
            ref_msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
            member = ref_msg.author
        else:
            return await ctx.send(
                embed=discord.Embed(
                    description="❌ Mentionne un membre ou réponds à son message.\n`&derank @user [raison]`",
                    color=0xFF0000,
                )
            )

    if member == ctx.author:
        return await ctx.send(
            embed=discord.Embed(
                description="❌ Tu ne peux pas te derank toi-même.",
                color=0xFF0000,
            )
        )

    if member.top_role >= ctx.guild.me.top_role:
        return await ctx.send(
            embed=discord.Embed(
                description="❌ Je ne peux pas retirer les rôles de ce membre (rôle trop haut).",
                color=0xFF0000,
            )
        )

    # Retirer tous les rôles (sauf @everyone)
    roles_to_remove = [r for r in member.roles if r != ctx.guild.default_role and r < ctx.guild.me.top_role]

    if not roles_to_remove:
        return await ctx.send(
            embed=discord.Embed(
                description=f"⚠️ {member.mention} n'a aucun rôle à retirer.",
                color=0xFFA500,
            )
        )

    await member.remove_roles(*roles_to_remove, reason=f"Derank par {ctx.author} — {reason}")

    embed = discord.Embed(
        title="🔨 Derank effectué",
        color=0xFF4500,
    )
    embed.add_field(name="Membre", value=f"{member.mention} (`{member.id}`)", inline=False)
    embed.add_field(name="Rôles retirés", value=f"`{len(roles_to_remove)}`", inline=True)
    embed.add_field(name="Par", value=ctx.author.mention, inline=True)
    embed.add_field(name="Raison", value=reason, inline=False)
    embed.set_footer(text=f"Sys+ — {ctx.guild.name}")

    await ctx.send(embed=embed)

    # Essayer de notifier le membre en DM
    try:
        dm_embed = discord.Embed(
            title="⚠️ Vous avez été derank",
            description=f"Tous vos rôles ont été retirés sur **{ctx.guild.name}**.",
            color=0xFF4500,
        )
        dm_embed.add_field(name="Raison", value=reason)
        await member.send(embed=dm_embed)
    except discord.Forbidden:
        pass  # DMs fermés, on ignore


@derank.error
async def derank_error(ctx, error):
    if isinstance(error, commands.MemberNotFound):
        await ctx.send(
            embed=discord.Embed(
                description="❌ Membre introuvable. Vérifie l'ID ou la mention.",
                color=0xFF0000,
            )
        )


# ── &help ──────────────────────────────────────────────────────
@bot.command(name="help")
@is_sys_plus()
async def help_cmd(ctx):
    embed = discord.Embed(
        title="📖 Commandes — Sys+",
        color=0x5865F2,
    )
    embed.add_field(
        name="`&clear [nombre]`",
        value="Supprime les X derniers messages (défaut : 50, max : 500).",
        inline=False,
    )
    embed.add_field(
        name="`&derank @membre [raison]`",
        value="Retire tous les rôles d'un membre. Fonctionne aussi en répondant à son message.",
        inline=False,
    )
    embed.set_footer(text="Réservé aux Sys+")
    await ctx.send(embed=embed)


# ── Lancement ──────────────────────────────────────────────────
# Remplace TON_TOKEN par le token de ton bot
bot.run("MTU1ODI2MzE1MTYzNDU0Njc1MA.GS8imS.gFmfPQUFcZwKBySPuMP9Zqc4e28vsTUKBJ0HTk")
