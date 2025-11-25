#!/usr/bin/env python3
from bot.helper.telegram_helper.bot_commands import BotCommands

YT_HELP_MESSAGE = [
    """<i>Send links/files along with a command or reply to a command to mirror or leech yt-dlp supported sites to Telegram, Google Drive, or DDL servers using RClone or yt-dlp.</i>

🔹 <b><u>Available Arguments</u></b>:

• <b>-n, -name, or |</b>: 📝 Rename the file.
• <b>-z or -zip</b>: 🗜️ Zip files or links.
• <b>-up or -upload</b>: 📤 Upload to your Drive, RClone, or DDL server.
• <b>-b or -bulk</b>: 📚 Download bulk links.
• <b>-i</b>: 🔗 Download multiple links by replying.
• <b>-m, -sd, or -samedir</b>: 📂 Download multiple links into the same upload directory.
• <b>-opt or -options</b>: ⚙️ Add custom yt-dlp options to the link.
• <b>-s or -select</b>: ✅ Select files from yt-dlp links, even if a quality is specified.
• <b>-rcf</b>: 🚩 Add additional RClone flags.
• <b>-id</b>: 🆔 Specify a GDrive folder ID or link.
• <b>-index</b>: 📑 Provide an index URL for GDrive.
• <b>-c or -category</b>: 🏷️ Select a GDrive category for uploading (case insensitive).
• <b>-ud or -dump</b>: 🗑️ Select a dump category for uploading (name, chat_id, or username).
• <b>-ss or -screenshots</b>: 📸 Generate screenshots for leeched files.
• <b>-t or -thumb</b>: 🖼️ Add a custom thumbnail to a specific leech.
""",
    """
🔹 <b><i>Usage Examples</i></b>:

▸ <b>Command with link</b>:
<code>/cmd</code> [link] -s -n [new name] -opt x:y|x1:y1

▸ <b>Replying to a link</b>:
<code>/cmd</code> -n [new name] -z [password] -opt x:y|x1:y1

▸ <b>Rename</b>: -n, -name, or |
<code>/cmd</code> [link] -n [new name]
<b>Note</b>: Do not include the file extension in the name.

▸ <b>Screenshots</b>: -ss or -screenshots
<code>/cmd</code> [link] -ss [number]
Generates a specified number of screenshots for each video file.

▸ <b>Custom Thumbnail</b>: -t or -thumb
<code>/cmd</code> [link] -t [tg_link|dl_link]
Provide a direct image URL or a Telegram link to an image.

▸ <b>Select Quality</b>: -s or -select
Use this to manually select video quality if a default is set in your yt-dlp options.
<code>/cmd</code> [link] -s

▸ <b>Zip</b>: -z or -zip
<code>/cmd</code> [link] -z (creates a password-free zip)
<code>/cmd</code> [link] -z [password] (creates a password-protected zip)

▸ <b>Custom Options</b>: -opt or -options
<code>/cmd</code> [link] -opt playliststart:^10|fragment_retries:^inf
<b>Note</b>: Use `^` before numbers for numeric values. Refer to the <a href='https://github.com/yt-dlp/yt-dlp/blob/master/yt_dlp/YoutubeDL.py#L184'>yt-dlp documentation</a> for all options.

▸ <b>Multi-Link</b>: -i
Reply to the first link and specify the number of links to process.
<code>/cmd</code> -i 10

▸ <b>Same Directory</b>: -m, -sd, or -samedir
<code>/cmd</code> -i 10 -m [folder name]

▸ <b>Custom Drive/Category/Dump</b>:
- <b>-id</b>: <code>/cmd</code> -id [drive_id|drive_link]
- <b>-c</b>: <code>/cmd</code> -c [category_name]
- <b>-ud</b>: <code>/cmd</code> -ud [dump_name|@username|chat_id|all]

▸ <b>Custom Upload Destination</b>: -up or -upload
<code>/cmd</code> [link] -up [rcl|ddl|gd]
You can also specify a path directly: <code>-up remote:path/to/dir</code>
To use a custom rclone config, prefix with `mrcc:`: <code>-up mrcc:main:dump</code>

▸ <b>RClone Flags</b>: -rcf
<code>/cmd</code> [link] -up [path] -rcf --buffer-size:8M|--drive-starred-only
Refer to the <a href='https://rclone.org/flags/'>Rclone documentation</a> for all flags.

▸ <b>Bulk Download</b>: -b or -bulk
Reply to a message or text file with links. Each link can have its own options.
<b>Example</b>:
link1 -n [new_name] -up remote1:path1
link2 -z -n [new_name]
- To process a specific range, use <code>-b start:end</code>.
""",
]

