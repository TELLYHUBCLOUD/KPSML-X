#!/usr/bin/env python3
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from pyrogram.filters import command, regex
from aiohttp import ClientSession
from html import escape
from urllib.parse import quote

from bot import bot, LOGGER, config_dict, get_client
from bot.helper.telegram_helper.message_utils import editMessage, sendMessage
from bot.helper.ext_utils.telegraph_helper import telegraph
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.ext_utils.bot_utils import get_readable_file_size, sync_to_async, new_task, checking_access
from bot.helper.telegram_helper.button_build import ButtonMaker

PLUGINS = []
SITES = None
TELEGRAPH_LIMIT = 300


async def initiate_search_tools():
    """
    Initializes search tools, including qBittorrent search plugins and API sites.
    """
    qbclient = await sync_to_async(get_client)
    qb_plugins = await sync_to_async(qbclient.search_plugins)

    # Setup search plugins
    if SEARCH_PLUGINS := config_dict['SEARCH_PLUGINS']:
        globals()['PLUGINS'] = []
        src_plugins = eval(SEARCH_PLUGINS)
        if qb_plugins:
            names = [plugin['name'] for plugin in qb_plugins]
            await sync_to_async(qbclient.search_uninstall_plugin, names=names)
        await sync_to_async(qbclient.search_install_plugin, src_plugins)
    elif qb_plugins:
        for plugin in qb_plugins:
            await sync_to_async(qbclient.search_uninstall_plugin, names=plugin['name'])
        globals()['PLUGINS'] = []

    await sync_to_async(qbclient.auth_log_out)

    # Setup search API
    if SEARCH_API_LINK := config_dict['SEARCH_API_LINK']:
        global SITES
        try:
            async with ClientSession(trust_env=True) as c:
                async with c.get(f'{SEARCH_API_LINK}/api/v1/sites') as res:
                    data = await res.json()
            SITES = {str(site): str(site).capitalize() for site in data['supported_sites']}
            SITES['all'] = 'All'
        except Exception as e:
            LOGGER.error(f"Failed to fetch sites from SEARCH_API_LINK: {e}. Make sure you're using the latest API version.")
            SITES = None


async def __search(key, site, message, method):
    """
    Performs a torrent search using either the API or qBittorrent plugins.
    """
    if method.startswith('api'):
        SEARCH_API_LINK = config_dict['SEARCH_API_LINK']
        SEARCH_LIMIT = config_dict['SEARCH_LIMIT']

        if method == 'apisearch':
            LOGGER.info(f"API Search: '{key}' on {site}")
            api = f"{SEARCH_API_LINK}/api/v1/all/search?query={key}&limit={SEARCH_LIMIT}" if site == 'all' else f"{SEARCH_API_LINK}/api/v1/search?site={site}&query={key}&limit={SEARCH_LIMIT}"
        elif method == 'apitrend':
            LOGGER.info(f"API Trend from {site}")
            api = f"{SEARCH_API_LINK}/api/v1/all/trending?limit={SEARCH_LIMIT}" if site == 'all' else f"{SEARCH_API_LINK}/api/v1/trending?site={site}&limit={SEARCH_LIMIT}"
        elif method == 'apirecent':
            LOGGER.info(f"API Recent from {site}")
            api = f"{SEARCH_API_LINK}/api/v1/all/recent?limit={SEARCH_LIMIT}" if site == 'all' else f"{SEARCH_API_LINK}/api/v1/recent?site={site}&limit={SEARCH_LIMIT}"

        try:
            async with ClientSession(trust_env=True) as c:
                async with c.get(api) as res:
                    search_results = await res.json()

            if 'error' in search_results or search_results.get('total', 0) == 0:
                await editMessage(message, f"❌ No results found for <i>{key}</i> on <i>{SITES.get(site)}</i>.")
                return

            msg = f"🔍 <b>Found {min(search_results['total'], TELEGRAPH_LIMIT)} results for <i>{key}</i> on <i>{SITES.get(site)}</i></b>"
            if method == 'apitrend':
                msg = f"📈 <b>Top {min(search_results['total'], TELEGRAPH_LIMIT)} trending results on <i>{SITES.get(site)}</i></b>"
            elif method == 'apirecent':
                msg = f"🆕 <b>Latest {min(search_results['total'], TELEGRAPH_LIMIT)} results on <i>{SITES.get(site)}</i></b>"

            search_results = search_results['data']
        except Exception as e:
            await editMessage(message, f"⛔ API Error: {e}")
            return
    else: # qbittorrent search plugins
        LOGGER.info(f"Plugin Search: '{key}' on {site}")
        client = await sync_to_async(get_client)
        search = await sync_to_async(client.search_start, pattern=key, plugins=site, category='all')
        search_id = search.id

        while True:
            result_status = await sync_to_async(client.search_status, search_id=search_id)
            status = result_status[0].status
            if status != 'Running':
                break

        dict_search_results = await sync_to_async(client.search_results, search_id=search_id, limit=TELEGRAPH_LIMIT)
        search_results = dict_search_results.results
        total_results = dict_search_results.total

        if total_results == 0:
            await editMessage(message, f"❌ No results found for <i>{key}</i> on <i>{site.capitalize()}</i>.")
            return

        msg = f"🔍 <b>Found {min(total_results, TELEGRAPH_LIMIT)} results for <i>{key}</i> on <i>{site.capitalize()}</i></b>"
        await sync_to_async(client.search_delete, search_id=search_id)
        await sync_to_async(client.auth_log_out)

    link = await __getResult(search_results, key, message, method)
    buttons = ButtonMaker()
    buttons.ubutton("📄 View Results", link)
    await editMessage(message, msg, buttons.build_menu(1))


