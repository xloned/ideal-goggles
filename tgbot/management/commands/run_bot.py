"""
Команда Django для запуска Telegram-бота.

Использование:
  python manage.py run_bot --token <BOT_TOKEN>
  или
  export TELEGRAM_BOT_TOKEN=<token>
  python manage.py run_bot

Бот реализует:
  Лаб 5  — курсы валют с сайта ЦБ РФ через urllib.request
  Лаб 11 — мини CASE-система: визуальная компоновка y=F1(F2(F3(x)))
            с генерацией Python-кода (аналог генерации VBA в оригинальном задании)
"""

import os
import asyncio
import logging

from django.core.management.base import BaseCommand, CommandError

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    BotCommand,
)
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    filters,
    ContextTypes,
)

from tgbot.bot import (
    fetch_rates,
    build_rates_message,
    PRESET_CURRENCIES,
    FUNCTIONS,
    case_sessions,
    case_compute,
    case_generate_code,
)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ConversationHandler states для CASE-системы
CASE_F1, CASE_F2, CASE_F3, CASE_X = range(4)


# ─────────────────────────────────────────────────────────
# Общие обработчики
# ─────────────────────────────────────────────────────────

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = (
        "👋 <b>Привет! Я учебный бот (Лаб 5 + Лаб 11)</b>\n\n"
        "<b>Лаб 5 — Интернет-ресурсы:</b>\n"
        "  /rates — курсы валют ЦБ РФ (USD, EUR, CNY, GBP, JPY)\n"
        "  /rate &lt;КОД&gt; — курс конкретной валюты, например /rate CHF\n\n"
        "<b>Лаб 11 — CASE-система:</b>\n"
        "  /case — построить цепочку y = F₁(F₂(F₃(x)))\n"
        "          и получить сгенерированный Python-код\n\n"
        "  /help — это сообщение"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)


async def help_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await start(update, ctx)


# ─────────────────────────────────────────────────────────
# Лаб 5: Курсы валют
# ─────────────────────────────────────────────────────────

async def rates_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Показать курсы основных валют."""
    msg = await update.message.reply_text('⏳ Получаю данные с сервера ЦБ РФ...')
    data = fetch_rates()
    if not data:
        await msg.edit_text('❌ Не удалось получить данные. Попробуйте позже.')
        return
    text = build_rates_message(data)
    # Кнопки для быстрого запроса отдельных валют
    buttons = [
        [InlineKeyboardButton(code, callback_data=f'rate:{code}') for code in PRESET_CURRENCIES[:3]],
        [InlineKeyboardButton(code, callback_data=f'rate:{code}') for code in PRESET_CURRENCIES[3:]],
        [InlineKeyboardButton('🔄 Обновить', callback_data='rates:refresh')],
    ]
    await msg.edit_text(text, parse_mode=ParseMode.HTML,
                        reply_markup=InlineKeyboardMarkup(buttons))


async def rate_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Показать курс конкретной валюты: /rate USD."""
    if not ctx.args:
        await update.message.reply_text('Укажите код валюты, например: /rate USD')
        return
    code = ctx.args[0].upper()
    data = fetch_rates()
    if not data:
        await update.message.reply_text('❌ Не удалось получить данные ЦБ РФ.')
        return
    valutes = data.get('Valute', {})
    if code not in valutes:
        await update.message.reply_text(
            f'Валюта <b>{code}</b> не найдена. Попробуйте: USD, EUR, CNY, GBP, JPY, CHF...',
            parse_mode=ParseMode.HTML,
        )
        return
    text = build_rates_message(data, codes=[code])
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)