MIRROR_HELP_MESSAGE = [
    """<i>Send links, files, or rclone paths to mirror or leech content to Telegram, Google Drive, or DDL servers using RClone, Aria2, or qBittorrent.</i>

🔹 <b><u>Available Arguments</u></b>:

• <b>-n, -name, or |</b>: 📝 Rename the file.
• <b>-z or -zip</b>: 🗜️ Zip files or links.
• <b>-e, -extract, -uz, or -unzip</b>: 📂 Extract files from an archive.
• <b>-up or -upload</b>: 📤 Upload to your Drive, RClone, or DDL server.
• <b>-b or -bulk</b>: 📚 Download bulk links.
• <b>-i</b>: 🔗 Download multiple links by replying.
• <b>-m, -sd, or -samedir</b>: 📂 Download multiple links into the same upload directory.
• <b>-d or -seed</b>: 🌱 Seed torrents.
• <b>-s or -select</b>: ✅ Select files from a torrent.
• <b>-u or -user</b>: 👤 Provide a username for authentication.
• <b>-p or -pass</b>: 🔑 Provide a password for authentication.
• <b>-j or -join</b>: 🔗 Join multiple files.
• <b>-rcf</b>: 🚩 Add additional RClone flags.
• <b>-id</b>: 🆔 Specify a GDrive folder ID or link.
• <b>-index</b>: 📑 Provide an index URL for GDrive.
• <b>-c or -category</b>: 🏷️ Select a GDrive category for uploading.
• <b>-ud or -dump</b>: 🗑️ Select a dump category for uploading.
• <b>-ss or -screenshots</b>: 📸 Generate screenshots for leeched files.
• <b>-t or -thumb</b>: 🖼️ Add a custom thumbnail to a specific leech.
""",
    """
🔹 <b><i>Usage Examples</i></b>:

▸ <b>With link in command</b>:
<code>/cmd</code> [link] -n [new name]

▸ <b>Replying to a link/file</b>:
<code>/cmd</code> -n [new name] -z -e -up [upload_destination]

▸ <b>Rename</b>: -n, -name, or |
<code>/cmd</code> [link] -n [new name]
<b>Note</b>: Does not work with torrents.

▸ <b>Authentication</b>: -u, -p or -user, -pass
<code>/cmd</code> [link] -u [username] -p [password]

▸ <b>Custom Headers</b>: -h or -headers
<code>/cmd</code> [link] -h key:value key1:value1

▸ <b>Screenshots & Thumbnail</b>:
- <b>-ss</b>: <code>/cmd</code> [link] -ss [number]
- <b>-t</b>: <code>/cmd</code> [link] -t [tg_link|dl_link]

▸ <b>Extract & Zip</b>:
<code>/cmd</code> [link] -e [password] (extracts a password-protected archive)
<code>/cmd</code> [link] -z [password] (zips with a password)
<code>/cmd</code> [link] -e -z (extracts, then zips the result)
<b>Note</b>: Extraction always occurs before zipping.

▸ <b>Torrent Selection & Seeding</b>:
- <b>Select</b>: <code>/cmd</code> [link] -s
- <b>Seed</b>: <code>/cmd</code> [link] -d [ratio]:[time_in_minutes]
  (e.g., <code>-d 0.7:10</code> for a 0.7 ratio for 10 minutes)

▸ <b>Multi-Link & Same Directory</b>:
- <b>Multi-Link</b>: <code>/cmd</code> -i [number_of_links]
- <b>Same Directory</b>: <code>/cmd</code> -i [number] -m [folder_name]

▸ <b>Custom Drive/Category/Dump</b>:
- <b>-id</b>: <code>/cmd</code> -id [drive_id|drive_link]
- <b>-c</b>: <code>/cmd</code> -c [category_name]
- <b>-ud</b>: <code>/cmd</code> -ud [dump_name|@username|chat_id|all]

▸ <b>Custom Upload & RClone</b>:
- <b>Destination</b>: <code>/cmd</code> [link] -up [rcl|ddl|gd]
- <b>Path</b>: <code>-up remote:path/to/dir</code> or <code>-up mrcc:main:dump</code>
- <b>Flags</b>: <code>-rcf --buffer-size:8M</code>

▸ <b>Bulk Download</b>: -b or -bulk
Reply to a message/file with links. Each line can have different options.
<b>Example</b>:
link1 -n [name1] -up remote1:path1
link2 -z -up remote2:path2
- Use <code>-b start:end</code> to process a range.

▸ <b>Join Files</b>: -j or -join
Joins split files. Primarily used with <code>-m</code>.
<code>/cmd</code> -i 3 -j -m [folder_name]

▸ <b>RClone & TG Links</b>:
Treat rclone paths and Telegram links just like direct links.
- <b>RClone</b>: <code>/cmd</code> main:dump/file.iso
- <b>TG Link</b>: <code>/cmd</code> https://t.me/channel/123
""",
]