async def __getResult(search_results, key, message, method):
    """
    Formats search results into a Telegraph page.
    """
    telegraph_content = []

    if method == 'apirecent':
        title = "🆕 API Recent Results"
    elif method == 'apisearch':
        title = f"🔍 API Search Results for '{key}'"
    elif method == 'apitrend':
        title = "📈 API Trending Results"
    else:
        title = f"🔌 Plugin Search Results for '{key}'"

    html_content = f"<h4>{title}</h4>"

    for index, result in enumerate(search_results, start=1):
        item_html = ""
        if method.startswith('api'):
            try:
                if 'name' in result:
                    item_html += f"<code><a href='{result['url']}'>{escape(result['name'])}</a></code><br>"
                if 'torrents' in result:
                    for subres in result['torrents']:
                        item_html += f"<b>Quality:</b> {subres.get('quality', 'N/A')} | <b>Type:</b> {subres.get('type', 'N/A')} | <b>Size:</b> {subres.get('size', 'N/A')}<br>"
                        if 'torrent' in subres:
                            item_html += f"<a href='{subres['torrent']}'>📥 Direct Link</a><br>"
                        elif 'magnet' in subres:
                            item_html += f"<b>Share Magnet:</b> <a href='http://t.me/share/url?url={subres['magnet']}'>🔗 Telegram</a><br>"
                    item_html += '<br>'
                else:
                    item_html += f"<b>Size:</b> {result.get('size', 'N/A')}<br>"
                    if 'seeders' in result and 'leechers' in result:
                        item_html += f"<b>Seeders:</b> {result['seeders']} | <b>Leechers:</b> {result['leechers']}<br>"
                    if 'torrent' in result:
                        item_html += f"<a href='{result['torrent']}'>📥 Direct Link</a><br><br>"
                    elif 'magnet' in result:
                        item_html += f"<b>Share Magnet:</b> <a href='http://t.me/share/url?url={quote(result['magnet'])}'>🔗 Telegram</a><br><br>"
                    else:
                        item_html += '<br>'
            except Exception as e:
                LOGGER.error(f"Error processing API result: {e}")
                continue
        else: # plugin result
            item_html += f"<a href='{result.descrLink}'>{escape(result.fileName)}</a><br>"
            item_html += f"<b>Size:</b> {get_readable_file_size(result.fileSize)}<br>"
            item_html += f"<b>Seeders:</b> {result.nbSeeders} | <b>Leechers:</b> {result.nbLeechers}<br>"
            link = result.fileUrl
            if link.startswith('magnet:'):
                item_html += f"<b>Share Magnet:</b> <a href='http://t.me/share/url?url={quote(link)}'>🔗 Telegram</a><br><br>"
            else:
                item_html += f"<a href='{link}'>📥 Direct Link</a><br><br>"

        if len(html_content.encode('utf-8')) + len(item_html.encode('utf-8')) > 39000:
            telegraph_content.append(html_content)
            html_content = ""

        html_content += item_html

        if index == TELEGRAPH_LIMIT:
            break

    if html_content:
        telegraph_content.append(html_content)

    await editMessage(message, f"✍️ Creating {len(telegraph_content)} Telegraph page(s)...")

    paths = [(await telegraph.create_page(title=f"{config_dict['TITLE_NAME']} Torrent Search", content=content))["path"] for content in telegraph_content]

    if len(paths) > 1:
        await editMessage(message, f"⚙️ Editing {len(telegraph_content)} Telegraph pages...")
        await telegraph.edit_telegraph(paths, telegraph_content)

    return f"https://telegra.ph/{paths[0]}"


