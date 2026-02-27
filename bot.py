import os
import time
import asyncio
import re
import requests
from bs4 import BeautifulSoup
from telegram import Bot

# ================= VARIÁVEIS =================
TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

if not TOKEN or not CHAT_ID:
    raise Exception("⚠️ Variáveis TOKEN e CHAT_ID não definidas no Railway!")

bot = Bot(TOKEN)
enviados = set()  # evitar duplicados

# ================= AUXILIARES =================
def parse_price_to_float(price_str):
    if not price_str:
        return None
    m = re.search(r'(\d{1,3}(?:\.\d{3})*(?:,\d{2})|\d+(?:,\d{2})?)', price_str)
    if not m:
        return None
    return float(m.group(1).replace('.', '').replace(',', '.'))

async def enviar(msg):
    await bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode="HTML", disable_web_page_preview=False)

def enviar_oferta(termo, titulo, preco, link, origem):
    if link in enviados:
        return
    enviados.add(link)
    msg = (
        f"🔎 <b>{origem}</b>\n"
        f"📦 <b>{termo}</b>\n"
        f"💰 <b>{preco}</b>\n"
        f"🔗 <a href='{link}'>Abrir oferta</a>\n\n"
        f"📌 <i>{titulo}</i>"
    )
    try:
        asyncio.run(enviar(msg))
    except Exception as e:
        print("Erro ao enviar mensagem:", e)

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

# ================= BUSCAR AMAZON COM REQUESTS =================
def buscar_amazon_requests(termo, max_val=None):
    url = f"https://www.amazon.com.br/s?k={termo.replace(' ','+')}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/117.0.0.0 Safari/537.36"
    }
    try:
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
    except Exception as e:
        print("Erro ao acessar Amazon:", e)
        return []

    soup = BeautifulSoup(r.text, "html.parser")
    resultados = []

    for p in soup.select("div.s-result-item")[:10]:
        titulo_el = p.select_one("h2 span")
        preco_whole = p.select_one(".a-price-whole")
        preco_fraction = p.select_one(".a-price-fraction")
        link_el = p.select_one("h2 a")

        if not (titulo_el and preco_whole and preco_fraction and link_el):
            continue

        titulo = titulo_el.text.strip()
        preco_txt = preco_whole.text.strip() + "," + preco_fraction.text.strip()
        preco_float = parse_price_to_float(preco_txt)
        link = "https://www.amazon.com.br" + link_el.get("href")

        if max_val and preco_float and preco_float > max_val:
            continue

        resultados.append((titulo, f"R$ {preco_txt}", link))

    return resultados

# ================= LOOP PRINCIPAL =================
def main():
    termos = carregar_produtos()
    print("Bot iniciado com produtos:", termos)

    while True:
        try:
            for termo, max_val in termos:
                print("Buscando:", termo)
                resultados = buscar_amazon_requests(termo, max_val)
                for titulo, preco, link in resultados:
                    enviar_oferta(termo, titulo, preco, link, "Amazon")
        except Exception as e:
            print("Erro geral:", e)

        print("Aguardando 1 hora para próxima busca...")
        time.sleep(3600)  # roda a cada 1 hora

if __name__ == "__main__":
    main()