RSS_HELP_MESSAGE = """
🔹 <b>Feed URL Format</b>:
Title1 https://rss-url.com
Title2 https://rss-url.com -c cmd -inf xx -exf xx
Title3 https://rss-url.com -c cmd -d ratio:time -z password

🔹 <b>Argument Details</b>:
• <b>-c</b>: Command and arguments to execute.
• <b>-inf</b>: Keywords to include (if present, the link will be downloaded).
• <b>-exf</b>: Keywords to exclude (if present, the link will be skipped).

<b>Example Filter</b>:
<code>Title https://rss-url.com inf: 1080|mkv or 720|mkv exf: web|xxx</code>
This filter will download links containing (1080 and mkv) or (720 and mkv), but will skip any that contain "web" or "xxx".

🔹 <b>Filter Logic</b>:
• <b>`|`</b> = AND
• <b>`or`</b> = OR
• Use spaces to avoid partial matches (e.g., `1080` vs. ` 1080 `).
"""

CLONE_HELP_MESSAGE = [
    """<i>Send a GDrive, Gdtot, Filepress, or RClone path to clone content.</i>

🔹 <b><u>Available Arguments</u></b>:

• <b>-up or -upload</b>: 📤 Upload to your Drive, RClone, or DDL server.
• <b>-i</b>: 🔗 Clone multiple links by replying.
• <b>-rcf</b>: 🚩 Add additional RClone flags.
• <b>-id</b>: 🆔 Specify a GDrive folder ID or link.
• <b>-index</b>: 📑 Provide an index URL for GDrive.
• <b>-c or -category</b>: 🏷️ Select a GDrive category for uploading.
""",
    """
🔹 <b><i>Usage Examples</i></b>:

▸ <b>GDrive Link</b>:
<code>/cmd</code> [gdrive_link]

▸ <b>Multi-Link</b> (reply to the first link):
<code>/cmd</code> -i 10

▸ <b>RClone Path with Flags</b>:
<code>/cmd</code> [rclone_path] -up [destination_path] -rcf key:value

▸ <b>Custom Drive/Category</b>:
- <b>-id</b>: <code>/cmd</code> -id [drive_id|drive_link]
- <b>-c</b>: <code>/cmd</code> -c [category_name]

<b>Notes</b>:
• If <code>-up</code> is not specified, the default RCLONE_PATH will be used.
• For multi-uploads with custom destinations, specify the destination for each link and then reply with <code>/cmd -i [number]</code>.
""",
]

CATEGORY_HELP_MESSAGE = """
Reply to an active download command or provide a GID to change the upload category.

🔹 <b>Upload to a Custom Drive</b>:
<code>/{cmd}</code> -id [drive_folder_link|drive_id] -index [index_url] [gid]
"""

