from asyncio import create_subprocess_exec
from aiofiles.os import path as aiopath
from aiofiles import open as aiopen
from configparser import ConfigParser

from bot import config_dict, bot_loop, bot_cache

RcloneServe = []


async def rclone_serve_booter():
    """
    Starts the rclone serve process.
    """
    if not config_dict.get('RCLONE_SERVE_URL') or not await aiopath.exists('wcl.conf'):
        if RcloneServe:
            try:
                RcloneServe[0].kill()
                RcloneServe.clear()
            except Exception:
                pass
        return

    config = ConfigParser()
    async with aiopen('wcl.conf', 'r') as f:
        config.read_string(await f.read())

    if not config.has_section('combine'):
        upstreams = ' '.join(f'{remote}={remote}:' for remote in config.sections())
        config.add_section('combine')
        config.set('combine', 'type', 'combine')
        config.set('combine', 'upstreams', upstreams)
        with open('wcl.conf', 'w') as f:
            config.write(f, space_around_delimiters=False)

    if RcloneServe:
        try:
            RcloneServe[0].kill()
            RcloneServe.clear()
        except Exception:
            pass

    cmd = [
        bot_cache['pkgs'][3], "serve", "http", "combine:",
        "--config", "wcl.conf",
        "--no-modtime",
        "--addr", f":{config_dict['RCLONE_SERVE_PORT']}",
        "--vfs-cache-mode", "full",
        "--vfs-cache-max-age", "1m0s",
        "--buffer-size", "64M"
    ]

    if (user := config_dict.get('RCLONE_SERVE_USER')) and (pswd := config_dict.get('RCLONE_SERVE_PASS')):
        cmd.extend(("--user", user, "--pass", pswd))

    rc_serve_process = await create_subprocess_exec(*cmd)
    RcloneServe.append(rc_serve_process)


bot_loop.run_until_complete(rclone_serve_booter())
