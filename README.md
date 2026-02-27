
# Bot de Promoções (Telegram) — Deploy no Pella.app

## Arquivos
- `bot.py` — código do bot (limites por produto + limite global opcional via `MAX_PRICE`).
- `produtos.txt` — termos que o bot pesquisa. Você pode definir `max=` e `min=` por termo.
- `requirements.txt` — dependências Python instaladas automaticamente no Pella.

## Variáveis de Ambiente no Pella
- `TELEGRAM_TOKEN` — token do BotFather.
- `CHAT_ID` — seu chat ID (ex.: via @RawDataBot).
- `MAX_PRICE` *(opcional)* — limite GLOBAL em R$ (aplicado quando o termo não tem `max=`).
- `CHECK_INTERVAL` *(opcional)* — intervalo em segundos entre varreduras (padrão 600).

## Comando de inicialização
```
python bot.py
```

## Dica
- Edite `produtos.txt` para ajustar seus termos e limites.
- Se quiser evitar mensagens repetidas, me avise que adiciono cache (`seen.json`).