help_string = [
    f"""✨ <b>Basic Commands</b>

• <b>Mirror</b>:
  » <code>/{BotCommands.MirrorCommand[0]}</code> or <code>/{BotCommands.MirrorCommand[1]}</code>: Mirror files/links to the cloud.
  » <code>/{BotCommands.CategorySelect}</code>: Select an upload category.

• <b>qBittorrent</b>:
  » <code>/{BotCommands.QbMirrorCommand[0]}</code> or <code>/{BotCommands.QbMirrorCommand[1]}</code>: Mirror torrents.
  » <code>/{BotCommands.BtSelectCommand}</code>: Select files from a torrent.

• <b>yt-dlp</b>:
  » <code>/{BotCommands.YtdlCommand[0]}</code> or <code>/{BotCommands.YtdlCommand[1]}</code>: Mirror yt-dlp supported links.

• <b>Leech</b>:
  » <code>/{BotCommands.LeechCommand[0]}</code> or <code>/{BotCommands.LeechCommand[1]}</code>: Leech files to Telegram.
  » <code>/{BotCommands.QbLeechCommand[0]}</code> or <code>/{BotCommands.QbLeechCommand[1]}</code>: Leech torrents to Telegram.
  » <code>/{BotCommands.YtdlLeechCommand[0]}</code> or <code>/{BotCommands.YtdlLeechCommand[1]}</code>: Leech yt-dlp links to Telegram.

• <b>Google Drive</b>:
  » <code>/{BotCommands.CloneCommand[0]}</code>: Clone files/folders.
  » <code>/{BotCommands.CountCommand}</code>: Count files/folders.
  » <code>/{BotCommands.DeleteCommand}</code>: Delete files/folders (Sudo/Owner).

• <b>Cancel Tasks</b>:
  » <code>/{BotCommands.CancelMirror}</code>: Cancel a single task.
""",
    f"""👤 <b>User Commands</b>

• <b>Settings</b>:
  » <code>/{BotCommands.UserSetCommand[0]}</code> or <code>/{BotCommands.UserSetCommand[1]}</code>: Manage your user settings.

• <b>Authentication</b>:
  » <code>/login</code>: Log in to the bot permanently.

• <b>Bot Status</b>:
  » <code>/{BotCommands.StatusCommand[0]}</code> or <code>/{BotCommands.StatusCommand[1]}</code>: View status of all tasks.
  » <code>/{BotCommands.StatsCommand[0]}</code> or <code>/{BotCommands.StatsCommand[1]}</code>: View bot and server stats.
  » <code>/{BotCommands.PingCommand[0]}</code> or <code>/{BotCommands.PingCommand[1]}</code>: Check bot's response time.

• <b>RSS</b>:
  » <code>/{BotCommands.RssCommand}</code>: Manage RSS feeds.
""",
    f"""👑 <b>Admin & Sudo Commands</b>

• <b>Bot Settings</b>:
  » <code>/{BotCommands.BotSetCommand[0]}</code> or <code>/{BotCommands.BotSetCommand[1]}</code>: Manage bot-wide settings.
  » <code>/{BotCommands.UsersCommand}</code>: View user stats.

• <b>Authentication</b>:
  » <code>/{BotCommands.AuthorizeCommand[0]}</code>: Authorize a user or chat.
  » <code>/{BotCommands.UnAuthorizeCommand[0]}</code>: Unauthorize a user or chat.
  » <code>/{BotCommands.AddSudoCommand}</code>: Add a sudo user.
  » <code>/{BotCommands.RmSudoCommand}</code>: Remove a sudo user.
  » <code>/{BotCommands.AddBlackListCommand[0]}</code>: Blacklist a user.
  » <code>/{BotCommands.RmBlackListCommand[0]}</code>: Unblacklist a user.

• <b>Broadcast</b>:
  » <code>/{BotCommands.BroadcastCommand[0]}</code>: Send a message to all users.

• <b>Google Drive</b>:
  » <code>/{BotCommands.GDCleanCommand[0]}</code>: Clean a GDrive folder.

• <b>Cancel Tasks</b>:
  » <code>/{BotCommands.CancelAllCommand[0]}</code>: Cancel all tasks.

• <b>Maintenance</b>:
  » <code>/{BotCommands.RestartCommand[0]}</code>: Restart and update the bot.
  » <code>/{BotCommands.LogCommand}</code>: View bot logs.

• <b>Execution</b>:
  » <code>/{BotCommands.ShellCommand}</code>: Execute shell commands.
  » <code>/{BotCommands.EvalCommand}</code>: Evaluate Python code.
  » <code>/{BotCommands.ExecCommand}</code>: Execute commands.
  » <code>/{BotCommands.ClearLocalsCommand}</code>: Clear local variables.
  » <code>/exportsession</code>: Export a user session string.

• <b>Images</b>:
  » <code>/{BotCommands.AddImageCommand}</code>: Add an image.
  » <code>/{BotCommands.ImagesCommand}</code>: View stored images.
""",
    f"""⚙️ <b>Miscellaneous Commands</b>

• <b>Utilities</b>:
  » <code>/{BotCommands.SpeedCommand[0]}</code> or <code>/{BotCommands.SpeedCommand[1]}</code>: Perform a speed test.
  » <code>/{BotCommands.MediaInfoCommand[0]}</code> or <code>/{BotCommands.MediaInfoCommand[1]}</code>: Get media information.

• <b>Search</b>:
  » <code>/{BotCommands.ListCommand}</code>: Search Google Drive.
  » <code>/{BotCommands.SearchCommand}</code>: Search for torrents.

• <b>Media Databases</b>:
  » <code>/{BotCommands.IMDBCommand}</code>: Search IMDB.
  » <code>/{BotCommands.AniListCommand}</code>: Search AniList.
  » <code>/{BotCommands.MyDramaListCommand}</code>: Search MyDramaList.
""",
]

