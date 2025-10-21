# main.py — BOT ADMINISTRADOR 🔎⚙️
import os, asyncio, httpx, time
from fastapi import FastAPI, Request
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
from telegram import Bot

# ───────────────────────────────
# CONFIGURACIÓN GENERAL
# ───────────────────────────────
app = FastAPI(title="Bot Administrador", version="1.0")

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")

# URLs de los servicios supervisados
SERVICES = {
    "bot_investigador": "https://bot-investigador.onrender.com",
    "bot_ventas": "https://vendedorbt.onrender.com",
}

CHECK_INTERVAL_MIN = 30  # cada 30 minutos verifica el estado

bot = Bot(token=TELEGRAM_TOKEN)
scheduler = AsyncIOScheduler(timezone="America/Costa_Rica")

# ───────────────────────────────
# FUNCIÓN DE SUPERVISIÓN
# ───────────────────────────────
async def check_services():
    """Revisa el estado de los bots y notifica si hay caídas."""
    print(f"[ADMIN] ⏰ Verificando bots ({datetime.now().strftime('%H:%M:%S')})...")
    async with httpx.AsyncClient(timeout=15) as client:
        for name, url in SERVICES.items():
            try:
                resp = await client.get(url)
                if resp.status_code == 200:
                    print(f"[ADMIN] ✅ {name} activo ({url})")
                else:
                    print(f"[ADMIN] ⚠️ {name} respondió con {resp.status_code}")
                    await alert_admin(f"⚠️ *{name}* respondió con error {resp.status_code}. URL: {url}")
            except Exception as e:
                print(f"[ADMIN] ❌ {name} no responde → {e}")
                await alert_admin(f"❌ *{name}* no responde.\nError: `{e}`\nURL: {url}")

# ───────────────────────────────
# ENVIAR ALERTA AL ADMIN
# ───────────────────────────────
async def alert_admin(msg: str):
    """Envía mensajes de alerta por Telegram."""
    try:
        await bot.send_message(chat_id=ADMIN_CHAT_ID, text=msg, parse_mode="Markdown")
    except Exception as e:
        print(f"[ADMIN] ⚠️ No se pudo enviar mensaje al admin: {e}")

# ───────────────────────────────
# RUTAS FASTAPI
# ───────────────────────────────
@app.get("/")
def home():
    return {"ok": True, "service": "Bot Administrador", "status": "activo"}

@app.post("/debug/check")
async def debug_check(req: Request):
    """Permite probar manualmente la verificación desde Hoppscotch."""
    payload = await req.json()
    if payload.get("check") is True:
        await check_services()
        return {"ok": True, "msg": "Verificación ejecutada manualmente"}
    return {"ok": False, "msg": "Faltó el flag 'check': true"}

# ───────────────────────────────
# INICIO AUTOMÁTICO
# ───────────────────────────────
@scheduler.scheduled_job("interval", minutes=CHECK_INTERVAL_MIN)
async def scheduled_check():
    await check_services()

@app.on_event("startup")
async def startup_event():
    print("[ADMIN] 🚀 Bot Administrador iniciado correctamente.")
    scheduler.start()
    await alert_admin("🟢 *Bot Administrador* iniciado y vigilando los otros servicios.")

# ───────────────────────────────
# EJECUCIÓN LOCAL (opcional)
# ───────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=10000)
