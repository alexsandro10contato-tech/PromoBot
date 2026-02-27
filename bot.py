import requests
from bs4 import BeautifulSoup
from telegram import Bot
import time
import os
import re

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
MAX_PRICE_GLOBAL = float(os.getenv("MAX_PRICE")) if os.getenv("MAX_PRICE") else None

if not TOKEN or not CHAT_ID:
    raise RuntimeError("Defina as variáveis de ambiente TELEGRAM_TOKEN e CHAT_ID no painel do Pella.")

bot = Bot(TOKEN)

# --- Utilidades ---

def parse_price_to_float(price_str: str):
    """Converte 'R$ 1.234,56' -> 1234.56 ; '1.299' -> 1299.0"""
    if not price_str:
        return None
    m = re.search(r'(\d{1,3}(?:\.\d{3})*(?:,\d{2})|\d+(?:,\d{2})?)', price_str)
    if not m:
        return None
    val = m.group(1).replace('.', '').replace(',', '.')
    try:
        return float(val)
    except:
        return None


def parse_produto_line(line: str):
    """
    Entrada: 'iphone 13 | max=2500' -> ('iphone 13', {'max': 2500.0})
    Suporta: max=, min=
    """
    parts = [p.strip() for p in line.split('|')]
    termo = parts[0]
    config = {}
    if len(parts) > 1:
        for chunk in parts[1:]:
            if chunk.lower().startswith('max='):
                try:
                    config['max'] = float(chunk.split('=', 1)[1].strip().replace(',', '.'))
                except:
                    pass
            if chunk.lower().startswith('min='):
                try:
                    config['min'] = float(chunk.split('=', 1)[1].strip().replace(',', '.'))
                except:
                    pass
    return termo, config


# --- Consulta simples ao Google Shopping ---

def pesquisar_google(termo, max_local=None, min_local=None):
    url = f"https://www.google.com/search?q={termo.replace(' ', '+')}+comprar&tbm=shop&hl=pt-BR"
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers, timeout=20)
    soup = BeautifulSoup(r.text, "html.parser")

    itens = soup.select("div.sh-dgr__content")
    ofertas = []
    for item in itens[:10]:
        title_el = item.select_one("h3")
        price_el = item.select_one(".a8Pemb")
        link_el = item.select_one("a")

        titulo = title_el.text.strip() if title_el else ""
        preco_txt = price_el.text.strip() if price_el else ""
        link = ("https://www.google.com" + link_el.get("href")) if (link_el and link_el.get("href")) else ""

        preco_float = parse_price_to_float(preco_txt)

        # filtros
        if preco_float is not None:
            if min_local is not None and preco_float < min_local:
                continue
            if max_local is not None and preco_float > max_local:
                continue
            if max_local is None and MAX_PRICE_GLOBAL is not None and preco_float > MAX_PRICE_GLOBAL:
                continue

        if titulo and link:
            ofertas.append((titulo, preco_txt, preco_float, link))
    return ofertas


def carregar_produtos_config():
    linhas = []
    with open("produtos.txt", "r", encoding="utf-8") as f:
        for raw in f.readlines():
            line = raw.strip()
            if not line or line.startswith('#'):
                continue
            termo, cfg = parse_produto_line(line)
            linhas.append((termo, cfg))
    return linhas


def enviar_oferta(termo, titulo, preco_txt, link):
    msg = (
        f"🔥 *Oferta encontrada!*\n\n"
        f"📦 *Termo:* {termo}\n"
        f"💰 *Preço:* {preco_txt}\n"
        f"🔗 {link}\n\n"
        f"📌 _{titulo}_"
    )
    bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode="Markdown")


def iniciar_bot():
    print("Bot rodando 24h no Pella (limites por produto e global suportados).")
    intervalo = int(os.getenv("CHECK_INTERVAL", "600"))  # padrão 10 minutos
    while True:
        termos = carregar_produtos_config()
        for termo, cfg in termos:
            ofertas = pesquisar_google(termo, max_local=cfg.get('max'), min_local=cfg.get('min'))
            for titulo, preco_txt, preco_float, link in ofertas:
                enviar_oferta(termo, titulo, preco_txt, link)
                time.sleep(1)
        time.sleep(intervalo)


if __name__ == "__main__":
    iniciar_bot()
