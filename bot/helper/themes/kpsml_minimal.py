#!/usr/bin/env python3

class KPSMLStyle:
    # ----------------------
    # async def start(client, message) ---> __main__.py
    ST_BN1_NAME = '👨‍💻 Oᴡɴᴇʀ'
    ST_BN1_URL = 'https://t.me/tellyhubowner'
    ST_BN2_NAME = '🌐 Uᴘᴅᴀᴛᴇs'
    ST_BN2_URL = 'https://t.me/telly_mirror'
    ST_MSG = '''<i>Tʜɪs ʙᴏᴛ ᴄᴀɴ ᴍɪʀʀᴏʀ ᴀʟʟ ʏᴏᴜʀ ʟɪɴᴋs|ғɪʟᴇs|ᴛᴏʀʀᴇɴᴛs ᴛᴏ Gᴏᴏɢʟᴇ Dʀɪᴠᴇ ᴏʀ ᴀɴʏ ʀᴄʟᴏɴᴇ ᴄʟᴏᴜᴅ ᴏʀ ᴛᴏ ᴛᴇʟᴇɢʀᴀᴍ ᴏʀ ᴛᴏ ᴅᴅʟ sᴇʀᴠᴇʀs</i>
<b>Tʏᴘᴇ {help_command} ᴛᴏ ɢᴇᴛ ᴀ ʟɪsᴛ ᴏғ ᴀᴠᴀɪʟᴀʙʟᴇ ᴄᴏᴍᴍᴀɴᴅs</b>'''
    ST_BOTPM = '''<i>Nᴏᴡ, Tʜɪs ʙᴏᴛ ᴡɪʟʟ sᴇɴᴅ ᴀʟʟ ʏᴏᴜʀ ғɪʟᴇs ᴀɴᴅ ʟɪɴᴋs ʜᴇʀᴇ. Sᴛᴀʀᴛ Usɪɴɢ...</i>'''
    ST_UNAUTH = '''<i>Yᴏᴜ Aʀᴇ ɴᴏᴛ Aᴜᴛʜᴏʀɪᴢᴇᴅ Usᴇʀ! 💔 \nDᴇᴘʟᴏʏ ʏᴏᴜʀ ᴏᴡɴ WZML-X Mɪʀʀᴏʀ-Lᴇᴇᴄʜ ʙᴏᴛ</i>'''
    OWN_TOKEN_GENERATE = '''<b>Tᴇᴍᴘᴏʀᴀʀʏ Tᴏᴋᴇɴ ɪs ɴᴏᴛ ʏᴏᴜʀs!</b>\n\n<i>Kɪɴᴅʟʏ ɢᴇɴᴇʀᴀᴛᴇ ʏᴏᴜʀ ᴏᴡɴ.</i>'''
    USED_TOKEN = '''<b>Tᴇᴍᴘᴏʀᴀʀʏ Tᴏᴋᴇɴ ᴀʟʀᴇᴀᴅʏ ᴜsᴇᴅ!</b>\n\n<i>Kɪɴᴅʟʏ ɢᴇɴᴇʀᴀᴛᴇ ᴀ ɴᴇᴡ ᴏɴᴇ.</i>'''
    LOGGED_PASSWORD = '''<b>Bᴏᴛ Aʟʀᴇᴀᴅʏ Lᴏɢɢᴇᴅ Iɴ ᴠɪᴀ Pᴀssᴡᴏʀᴅ</b>\n\n<i>Nᴏ Nᴇᴇᴅ ᴛᴏ Aᴄᴄᴇᴘᴛ Tᴇᴍᴘ Tᴏᴋᴇɴs.</i>'''
    ACTIVATE_BUTTON = 'Aᴄᴛɪᴠᴀᴛᴇ Tᴇᴍᴘᴏʀᴀʀʏ Tᴏᴋᴇɴ'
    TOKEN_MSG = '''<b><u>Gᴇɴᴇʀᴀᴛᴇᴅ Tᴇᴍᴘᴏʀᴀʀʏ Lᴏɢɪɴ Tᴏᴋᴇɴ!</u></b>
<b>Tᴇᴍᴘ Tᴏᴋᴇɴ:</b> <code>{token}</code>
<b>Vᴀʟɪᴅɪᴛʏ:</b> {validity}'''
    # ---------------------
    # async def token_callback(_, query): ---> __main__.py
    ACTIVATED = '✅️ Aᴄᴛɪᴠᴀᴛᴇᴅ ✅'
    # ---------------------
    # async def login(_, message): --> __main__.py
    LOGGED_IN = '<b>Aʟʀᴇᴀᴅʏ Bᴏᴛ Lᴏɢɪɴ Iɴ!</b>'
    INVALID_PASS = '<b>Iɴᴠᴀʟɪᴅ Pᴀssᴡᴏʀᴅ!</b>\n\nKɪɴᴅʟʏ ᴘᴜᴛ ᴛʜᴇ ᴄᴏʀʀᴇᴄᴛ Pᴀssᴡᴏʀᴅ .'
    PASS_LOGGED = '<b>Bᴏᴛ Pᴇʀᴍᴀɴᴇɴᴛ Lᴏɢɪɴ Sᴜᴄᴄᴇssғᴜʟʟʏ!</b>'
    LOGIN_USED = '<b>Bᴏᴛ Lᴏɢɪɴ Usᴀɢᴇ :</b>\n\n<code>/cmd [ᴘᴀssᴡᴏʀᴅ]</code>'
    # ---------------------
    # async def log(_, message): ---> __main__.py
    LOG_DISPLAY_BT = '📑 Lᴏɢ Dɪsᴘʟᴀʏ'
    WEB_PASTE_BT = '📨 Wᴇʙ Pᴀsᴛᴇ (SB)'
    # ---------------------
    # async def bot_help(client, message): ---> __main__.py
    BASIC_BT = 'Bᴀsɪᴄ'
    USER_BT = 'Usᴇʀs'
    MICS_BT = 'Mɪᴄs'
    O_S_BT = 'Oᴡɴᴇʀ & Sᴜᴅᴏs'
    CLOSE_BT = 'Cʟᴏsᴇ'
    HELP_HEADER = "㊂ <b><i>Hᴇʟᴘ Gᴜɪᴅᴇ Mᴇɴᴜ!</i></b>\n\n<b>NOTE: <i>Cʟɪᴄᴋ ᴏɴ ᴀɴʏ CMD ᴛᴏ sᴇᴇ ᴍᴏʀᴇ ᴍɪɴᴏʀ ᴅᴇᴛᴀʟɪs.</i></b>"

    
    # async def stats(client, message):
    BOT_STATS = '''<b><i>BOT STATISTICS 🧮</i></b> \n
<b>⏰ Bᴏᴛ Uᴘᴛɪᴍᴇ :</b> {bot_uptime}

╭ <b><i>🎮 Rᴀᴍ ( Mᴇᴍᴏʀʏ )</i></b>
┊ {ram_bar} {ram}%
╰ <b>U :</b> {ram_u} | <b>F :</b> {ram_f} | <b>T :</b> {ram_t}

╭ <b><i>🍃 Sᴡᴀᴘ Mᴇᴍᴏʀʏ</i></b>
┊ {swap_bar} {swap}%
╰ <b>U :</b> {swap_u} | <b>F :</b> {swap_f} | <b>T :</b> {swap_t}

╭ <b><i>💾 Dɪsᴋ </i></b>
┊ {disk_bar} {disk}%
┊ <b>Tᴏᴛᴀʟ Dɪsᴋ Rᴇᴀᴅ :</b> {disk_read}
┊ <b>Tᴏᴛᴀʟ Dɪsᴋ Wʀɪᴛᴇ :</b> {disk_write}
╰ <b>U :</b> {disk_u} | <b>F :</b> {disk_f} | <b>T :</b> {disk_t}
    
    '''
    SYS_STATS = '''<b><i>🧩 OS SYSTEM </i></b>
╭ <b>OS Uᴘᴛɪᴍᴇ :</b> {os_uptime}
┊ <b>OS Vᴇʀsɪᴏɴ :</b> {os_version}
╰ <b>OS Aʀᴄʜ :</b> {os_arch}

<b><i>🛰️ NETWORK STATISTICS </i></b>
╭ <b>🔺 Uᴘʟᴏᴀᴅ Dᴀᴛᴀ:</b> {up_data}
┊ <b>🔻 Dᴏᴡɴʟᴏᴀᴅ Dᴀᴛᴀ:</b> {dl_data}
┊ <b>Pᴋᴛs Sᴇɴᴛ:</b> {pkt_sent}k
┊ <b>Pᴋᴛs Rᴇᴄᴇɪᴠᴇᴅ:</b> {pkt_recv}k
╰ <b>Tᴏᴛᴀʟ I/O Dᴀᴛᴀ:</b> {tl_data}

<i><b>🖥 CPU </b></i>
╭ {cpu_bar} {cpu}%
┊ <b>CPU Fʀᴇǫᴜᴇɴᴄʏ :</b> {cpu_freq}
┊ <b>Sʏsᴛᴇᴍ Aᴠɢ Lᴏᴀᴅ :</b> {sys_load}
┊ <b>P-Cᴏʀᴇ(s) :</b> {p_core} | <b>V-Cᴏʀᴇ(s) :</b> {v_core}
┊ <b>Tᴏᴛᴀʟ Cᴏʀᴇ(s) :</b> {total_core}
╰ <b>Usᴀʙʟᴇ CPU(s) :</b> {cpu_use}
    '''
    REPO_STATS = '''📊 <b><i>REPO STATISTICS :</i></b>
╭ <b>Bᴏᴛ Uᴘᴅᴀᴛᴇᴅ :</b> {last_commit}
┊ <b>Cᴜʀʀᴇɴᴛ Vᴇʀsɪᴏɴ :</b> {bot_version}
┊ <b>Lᴀᴛᴇsᴛ Vᴇʀsɪᴏɴ :</b> {lat_version}
╰ <b>Lᴀsᴛ CʜᴀɴɢᴇLᴏɢ  :</b> {commit_details}

🧬 <b>REMARKS :</b> <code>{remarks}</code>
    '''
    BOT_LIMITS = '''<b><i>BOT LIMITATIONS 🚧</i></b>
╭ <b>🎯 Dɪʀᴇᴄᴛ :</b> <code>{DL} GB</code>
┊ <b>🧲 Tᴏʀʀᴇɴᴛ :</b> <code>{TL} GB</code>
┊ <b>☁️ GDʀɪᴠᴇ :</b> <code>{GL} GB</code>
┊ <b>📺 YT-DLP :</b> <code>{YL} GB</code>
┊ <b>🎥 Pʟᴀʏʟɪsᴛ :</b> <code>{PL} Videos</code>
┊ <b>Ⓜ️ Mᴇɢᴀ :</b> <code>{ML} GB</code>
┊ <b>🎗️ Cʟᴏɴᴇ :</b> <code>{CL} GB</code>
╰ <b>📂 Lᴇᴇᴄʜ :</b> <code>{LL} GB</code>

╭ <b>Tᴏᴋᴇɴ Vᴀʟɪᴅɪᴛʏ :</b> {TV}
┊ <b>Usᴇʀ Tɪᴍᴇ Lɪᴍɪᴛ :</b> {UTI} / ᴛᴀsᴋ
┊ <b>Usᴇʀ Pᴀʀᴀʟʟᴇʟ Tᴀsᴋs :</b> {UT}
╰ <b>Bᴏᴛ Pᴀʀᴀʟʟᴇʟ Tᴀsᴋs :</b> {BT}
    '''
    # ---------------------

    # async def restart(client, message): ---> __main__.py
    RESTARTING = '<i>Rᴇsᴛᴀʀᴛɪɴɢ....♻️</i>'
    # ---------------------

    # async def restart_notification(): ---> __main__.py
    RESTART_SUCCESS = '''<b><i>Rᴇsᴛᴀʀᴛᴇᴅ Sᴜᴄᴄᴇssғᴜʟʟʏ ✅</i></b>
╭ <b>Dᴀᴛᴇ:</b> {date}
┊ <b>Tɪᴍᴇ:</b> {time}
┊ <b>TɪᴍᴇZᴏɴᴇ:</b> {timz}
╰ <b>Vᴇʀsɪᴏɴ:</b> {version}'''
    RESTARTED = '''<b><i>Bᴏᴛ Rᴇsᴛᴀʀᴛᴇᴅ! ✅</i></b>'''
    # ---------------------

    # async def ping(client, message): ---> __main__.py
    PING = '<i>Sᴛᴀʀᴛɪɴɢ Pɪɴɢ...🌋</i>'
    PING_VALUE = '<b>🎯 Pɪɴɢ: </b><code>{value} ms..</code>'
    # ---------------------

    # async def onDownloadStart(self): --> tasks_listener.py
    LINKS_START = """╭ <b><i>Tᴀsᴋ Sᴛᴀʀᴛᴇᴅ</i></b>
┊ <b>Mᴏᴅᴇ:</b> {Mode}
╰ <b>Bʏ:</b> {Tag}\n\n"""
    LINKS_SOURCE = """➲ <b>Sᴏᴜʀᴄᴇ:</b>
┖ <b>Aᴅᴅᴇᴅ Oɴ:</b> {On}
▰▰▰▰▰▰▰▰▰▰▰▰▰
{Source}
▰▰▰▰▰▰▰▰▰▰▰▰▰"""
    
    # async def __msg_to_reply(self): ---> pyrogramEngine.py
    PM_START =            "➲ <b><u>Tᴀsᴋ Sᴛᴀʀᴛᴇᴅ :</u></b>\n┃\n┖ <b>Lɪɴᴋ:</b> <a href='{msg_link}'>Cʟɪᴄᴋ Hᴇʀᴇ</a>"
    L_LOG_START =           "➲ <b><u>Lᴇᴇᴄʜ Sᴛᴀʀᴛᴇᴅ :</u></b>\n┃\n┠ <b>Usᴇʀ :</b> {mention} ( #ID{uid} )\n┖ <b>Sᴏᴜʀᴄᴇ :</b> <a href='{msg_link}'>Cʟɪᴄᴋ Hᴇʀᴇ</a>"

    # async def onUploadComplete(): ---> tasks_listener.py
    NAME =                  '<b><i>{Name}</i></b>\n'
    SIZE =                  '╭ <b>Sɪᴢᴇ: </b><code>{Size}</code>\n'
    ELAPSE =                '┊ <b>Eʟᴀᴘsᴇᴅ: </b><code>{Time}</code>\n'
    MODE =                  '┊ <b>Mᴏᴅᴇ: </b>{Mode}\n'

    # ----- LEECH -------
    L_TOTAL_FILES =         '┊ <b>Tᴏᴛᴀʟ Fɪʟᴇs: </b>{Files}\n'
    L_CORRUPTED_FILES =     '┊ <b>Cᴏʀʀᴜᴘᴛᴇᴅ Fɪʟᴇs: </b>{Corrupt}\n'
    L_CC =                  '╰ <b>Bʏ: </b>{Tag}\n'
    PM_BOT_MSG =            '〄 <i>Fɪʟᴇ(s) ʜᴀᴠᴇ ʙᴇᴇɴ Sᴇɴᴛ ᴀʙᴏᴠᴇ</i>'
    L_BOT_MSG =             '〄 <i>Fɪʟᴇ(s) ʜᴀᴠᴇ ʙᴇᴇɴ Sᴇɴᴛ ᴛᴏ Bᴏᴛ PM (Pʀɪᴠᴀᴛᴇ)</i>'
    L_LL_MSG =              '〄 <i>Fɪʟᴇ(s) ʜᴀᴠᴇ ʙᴇᴇɴ Sᴇɴᴛ. Aᴄᴄᴇss ᴠɪᴀ Lɪɴᴋs...</i>\n'
    
    # ----- MIRROR -------
    M_TYPE =                '╭ <b>Tʏᴘᴇ: </b>{Mimetype}\n'
    M_SUBFOLD =             '┊ <b>SᴜʙFᴏʟᴅᴇʀs: </b>{Folder}\n'
    TOTAL_FILES =           '┊ <b>Fɪʟᴇs: </b>{Files}\n'
    RCPATH =                '┊ <b>Pᴀᴛʜ: </b><code>{RCpath}</code>\n'
    M_CC =                  '╰ <b>Bʏ: </b>{Tag}\n\n'
    M_BOT_MSG =             '➲ <b><i>Lɪɴᴋ(s) ʜᴀᴠᴇ ʙᴇᴇɴ Sᴇɴᴛ ᴛᴏ Bᴏᴛ PM (Pʀɪᴠᴀᴛᴇ)</i></b>'
    # ----- BUTTONS -------
    CLOUD_LINK =      '☁️ Cʟᴏᴜᴅ Lɪɴᴋ'
    SAVE_MSG =        '📨 Sᴀᴠᴇ Mᴇssᴀɢᴇ'
    RCLONE_LINK =     '♻️ RCʟᴏɴᴇ Lɪɴᴋ'
    DDL_LINK =        '📎 {Sᴇʀᴠ} Lɪɴᴋ'
    SOURCE_URL =      '🔐 Sᴏᴜʀᴄᴇ Lɪɴᴋ'
    INDEX_LINK_F =    '🗂 Iɴᴅᴇx Lɪɴᴋ'
    INDEX_LINK_D =    '⚡ Iɴᴅᴇx Lɪɴᴋ'
    VIEW_LINK =       '🌐 Vɪᴇᴡ Lɪɴᴋ'
    CHECK_PM =        '📥 Vɪᴇᴡ ɪɴ Bᴏᴛ PM'
    CHECK_LL =        '🖇 Vɪᴇᴡ ɪɴ Lɪɴᴋs Lᴏɢ'
    MEDIAINFO_LINK =  '📃 MᴇᴅɪᴀIɴғᴏ'
    SCREENSHOTS =     '🖼 SᴄʀᴇᴇɴSʜᴏᴛs'
    # ---------------------

    # def get_readable_message(): ---> bot_utilis.py
    ####--------OVERALL MSG HEADER----------
    STATUS_NAME =       '<b><i>{Name}</i></b>'
    USER =              '\n<b>By:</b> <code>{User}</code>'
    ID =                ' [<code>{Id}</code>]'
    
    #####---------PROGRESSIVE STATUS-------
    STATUS =            '\n╭ <b><a href="{Url}">{Status}</a></b>'
    BAR =               '\n┊ {Bar}'
    PROCESSED =         '\n┊ <code>{Processed}</code>'
    ETA =               '\n┊ <b>ETA:</b> <code>{Eta}</code>'
    SPEED =             '\n┊ <b>Sᴘᴇᴇᴅ:</b> <code>{Speed}</code>'
    ELAPSED =           '\n┊ <b>Pᴀsᴛ:</b> <code>{Elapsed}</code>'
    ENGINE =            '\n┊ <b>Eɴɢɪɴᴇ:</b> {Engine}'
    STA_MODE =          '\n┊ <b>Mᴏᴅᴇ:</b> {Mode}'
    SEEDERS =           '\n┊ <b>Sᴇᴇᴅᴇʀs:</b> {Seeders} | '
    LEECHERS =                                           '<b>Lᴇᴇᴄʜᴇʀs:</b> {Leechers}'

    ####--------SEEDING----------
    SEED_SIZE =      '\n┊ <b>Sɪᴢᴇ: </b><code>{Size}</code>'
    SEED_SPEED =     '\n┊ <b>Sᴘᴇᴇᴅ: </b> <code>{Speed}</code> | '
    UPLOADED =                                     '<b>Uᴘʟᴏᴀᴅᴇᴅ: </b> {Upload}'
    RATIO =          '\n┊ <b>Rᴀᴛɪᴏ: </b> <code>{Ratio}</code> | '
    TIME =                                         '<b>Tɪᴍᴇ: </b> <code>{Time}</code>'
    SEED_ENGINE =    '\n┊ <b>Eɴɢɪɴᴇ:</b> {Engine}'

    ####--------NON-PROGRESSIVE + NON SEEDING----------
    STATUS_SIZE =    '\n┊ <b>Sɪᴢᴇ: </b><code>{Size}</code>'
    NON_ENGINE =     '\n┊ <b>Eɴɢɪɴᴇ:</b> {Engine}'

    ####--------OVERALL MSG FOOTER----------
    BTSEL =          '\n┊ <b>Sᴇʟᴇᴄᴛ:</b> {Btsel}'
    CANCEL =         '\n╰ {Cancel}\n\n'

    ####------FOOTER--------
    FOOTER = '〄 <b><u>Sʏsᴛᴇᴍ Sᴛᴀᴛɪsᴛɪᴄs...</u></b>\n'
    TASKS =  '╰ <b>Tᴀsᴋs:</b> {Tasks}\n'
    BOT_TASKS = '╰ <b>Tᴀsᴋs:</b> {Tasks}/{Ttask} | <b>⚰️ AVL:</b> {Free}\n'
    Cpu = '╭ <b>Cᴘᴜ:</b> <code>{cpu}%</code> | '
    FREE =                      '<b>F:</b> <code>{free}</code>'
    Ram = '\n┊ <b>Rᴀᴍ:</b> <code>{ram}%</code> | '
    uptime =                     '<b>Uᴘ:</b> <code>{uptime}</code>'
    DL = '\n┊ <b>🔻 Total DL:</b> <code>{DL}/s</code>'
    UL = '\n╰ <b>🔺 Total UL:</b> <code>{UL}/s</code>'

    ###--------BUTTONS-------
    PREVIOUS = '⫷'
    REFRESH = '📑 Pᴀɢᴇ: {Page}'
    NEXT = '⫸'
    # ---------------------

    #STOP_DUPLICATE_MSG: ---> clone.py, aria2_listener.py, task_manager.py
    STOP_DUPLICATE = 'Fɪʟᴇ/Fᴏʟᴅᴇʀ ɪs ᴀʟʀᴇᴀᴅʏ ᴀᴠᴀɪʟᴀʙʟᴇ ɪɴ Dʀɪᴠᴇ.\nHᴇʀᴇ ᴀʀᴇ {content} ʟɪsᴛ ʀᴇsᴜʟᴛs:'
    # ---------------------

    # async def countNode(_, message): ----> gd_count.py
    COUNT_MSG = '<b>Cᴏᴜɴᴛɪɴɢ:</b> <code>{LINK}</code>'
    COUNT_NAME = '<b><i>{COUNT_NAME}</i></b>\n┃\n'
    COUNT_SIZE = '╭ <b>Sɪᴢᴇ: </b>{COUNT_SIZE}\n'
    COUNT_TYPE = '┊ <b>Tʏᴘᴇ: </b>{COUNT_TYPE}\n'
    COUNT_SUB =  '┊ <b>SᴜʙFᴏʟᴅᴇʀs: </b>{COUNT_SUB}\n'
    COUNT_FILE = '┊ <b>Fɪʟᴇs: </b>{COUNT_FILE}\n'
    COUNT_CC =   '╰ <b>Bʏ: </b>{COUNT_CC}\n'
    # ---------------------

    # LIST ---> gd_list.py
    LIST_SEARCHING = '<b>Sᴇᴀʀᴄʜɪɴɢ ғᴏʀ <i>{NAME}</i></b>'
    LIST_FOUND = '<b>Fᴏᴜɴᴅ {NO} ʀᴇsᴜʟᴛ ғᴏʀ <i>{NAME}</i></b>'
    LIST_NOT_FOUND = 'Nᴏ ʀᴇsᴜʟᴛ ғᴏᴜɴᴅ ғᴏʀ <i>{NAME}</i>'
    # ---------------------

    # async def mirror_status(_, message): ----> status.py
    NO_ACTIVE_DL = '''Nᴏ Aᴄᴛɪᴠᴇ Dᴏᴡɴʟᴏᴀᴅs ! 🗑️
    
〄 <u><b>Bᴏᴛ Sᴛᴀᴛs.......</b></u>
╭ <b>🖥️ Cᴘᴜ:</b> <code>{cpu}%</code>
┊ <b>🎮 Rᴀᴍ:</b> <code>{ram}%</code>
┊ <b>💿 Free:</b> <code>{free}</code>
╰ <b>🚀 Uᴘᴛɪᴍᴇ:</b> <code>{uptime}</code>
    '''
    # ---------------------

    # USER Setting --> user_setting.py 
    # USER Setting --> user_setting.py 
    USER_SETTING = '''👽 <b><u>Usᴇʀ Sᴇᴛᴛɪɴɢs :</u></b>
        
╭ <b>👤 Nᴀᴍᴇ :</b> {NAME}
┊ <b>🔖 Usᴇʀɴᴀᴍᴇ :</b> {USERNAME}
┊ <b>🆔 ID :</b> <code>{ID}</code>
┊ <b>🔮 DC :</b> <code>{DC}</code>
╰ <b>🗣️ Lᴀɴɢᴜᴀɢᴇ :</b> <code>{LANG}</code>

🗳️ <u><b>Aᴠᴀɪʟᴀʙʟᴇ Aʀɢs:</b></u>
• <b>-s</b> or <b>-set</b>: Sᴇᴛ Dɪʀᴇᴄᴛʟʏ ᴠɪᴀ Aʀɢ'''

    UNIVERSAL = '''🌐 <b><u>Uɴɪᴠᴇʀsᴀʟ Sᴇᴛᴛɪɴɢs : {NAME}</u></b>

╭ <b>  YT-DLP Oᴘᴛɪᴏɴs :</b> <b><code>{YT}</code></b>
┊ <b> Dᴀɪʟʏ Tᴀsᴋs :</b> <code>{DT}</code> per day
┊ <b> Lᴀsᴛ Bᴏᴛ Usᴇᴅ :</b> <code>{LAST_USED}</code>
┊ <b> Usᴇʀ Sᴇssɪᴏɴ :</b> <code>{USESS}</code>
┊ <b> MᴇᴅɪᴀIɴғᴏ Mᴏᴅᴇ :</b> <code>{MEDIAINFO}</code>
┊ <b> Sᴀᴠᴇ Mᴏᴅᴇ :</b> <code>{SAVE_MODE}</code>
╰ <b> Usᴇʀ Bᴏᴛ PM :</b> <code>{BOT_PM}</code>'''

    MIRROR = '''🏅 <b><u>Mɪʀʀᴏʀ/Cʟᴏɴᴇ Sᴇᴛᴛɪɴɢs : {NAME}</u></b>

╭ <b> RCʟᴏɴᴇ Cᴏɴғɪɢ :</b> <i>{RCLONE}</i>
┊ <b> Mɪʀʀᴏʀ Pʀᴇғɪx :</b> <code>{MPREFIX}</code>
┊ <b> Mɪʀʀᴏʀ Sᴜғғɪx :</b> <code>{MSUFFIX}</code>
┊ <b> Mɪʀʀᴏʀ Rᴇᴍɴᴀᴍᴇ :</b> <code>{MREMNAME}</code>
┊ <b> DDL Sᴇʀᴠᴇʀ(s) :</b> <i>{DDL_SERVER}</i>
┊ <b> Usᴇʀ TD Mᴏᴅᴇ :</b> <i>{TMODE}</i>
┊ <b> Tᴏᴛᴀʟ Usᴇʀ TD(s) :</b> <i>{USERTD}</i>
╰ <b> Dᴀɪʟʏ Mɪʀʀᴏʀ :</b> <code>{DM}</code> per day'''

    LEECH = '''🧲 <b><u>Lᴇᴇᴄʜ Sᴇᴛᴛɪɴɢs ғᴏʀ {NAME}</u></b>

╭ <b> Dᴀɪʟʏ Lᴇᴇᴄʜ : </b><code>{DL}</code> per day
┊ <b> Lᴇᴇᴄʜ Tʏᴘᴇ :</b> <i>{LTYPE}</i>
┊ <b> Cᴜsᴛᴏᴍ Tʜᴜᴍʙɴᴀɪʟ :</b> <i>{THUMB}</i>
┊ <b> Lᴇᴇᴄʜ Sᴘʟɪᴛ Sɪᴢᴇ :</b> <code>{SPLIT_SIZE}</code>
┊ <b> Eǫᴜᴀʟ Sᴘʟɪᴛs :</b> <i>{EQUAL_SPLIT}</i>
┊ <b> Mᴇᴅɪᴀ Gʀᴏᴜᴘ :</b> <i>{MEDIA_GROUP}</i>
┊ <b> Lᴇᴇᴄʜ Cᴀᴘᴛɪᴏɴ  :</b> <code>{LCAPTION}</code>
┊ <b> Lᴇᴇᴄʜ Pʀᴇғɪx :</b> <code>{LPREFIX}</code>
┊ <b> Lᴇᴇᴄʜ Sᴜғғɪx :</b> <code>{LSUFFIX}</code>
┊ <b> Lᴇᴇᴄʜ Dᴜᴍᴘs :</b> <code>{LDUMP}</code>
╰ <b> Lᴇᴇᴄʜ Rᴇᴍɴᴀᴍᴇ :</b> <code>{LREMNAME}</code>'''