PASSWORD_ERROR_MESSAGE = """
<b>🔒 This link requires a password!</b>
- Add <code>::</code> after the link, followed by the password.
<b>Example:</b> <code>{}::my_password</code>
<b>Note</b>: Do not add spaces around <code>::</code>.
"""

default_desp = {
    "AS_DOCUMENT": "📄 **As Document**: Upload files as documents instead of media.",
    "ANIME_TEMPLATE": "🎌 **Anime Template**: Customize the template for AniList search results.",
    "AUTHORIZED_CHATS": "✅ **Authorized Chats**: Allow specific users or chats to use the bot (user IDs and chat IDs, space-separated).",
    "AUTO_DELETE_MESSAGE_DURATION": "⏱️ **Auto-Delete Duration**: Time in seconds to auto-delete messages. Set to -1 to disable.",
    "BASE_URL": "🌐 **Base URL**: The public URL of your bot (e.g., http://1.2.3.4:80).",
    "BASE_URL_PORT": "🚪 **Base URL Port**: The port for the base URL (default: 80).",
    "BLACKLIST_USERS": "🚫 **Blacklist Users**: Prevent specific users from using the bot (user IDs, space-separated).",
    "BOT_MAX_TASKS": "🔢 **Bot Max Tasks**: The maximum number of parallel tasks for the bot.",
    "STORAGE_THRESHOLD": "💾 **Storage Threshold**: Cancel downloads if free space falls below this value (in GB).",
    "LEECH_LIMIT": "📥 **Leech Limit**: The maximum size for a leech (in GB).",
    "CLONE_LIMIT": "♻️ **Clone Limit**: The maximum size for a GDrive clone (in GB).",
    "MEGA_LIMIT": "☁️ **Mega Limit**: The maximum size for a Mega download (in GB).",
    "TORRENT_LIMIT": "🧲 **Torrent Limit**: The maximum size for a torrent download (in GB).",
    "DIRECT_LIMIT": "🔗 **Direct Limit**: The maximum size for a direct download (in GB).",
    "YTDLP_LIMIT": "📺 **YT-DLP Limit**: The maximum size for a yt-dlp download (in GB).",
    "PLAYLIST_LIMIT": "📋 **Playlist Limit**: The maximum number of items to download from a playlist.",
    "IMAGES": "🖼️ **Images**: A list of Telegraph image links to be used in the bot, separated by spaces.",
    "IMG_SEARCH": "🔍 **Image Search**: Keywords to search for images (e.g., anime, nature).",
    "IMG_PAGE": "📄 **Image Page**: The page number for image searches (default: 1).",
    "IMDB_TEMPLATE": "🎬 **IMDB Template**: Customize the template for IMDB search results.",
    "AUTHOR_NAME": "✍️ **Author Name**: The author name to display on Telegraph pages.",
    "AUTHOR_URL": "🔗 **Author URL**: The author URL to display on Telegraph pages.",
    "COVER_IMAGE": "🖼️ **Cover Image**: A cover image for Telegraph pages.",
    "TITLE_NAME": "📝 **Title Name**: The title for Telegraph pages created with the /list command.",
    "GD_INFO": "ℹ️ **GDrive Info**: A description to be added to files uploaded to GDrive.",
    "DELETE_LINKS": "🗑️ **Delete Links**: Delete trigger links and files after a task starts.",
    "EXCEP_CHATS": "🛡️ **Exception Chats**: Chats to exclude from logging.",
    "SAFE_MODE": "🔒 **Safe Mode**: Hide task names and source links for privacy.",
    "SOURCE_LINK": "🔗 **Source Link**: Add a source link button to mirrored files.",
    "SHOW_EXTRA_CMDS": "➕ **Show Extra Commands**: Enable extra commands like /unzipxxx.",
    "BOT_THEME": "🎨 **Bot Theme**: Customize the bot's appearance.",
    "USER_MAX_TASKS": "🔢 **User Max Tasks**: The maximum number of parallel tasks per user.",
    "DAILY_TASK_LIMIT": "📅 **Daily Task Limit**: The maximum number of tasks a user can execute per day.",
    "DISABLE_DRIVE_LINK": "🚫 **Disable Drive Link**: Disable the GDrive link button.",
    "DAILY_MIRROR_LIMIT": "📅 **Daily Mirror Limit**: The maximum total size a user can mirror per day (in GB).",
    "GDRIVE_LIMIT": "📥 **GDrive Limit**: The maximum size for GDrive links (in GB).",
    "DAILY_LEECH_LIMIT": "📅 **Daily Leech Limit**: The maximum total size a user can leech per day (in GB).",
    "FSUB_IDS": "📢 **Force Subscribe IDs**: Force users to join specific channels/chats before using the bot.",
    "BOT_PM": "🤖 **Bot PM**: Send files/links to the bot's private messages.",
    "BOT_TOKEN": "🤖 **Bot Token**: Your Telegram bot token from @BotFather.",
    "CMD_SUFFIX": "🔡 **Command Suffix**: A suffix to add to all bot commands.",
    "DATABASE_URL": "🗄️ **Database URL**: Your MongoDB connection string.",
    "DEFAULT_UPLOAD": "📤 **Default Upload**: The default upload destination (rc, gd, or ddl).",
    "DOWNLOAD_DIR": "📂 **Download Directory**: The local path where downloads are stored.",
    "MDL_TEMPLATE": "🎭 **MyDramaList Template**: Customize the template for MyDramaList search results.",
    "CLEAN_LOG_MSG": "🧹 **Clean Log Messages**: Clean leech logs and task start messages in the bot's PM.",
    "LEECH_LOG_ID": "📝 **Leech Log ID**: The chat ID where leeched files are uploaded.",
    "MIRROR_LOG_ID": "📝 **Mirror Log ID**: The chat ID where mirror notifications are sent.",
    "EQUAL_SPLITS": "🟰 **Equal Splits**: Split files into equal parts.",
    "EXTENSION_FILTER": "🚫 **Extension Filter**: File extensions to exclude from uploads/clones.",
    "GDRIVE_ID": "🆔 **GDrive ID**: The default Google Drive folder/TeamDrive ID for uploads.",
    "INCOMPLETE_TASK_NOTIFIER": "🔔 **Incomplete Task Notifier**: Notify about incomplete tasks on restart.",
    "INDEX_URL": "📑 **Index URL**: Your Google Drive Index URL.",
    "IS_TEAM_DRIVE": "👥 **Is Team Drive**: Set to True if GDRIVE_ID is a Team Drive.",
    "SHOW_MEDIAINFO": "ℹ️ **Show MediaInfo**: Add a button to show media information for leeched files.",
    "SCREENSHOTS_MODE": "📸 **Screenshots Mode**: Enable or disable screenshot generation.",
    "CAP_FONT": "🅰️ **Caption Font**: The font style for leech captions (b, i, u, s, code, spoiler).",
    "LEECH_FILENAME_PREFIX": "🔡 **Leech Filename Prefix**: A prefix for leeched filenames.",
    "LEECH_FILENAME_SUFFIX": "🔡 **Leech Filename Suffix**: A suffix for leeched filenames.",
    "LEECH_FILENAME_CAPTION": "📝 **Leech Filename Caption**: A custom caption for leeched files.",
    "LEECH_FILENAME_REMNAME": "🗑️ **Leech Filename Remove Name**: Words to remove from leeched filenames.",
    "LOGIN_PASS": "🔑 **Login Password**: A permanent password to bypass the token system.",
    "TOKEN_TIMEOUT": "⏳ **Token Timeout**: The timeout for temporary tokens in seconds.",
    "DEBRID_LINK_API": "🔗 **Debrid-Link API**: Your debrid-link.com API key.",
    "REAL_DEBRID_API": "🔗 **Real-Debrid API**: Your real-debrid.com API key.",
    "LEECH_SPLIT_SIZE": "✂️ **Leech Split Size**: The size for splitting leeched files in bytes.",
    "MEDIA_GROUP": "🎞️ **Media Group**: Group split files into a media group.",
    "MEGA_EMAIL": "📧 **Mega Email**: Your mega.nz email address.",
    "MEGA_PASSWORD": "🔑 **Mega Password**: Your mega.nz password.",
    "OWNER_ID": "👑 **Owner ID**: Your Telegram user ID.",
    "QUEUE_ALL": "🔢 **Queue All**: The total number of parallel downloads and uploads.",
    "QUEUE_DOWNLOAD": "📥 **Queue Download**: The number of parallel downloads.",
    "QUEUE_UPLOAD": "📤 **Queue Upload**: The number of parallel uploads.",
    "RCLONE_FLAGS": "🚩 **RClone Flags**: Default RClone flags.",
    "RCLONE_PATH": "📂 **RClone Path**: The default RClone upload path.",
    "RCLONE_SERVE_URL": "🌐 **RClone Serve URL**: The public URL for the RClone serve instance.",
    "RCLONE_SERVE_USER": "👤 **RClone Serve User**: The username for RClone serve.",
    "RCLONE_SERVE_PASS": "🔑 **RClone Serve Password**: The password for RClone serve.",
    "RCLONE_SERVE_PORT": "🚪 **RClone Serve Port**: The port for the RClone serve instance (default: 8080).",
    "RSS_CHAT_ID": "📰 **RSS Chat ID**: The chat ID where RSS updates are sent.",
    "RSS_DELAY": "⏱️ **RSS Delay**: The RSS refresh interval in seconds.",
    "SEARCH_API_LINK": "🔍 **Search API Link**: The URL of your torrent search API.",
    "SEARCH_LIMIT": "🔢 **Search Limit**: The number of search results per site.",
    "SEARCH_PLUGINS": "🔌 **Search Plugins**: A list of qBittorrent search plugins.",
    "STATUS_LIMIT": "🔢 **Status Limit**: The number of tasks to display per page in the status message.",
    "STATUS_UPDATE_INTERVAL": "⏱️ **Status Update Interval**: The interval for updating the status message in seconds.",
    "STOP_DUPLICATE": "🚫 **Stop Duplicate**: Prevent downloading duplicate files/folders.",
    "SUDO_USERS": "👑 **Sudo Users**: A list of user IDs with sudo privileges.",
    "TELEGRAM_API": "🆔 **Telegram API ID**: Your my.telegram.org API ID.",
    "TELEGRAM_HASH": "🔑 **Telegram Hash**: Your my.telegram.org API hash.",
    "TIMEZONE": "🌍 **Timezone**: Your preferred timezone.",
    "TORRENT_TIMEOUT": "⏳ **Torrent Timeout**: The timeout for dead torrents in seconds.",
    "UPSTREAM_REPO": "📦 **Upstream Repo**: The GitHub repository to update from.",
    "UPSTREAM_BRANCH": "🌿 **Upstream Branch**: The branch to update from (default: master).",
    "UPGRADE_PACKAGES": "🔄 **Upgrade Packages**: Upgrade Python packages on restart.",
    "SAVE_MSG": "💾 **Save Message**: Add a button to save messages.",
    "SET_COMMANDS": "🤖 **Set Commands**: Automatically set bot commands on startup.",
    "JIODRIVE_TOKEN": "🔑 **Jiodrive Token**: Your jiodrive.xyz token.",
    "USER_TD_MODE": "👥 **User TD Mode**: Enable User GDrive TD mode.",
    "USER_TD_SA": "📧 **User TD SA**: A global service account email for User TD uploads.",
    "USER_SESSION_STRING": "🔑 **User Session String**: Your Pyrogram user session string.",
    "USE_SERVICE_ACCOUNTS": "🤖 **Use Service Accounts**: Enable Google service accounts for GDrive uploads.",
    "WEB_PINCODE": "🔒 **Web Pincode**: Require a pincode for the web file selector.",
    "YT_DLP_OPTIONS": '⚙️ **YT-DLP Options**: Default options for yt-dlp.',
}