async def rates_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Обработка inline-кнопок в меню курсов валют."""
    query = update.callback_query
    await query.answer()
    action, *args = query.data.split(':')

    if action == 'rates' and args[0] == 'refresh':
        data = fetch_rates()
        if not data:
            await query.edit_message_text('❌ Не удалось обновить данные.')
            return
        text = build_rates_message(data)
        buttons = [
            [InlineKeyboardButton(code, callback_data=f'rate:{code}') for code in PRESET_CURRENCIES[:3]],
            [InlineKeyboardButton(code, callback_data=f'rate:{code}') for code in PRESET_CURRENCIES[3:]],
            [InlineKeyboardButton('🔄 Обновить', callback_data='rates:refresh')],
        ]
        await query.edit_message_text(text, parse_mode=ParseMode.HTML,
                                      reply_markup=InlineKeyboardMarkup(buttons))

    elif action == 'rate':
        code = args[0]
        data = fetch_rates()
        if not data:
            await query.edit_message_text('❌ Не удалось получить данные.')
            return
        text = build_rates_message(data, codes=[code])
        back_btn = [[InlineKeyboardButton('⬅️ Назад ко всем', callback_data='rates:refresh')]]
        await query.edit_message_text(text, parse_mode=ParseMode.HTML,
                                      reply_markup=InlineKeyboardMarkup(back_btn))


# ─────────────────────────────────────────────────────────
# Лаб 11: CASE-система
# ─────────────────────────────────────────────────────────

def _func_keyboard(step_label: str) -> InlineKeyboardMarkup:
    """Клавиатура выбора функции для шага F1/F2/F3."""
    buttons = [
        [InlineKeyboardButton(f'y = x  (тождественная)', callback_data='case_fn:identity')],
        [InlineKeyboardButton(f'y = 1/x  (обратная)',    callback_data='case_fn:inverse')],
        [InlineKeyboardButton(f'y = eˣ  (экспонента)',   callback_data='case_fn:exp')],
        [InlineKeyboardButton('❌ Отмена', callback_data='case_fn:cancel')],
    ]
    return InlineKeyboardMarkup(buttons)


async def case_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """Старт CASE-системы: выбор F3 (самая внутренняя функция)."""
    user_id = update.effective_user.id
    case_sessions[user_id] = {'funcs': [None, None, None]}

    await update.message.reply_text(
        '🔧 <b>CASE-система (Лаб 11)</b>\n\n'
        'Строим цепочку: <code>y = F₁( F₂( F₃(x) ) )</code>\n\n'
        '<b>Шаг 1 из 3</b> — выберите функцию <b>F₃</b> (самая внутренняя):',
        parse_mode=ParseMode.HTML,
        reply_markup=_func_keyboard('F₃'),
    )
    return CASE_F3


async def case_choose_f3(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    data = query.data.split(':')[1]
    if data == 'cancel':
        await query.edit_message_text('❌ Построение отменено. /case — начать заново.')
        return ConversationHandler.END

    user_id = update.effective_user.id
    case_sessions[user_id]['funcs'][2] = data
    fn = FUNCTIONS[data]
    await query.edit_message_text(
        f'✅ F₃ = <b>{fn["label"]}</b>\n\n'
        f'<b>Шаг 2 из 3</b> — выберите функцию <b>F₂</b>:',
        parse_mode=ParseMode.HTML,
        reply_markup=_func_keyboard('F₂'),
    )
    return CASE_F2


async def case_choose_f2(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    data = query.data.split(':')[1]
    if data == 'cancel':
        await query.edit_message_text('❌ Построение отменено. /case — начать заново.')
        return ConversationHandler.END

    user_id = update.effective_user.id
    case_sessions[user_id]['funcs'][1] = data
    fn = FUNCTIONS[data]
    f3_key = case_sessions[user_id]['funcs'][2]
    f3_label = FUNCTIONS[f3_key]['label']
    await query.edit_message_text(
        f'✅ F₂ = <b>{fn["label"]}</b>\n\n'
        f'Текущая цепочка: <code>F₂( F₃(x) ) = {fn["label"]} ∘ ({f3_label})</code>\n\n'
        f'<b>Шаг 3 из 3</b> — выберите функцию <b>F₁</b> (самая внешняя):',
        parse_mode=ParseMode.HTML,
        reply_markup=_func_keyboard('F₁'),
    )
    return CASE_F1


async def case_choose_f1(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    data = query.data.split(':')[1]
    if data == 'cancel':
        await query.edit_message_text('❌ Построение отменено. /case — начать заново.')
        return ConversationHandler.END

    user_id = update.effective_user.id
    session = case_sessions[user_id]
    session['funcs'][0] = data
    f1_key, f2_key, f3_key = session['funcs']
    f1 = FUNCTIONS[f1_key]
    f2 = FUNCTIONS[f2_key]
    f3 = FUNCTIONS[f3_key]

    summary = (
        f'✅ F₁ = <b>{f1["label"]}</b>\n\n'
        f'<b>Сконструированная цепочка:</b>\n'
        f'<code>y = F₁( F₂( F₃(x) ) )</code>\n'
        f'<code>y = {f1["label"]} ∘ ({f2["label"]}) ∘ ({f3["label"]})</code>\n\n'
        f'Введите значение <b>x</b> (число):'
    )
    await query.edit_message_text(summary, parse_mode=ParseMode.HTML)
    return CASE_X


async def case_input_x(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """Пользователь ввёл x — вычисляем и генерируем код."""
    text = update.message.text.strip().replace(',', '.')
    try:
        x_val = float(text)
    except ValueError:
        await update.message.reply_text('Введите числовое значение x, например: 2.5')
        return CASE_X

    user_id = update.effective_user.id
    session = case_sessions.get(user_id, {})
    f1_key, f2_key, f3_key = session.get('funcs', [None, None, None])
    if not all([f1_key, f2_key, f3_key]):
        await update.message.reply_text('Сессия устарела. Начните заново: /case')
        return ConversationHandler.END

    result, err = case_compute(f1_key, f2_key, f3_key, x_val)

    f1 = FUNCTIONS[f1_key]
    f2 = FUNCTIONS[f2_key]
    f3 = FUNCTIONS[f3_key]

    if err:
        msg = (
            f'⚠️ <b>Ошибка вычисления</b>\n'
            f'{err}\n\n'
            f'Цепочка: <code>{f1["label"]} ∘ ({f2["label"]}) ∘ ({f3["label"]})</code>\n'
            f'x = {x_val}\n\n'
            f'Введите другое значение x или /case для начала.'
        )
    else:
        msg = (
            f'✅ <b>Результат вычисления</b>\n\n'
            f'Цепочка: <code>y = F₁(F₂(F₃(x)))</code>\n'
            f'  F₁ = {f1["label"]}\n'
            f'  F₂ = {f2["label"]}\n'
            f'  F₃ = {f3["label"]}\n\n'
            f'<b>x = {x_val}</b>\n'
            f'<b>y = {result:.6g}</b>\n\n'
            f'Введите другое x или /case для новой цепочки.'
        )

    await update.message.reply_text(msg, parse_mode=ParseMode.HTML)

    # Отдельным сообщением — сгенерированный Python-код
    code = case_generate_code(f1_key, f2_key, f3_key)
    code_msg = (
        f'<b>🖥️ Сгенерированный Python-код (Лаб 11):</b>\n\n'
        f'<pre><code>{code}</code></pre>'
    )
    await update.message.reply_text(code_msg, parse_mode=ParseMode.HTML)
    return CASE_X   # остаёмся в состоянии ввода x — можно ввести ещё


async def case_cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text('❌ CASE-система закрыта. /case — начать заново.')
    return ConversationHandler.END


# ─────────────────────────────────────────────────────────
# Сборка и запуск приложения
# ─────────────────────────────────────────────────────────

def build_application(token: str) -> Application:
    app = Application.builder().token(token).build()

    # Лаб 5 — курсы валют
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('help',  help_cmd))
    app.add_handler(CommandHandler('rates', rates_cmd))
    app.add_handler(CommandHandler('rate',  rate_cmd))
    app.add_handler(CallbackQueryHandler(rates_callback, pattern=r'^(rates|rate):'))

    # Лаб 11 — CASE-система (ConversationHandler)
    case_conv = ConversationHandler(
        entry_points=[CommandHandler('case', case_cmd)],
        states={
            CASE_F3: [CallbackQueryHandler(case_choose_f3, pattern=r'^case_fn:')],
            CASE_F2: [CallbackQueryHandler(case_choose_f2, pattern=r'^case_fn:')],
            CASE_F1: [CallbackQueryHandler(case_choose_f1, pattern=r'^case_fn:')],
            CASE_X:  [MessageHandler(filters.TEXT & ~filters.COMMAND, case_input_x)],
        },
        fallbacks=[CommandHandler('cancel', case_cancel)],
        allow_reentry=True,
    )
    app.add_handler(case_conv)

    return app


class Command(BaseCommand):
    help = 'Запустить Telegram-бота (Лаб 5: курсы валют, Лаб 11: CASE-система)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--token',
            type=str,
            default='',
            help='Telegram Bot Token (или переменная окружения TELEGRAM_BOT_TOKEN)',
        )

    def handle(self, *args, **options):
        from django.conf import settings as django_settings
        token = (options['token']
                 or os.environ.get('TELEGRAM_BOT_TOKEN', '')
                 or getattr(django_settings, 'TELEGRAM_BOT_TOKEN', ''))
        if not token:
            raise CommandError(
                'Укажите токен бота:\n'
                '  python manage.py run_bot --token <TOKEN>\n'
                'или задайте переменную окружения TELEGRAM_BOT_TOKEN'
            )

        self.stdout.write(self.style.SUCCESS(
            '🤖 Запуск Telegram-бота...\n'
            '   Лаб 5: /rates — курсы валют ЦБ РФ\n'
            '   Лаб 11: /case — CASE-система (y = F1(F2(F3(x))))\n'
            'Нажмите Ctrl+C для остановки.'
        ))

        app = build_application(token)
        app.run_polling(allowed_updates=Update.ALL_TYPES)
