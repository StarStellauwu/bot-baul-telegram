from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

import os
TOKEN = os.environ.get("BOT_TOKEN")

duelo_activo = False
players = []
personajes = {}
grupo_id = None

# /duelo
async def duelo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global duelo_activo, players, personajes, grupo_id

    if duelo_activo:
        await update.message.reply_text("⚠️ Ya hay un duelo en curso. Finalícenlo con /revelar.")
        return

    duelo_activo = True
    players = []
    personajes = {}
    grupo_id = update.message.chat_id

    await update.message.reply_text(
        "🎮 Duelo iniciado.\n"
        "Dos jugadores deben unirse con /join",
        parse_mode=None
    )

# /join
async def join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global players

    if not duelo_activo:
        await update.message.reply_text("⚠️ No hay ningún duelo activo.")
        return

    user = update.message.from_user

    if user.id in players:
        await update.message.reply_text("⚠️ Ya estás en el duelo.")
        return

    if len(players) >= 2:
        await update.message.reply_text("⚠️ El duelo ya tiene dos jugadores.")
        return

    players.append(user.id)

    username = f"@{user.username}" if user.username else user.full_name

    await update.message.reply_text(
        f"✅ {username} se unió al duelo ({len(players)}/2)",
        parse_mode=None
    )

    if len(players) == 2:
        await context.bot.send_message(
            chat_id=grupo_id,
            text=(
                "📩 Ambos jugadores están listos.\n"
                "Ahora envíen por privado al bot el nombre del personaje que eligieron."
            ),
            parse_mode=None
        )

# Mensajes privados
async def privado(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global personajes

    if not duelo_activo:
        return

    user = update.message.from_user

    if user.id not in players:
        return

    # 🚫 Anti-trampa: no permitir cambiar personaje
    if user.id in personajes:
        await update.message.reply_text(
            "⚠️ Ya enviaste tu personaje para este duelo. No se puede cambiar.",
            parse_mode=None
        )
        return

    personajes[user.id] = update.message.text.strip()

    await update.message.reply_text(
        "🔒 Personaje guardado correctamente.",
        parse_mode=None
    )

    if len(personajes) == 2:
        await context.bot.send_message(
            chat_id=grupo_id,
            text="✅ Ambos personajes han sido guardados. El duelo puede comenzar 🧠",
            parse_mode=None
        )


# /revelar
async def revelar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global duelo_activo, players, personajes

    if not duelo_activo:
        await update.message.reply_text("⚠️ No hay ningún duelo activo.")
        return

    if len(personajes) < 2:
        await update.message.reply_text("⚠️ Aún faltan personajes por enviar.")
        return

    mensaje = "🧠 Duelo finalizado\n"

    for user_id in players:
        user = await context.bot.get_chat(user_id)
        username = f"@{user.username}" if user.username else user.full_name
        personaje = personajes.get(user_id, "???")
        mensaje += f"{username} → {personaje}\n"

    await update.message.reply_text(mensaje, parse_mode=None)

    duelo_activo = False
    players = []
    personajes = {}

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("duelo", duelo))
    app.add_handler(CommandHandler("join", join))
    app.add_handler(CommandHandler("revelar", revelar))
    app.add_handler(MessageHandler(filters.ChatType.PRIVATE & filters.TEXT, privado))

    print("🤖 Bot en marcha...")
    app.run_polling()

if __name__ == "__main__":
    main()

