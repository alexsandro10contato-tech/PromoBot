import os
import time
import asyncio
import re
import feedparser
from telegram import Bot

# ================= VARIÁVEIS =================
TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

if not TOKEN or not CHAT_ID:
    raise Exception("⚠️ Variáveis TOKEN e CHAT_ID não definidas no Railway!")

bot = Bot(TOKEN)
enviados = set()

# ================= EXTRAIR PREÇO =================
def extrair_preco(texto):
    match = re.search(r'R\$\s?(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)', texto)
    if match:
        valor = match.group(1)
        return float(valor.replace('.', '').replace(',', '.'))
    return None

# ================= ENVIAR TELEGRAM =================
async def enviar(msg):
    await bot.send_message(
        chat_id=CHAT_ID,
        text=msg,
        parse_mode="HTML",
        disable_web_page_preview=False
    )

# ================= CARREGAR PRODUTOS =================
def carregar_produtos():
    termos = []
    with open("produtos.txt", "r", encoding="utf-8") as f:
        for linha in f:
            linha = linha.strip()
            if not linha or linha.startswith("#"):
                continue

            partes = [p.strip() for p in linha.split("|")]
            termo = partes[0]
            max_val = None

            for p in partes[1:]:
                if p.lower().startswith("max="):
                    try:
                        max_val = float(p.split("=")[1].replace(",", "."))
                    except:
                        pass

            termos.append((termo, max_val))

    return termos

# ================= BUSCAR GOOGLE RSS =================
def buscar_google_rss(termo, max_val=None):
    query = termo.replace(" ", "+")
    url = f"https://news.google.com/rss/search?q={query}"

    feed = feedparser.parse(url)
    resultados = []

    for entry in feed.entries[:10]:
        titulo = entry.title
        link = entry.link
        preco = extrair_preco(titulo)

        if max_val and preco and preco > max_val:
            continue

        resultados.append((titulo, link, preco))

    return resultados

# ================= LOOP PRINCIPAL =================
async def main():
    termos = carregar_produtos()
    print("Bot iniciado com produtos:", termos)

    while True:
        try:
            for termo, max_val in termos:
                print("Buscando:", termo)
                resultados = buscar_google_rss(termo, max_val)

                for titulo, link, preco in resultados:
                    if link in enviados:
                        continue

                    enviados.add(link)

                    preco_texto = f"💰 <b>R$ {preco:.2f}</b>\n" if preco else ""

                    msg = (
                        f"🔎 <b>Google Shopping</b>\n"
                        f"📦 <b>{termo}</b>\n"
                        f"{preco_texto}"
                        f"🔗 <a href='{link}'>Abrir oferta</a>\n\n"
                        f"📌 <i>{titulo}</i>"
                    )

                    await enviar(msg)

        except Exception as e:
            print("Erro geral:", e)

        print("Aguardando 30 minutos...")
        await asyncio.sleep(1800)

if __name__ == "__main__":
    asyncio.run(main())
