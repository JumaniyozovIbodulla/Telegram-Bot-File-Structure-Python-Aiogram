# GuestMode — aiogram 3.34.0 (Bot API 10.5) Senior Template

Zamonaviy **aiogram 3.34.0** va **Telegram Bot API 10.5** asosida qurilgan, bitta `BOT_TOKEN` qo'yib darhol ishga tushirishga tayyor production-darajadagi Telegram bot shabloni.

## Asosiy imkoniyatlar

- **Typed Config (`pydantic-settings`)**: `.env` orqali xavfsiz sozlamalar (`BOT_TOKEN` yetarli, `ADMINS` va boshqa parametrlar ixtiyoriy).
- **Zero-config Async SQLite (`aiosqlite`)**: Hech qanday tashqi DB o'rnatmasdan ishlaydi (`data/bot.db`).
- **Guest Mode (Mehmon rejimi)**:
  - Yangi foydalanuvchilar avtomatik `guest` rolida boshlaydi.
  - Kunlik so'rov limiti (`GUEST_DAILY_LIMIT`) va alohida rate-limit (`RATE_LIMIT_GUEST`).
  - Adminlar `/admin` orqali global Guest Mode'ni yoqib-o'chirishi mumkin.
  - Mehmonlar `/register` (**FSM Scenes Wizard**) orqali to'liq foydalanuvchiga (`user`) aylanishi mumkin.
- **aiogram 3.34.0 & Bot API 10.5 funksiyalari**:
  - `DefaultBotProperties` (`ParseMode.HTML`, `link_preview_is_disabled=True`)
  - `BotFullInfo` & `bot.usernames()` (`/botinfo`)
  - `bot.set_my_settings(...)` (`supports_guest_queries` va boshqa Bot API 10.5 sozlamalari)
  - `bot.send_message_draft(...)` (AI / Draft Streaming)
  - `message_effect_id` + `set_message_reaction` (`ReactionTypeEmoji`)
  - `ChatActionSender.typing(...)`
  - `InputChecklist` / `InputChecklistTask` (Telegram Business Checklist API strukturasi)
  - `html.expandable_blockquote`, `html.spoiler`, `LinkPreviewOptions`
  - Scoped `BotCommand` (`Private`, `Group`, `Admin`)
  - `UserContextMiddleware`, `ThrottlingMiddleware`, `IsAdminFilter`, Global Error Handler

## Ishga tushirish

1. `.env.example` dan `.env` yarating va `BOT_TOKEN` ni kiriting:
   ```bash
   cp .env.example .env
   ```
   `.env` ichida:
   ```env
   BOT_TOKEN=123456789:your_bot_token_here
   ADMINS=123456789
   ```
2. Virtual muhitni faollashtirib botni ishga tushiring:
   ```bash
   source .venv/bin/activate
   python main.py
   ```

## Docker bilan deploy qilish

1. `.env` faylini yarating (`BOT_TOKEN` ni kiriting):
   ```bash
   cp .env.example .env
   ```
2. Container'ni build qilib fonda ishga tushiring:
   ```bash
   docker compose up -d --build
   ```
3. Loglarni kuzatish va to'xtatish:
   ```bash
   docker compose logs -f bot
   docker compose down
   ```

## Makefile komandalari

Barcha local va prod komandalarni ko'rish uchun:
```bash
make help
```
Asosiy komandalar: `make run`, `make test`, `make check`, `make up`, `make logs`, `make restart`, `make down`, `make update`.

## Testlarni ishga tushirish

```bash
./.venv/bin/pytest -v
```