def __api_buttons(user_id, method):
    buttons = ButtonMaker()
    for data, name in SITES.items():
        buttons.ibutton(name, f"torser {user_id} {data} {method}")
    buttons.ibutton("❌ Cancel", f"torser {user_id} cancel")
    return buttons.build_menu(2)


async def __plugin_buttons(user_id):
    buttons = ButtonMaker()
    if not PLUGINS:
        qbclient = await sync_to_async(get_client)
        pl = await sync_to_async(qbclient.search_plugins)
        for name in pl:
            PLUGINS.append(name['name'])
        await sync_to_async(qbclient.auth_log_out)
    for siteName in PLUGINS:
        buttons.ibutton(siteName.capitalize(), f"torser {user_id} {siteName} plugin")
    buttons.ibutton('All', f"torser {user_id} all plugin")
    buttons.ibutton("❌ Cancel", f"torser {user_id} cancel")
    return buttons.build_menu(2)


async def torrentSearch(_, message):
    user_id = message.from_user.id
    buttons = ButtonMaker()
    key = message.text.split() if message.text else ['/cmd']

    msg, btn = await checking_access(user_id)
    if msg is not None:
        await sendMessage(message, msg, btn.build_menu(1))
        return

    SEARCH_PLUGINS = config_dict['SEARCH_PLUGINS']
    if SITES is None and not SEARCH_PLUGINS:
        await sendMessage(message, "⚠️ No search API link or plugins are configured.")
    elif len(key) == 1 and SITES is None:
        await sendMessage(message, "Please provide a search query after the command.")
    elif len(key) == 1:
        buttons.ibutton('📈 Trending', f"torser {user_id} apitrend")
        buttons.ibutton('🆕 Recent', f"torser {user_id} apirecent")
        buttons.ibutton("❌ Cancel", f"torser {user_id} cancel")
        await sendMessage(message, "Please provide a search query or select an option.", buttons.build_menu(2))
    elif SITES is not None and SEARCH_PLUGINS:
        buttons.ibutton('🌐 API', f"torser {user_id} apisearch")
        buttons.ibutton('🔌 Plugins', f"torser {user_id} plugin")
        buttons.ibutton("❌ Cancel", f"torser {user_id} cancel")
        await sendMessage(message, 'Choose your search method:', buttons.build_menu(2))
    elif SITES is not None:
        button = __api_buttons(user_id, "apisearch")
        await sendMessage(message, 'Select a site to search via API:', button)
    else:
        button = await __plugin_buttons(user_id)
        await sendMessage(message, 'Select a site to search via plugins:', button)


@new_task
async def torrentSearchUpdate(_, query):
    user_id = query.from_user.id
    message = query.message
    key = message.reply_to_message.text.split(maxsplit=1)
    key = key[1].strip() if len(key) > 1 else None
    data = query.data.split()

    if user_id != int(data[1]):
        return await query.answer("🔒 This is not for you!", show_alert=True)

    await query.answer()
    action = data[2]

    if action.startswith('api'):
        button = __api_buttons(user_id, action)
        await editMessage(message, 'Select a site:', button)
    elif action == 'plugin':
        button = await __plugin_buttons(user_id)
        await editMessage(message, 'Select a site:', button)
    elif action != "cancel":
        site = data[2]
        method = data[3]
        if method.startswith('api'):
            if key is None:
                endpoint = 'Trending' if method == 'apitrend' else 'Recent'
                await editMessage(message, f"📋 <b>Listing {endpoint} items from <i>{SITES.get(site)}</i>...</b>")
            else:
                await editMessage(message, f"🔎 <b>Searching for <i>{key}</i> on <i>{SITES.get(site)}</i>...</b>")
        else:
            await editMessage(message, f"🔌 <b>Searching for <i>{key}</i> on <i>{site.capitalize()}</i>...</b>")
        await __search(key, site, message, method)
    else: # cancel
        await editMessage(message, "✅ Search has been cancelled.")


bot.add_handler(MessageHandler(torrentSearch, filters=command(
    BotCommands.SearchCommand) & CustomFilters.authorized & ~CustomFilters.blacklisted))
bot.add_handler(CallbackQueryHandler(
    torrentSearchUpdate, filters=regex("^torser")))
