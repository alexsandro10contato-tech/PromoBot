import os
import time
import asyncio
from telegram import Bot
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import re

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

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
    await bot.send_message(chat_id=CHAT_ID, text=msg)

def enviar_oferta(termo, titulo, preco, link, origem):
    if link in enviados:
        return
    enviados.add(link)
    msg = f"🔎 <b>{origem}</b>\n📦 <b>{termo}</b>\n💰 <b>{preco}</b>\n🔗 <a href='{link}'>Abrir oferta</a>\n\n📌 <i>{titulo}</i>"
    try:
        asyncio.run(enviar(msg))
    except:
        pass

# ================= CARREGAR PRODUTOS =================
def carregar_produtos():
    termos = []
    with open("produtos.txt", "r", encoding="utf-8") as f:
        for linha in f:
            linha = linha.strip()
            if not linha or linha.lstrip().startswith("#"):
                continue

            partes = [p.strip() for p in linha.split("|")]
            termo = partes[0]
            max_val = None
            for p in partes[1:]:
                if p.lower().startswith("max="):
                    max_val = float(p.split("=")[1].replace(",", "."))
            termos.append((termo, max_val))
    return termos

# ================= SELENIUM =================
def criar_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.binary_location = "/usr/bin/chromium"
    return webdriver.Chrome(options=options)

# ================= BUSCAR AMAZON =================
def buscar_amazon(termo, max_val=None):
    driver = criar_driver()
    driver.get(f"https://www.amazon.com.br/s?k={termo.replace(' ','+')}")
    time.sleep(5)

    produtos = driver.find_elements(By.CSS_SELECTOR, "div.s-result-item")
    resultados = []

    for p in produtos[:10]:
        try:
            titulo_el = p.find_element(By.CSS_SELECTOR, "h2 span")
            preco_whole = p.find_element(By.CSS_SELECTOR, ".a-price-whole")
            preco_fraction = p.find_element(By.CSS_SELECTOR, ".a-price-fraction")
            link_el = p.find_element(By.CSS_SELECTOR, "h2 a")

            titulo = titulo_el.text.strip()
            preco_txt = preco_whole.text.strip() + "," + preco_fraction.text.strip()
            preco_float = parse_price_to_float(preco_txt)
            link = "https://www.amazon.com.br" + link_el.get_attribute("href")

            if max_val and preco_float and preco_float > max_val:
                continue

            resultados.append((titulo, f"R$ {preco_txt}", link))
        except:
            continue

    driver.quit()
    return resultados

# ================= LOOP PRINCIPAL =================
def main():
    termos = carregar_produtos()
    print("Bot iniciado com produtos:", termos)

    while True:
        try:
            for termo, max_val in termos:
                print("Buscando:", termo)
                for titulo, preco, link in buscar_amazon(termo, max_val):
                    enviar_oferta(termo, titulo, preco, link, "Amazon")
        except Exception as e:
            print("Erro geral:", e)
        time.sleep(3600)  # roda a cada 1 hora

if __name__ == "__main__":
    main()
