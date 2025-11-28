#!/usr/bin/env python3
from logging import getLogger, ERROR
from time import time
from pickle import load as pload
from os import makedirs, path as ospath, listdir, remove as osremove
from io import FileIO
from re import search as re_search
from urllib.parse import parse_qs, urlparse, quote as rquote
from random import randrange
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type, RetryError

from bot import OWNER_ID, config_dict, list_drives_dict, GLOBAL_EXTENSION_FILTER
from bot.helper.ext_utils.bot_utils import setInterval, async_to_sync, get_readable_file_size, fetch_user_tds
from bot.helper.ext_utils.fs_utils import get_mime_type
from bot.helper.ext_utils.leech_utils import format_filename

LOGGER = getLogger(__name__)
getLogger('googleapiclient.discovery').setLevel(ERROR)


class GoogleDriveHelper:
    def __init__(self, name=None, path=None, listener=None):
        self.__OAUTH_SCOPE = ['https://www.googleapis.com/auth/drive']
        self.__G_DRIVE_DIR_MIME_TYPE = "application/vnd.google-apps.folder"
        self.__G_DRIVE_BASE_DOWNLOAD_URL = "https://drive.google.com/uc?id={}&export=download"
        self.__G_DRIVE_DIR_BASE_DOWNLOAD_URL = "https://drive.google.com/drive/folders/{}"
        self.__listener = listener
        self.__user_id = listener.message.from_user.id if listener else None
        self.__path = path
        self.__processed_bytes = 0
        self.__is_cancelled = False
        self.__sa_index = 0
        self.__sa_count = 1
        self.__sa_number = 100
        self.__service = self.__authorize()
        self.name = name

    @property
    def speed(self):
        try:
            return self.__processed_bytes / (time() - self.__start_time)
        except ZeroDivisionError:
            return 0

    @property
    def processed_bytes(self):
        return self.__processed_bytes

    def __authorize(self):
        if config_dict['USE_SERVICE_ACCOUNTS']:
            try:
                json_files = listdir("accounts")
                self.__sa_number = len(json_files)
                self.__sa_index = randrange(self.__sa_number)
                credentials = service_account.Credentials.from_service_account_file(
                    f'accounts/{json_files[self.__sa_index]}', scopes=self.__OAUTH_SCOPE)
                LOGGER.info(f"Authorized with SA: {json_files[self.__sa_index]}")
            except Exception as e:
                LOGGER.error(f"SA authorization failed: {e}")
                return None
        elif ospath.exists('token.pickle'):
            with open('token.pickle', 'rb') as f:
                credentials = pload(f)
            LOGGER.info("Authorized with token.pickle")
        else:
            LOGGER.error('token.pickle not found!')
            return None
        return build('drive', 'v3', credentials=credentials, cache_discovery=False)

    def __switch_service_account(self):
        if self.__sa_index == self.__sa_number - 1:
            self.__sa_index = 0
        else:
            self.__sa_index += 1
        self.__sa_count += 1
        LOGGER.info(f"Switching to SA index: {self.__sa_index}")
        self.__service = self.__authorize()

    @staticmethod
    def getIdFromUrl(link):
        if "folders" in link or "file" in link:
            match = re_search(r"folders/|file/d/|/document/d/|/presentation/d/|/spreadsheets/d/|/drawings/d/|/forms/d/|open\?id=([-\w]+)", link)
            if match:
                return match.group(1)
        parsed = urlparse(link)
        return parse_qs(parsed.query).get('id', [None])[0]

    @retry(wait=wait_exponential(multiplier=2, min=3, max=6), stop=stop_after_attempt(3), retry=retry_if_exception_type(Exception))
    def getFolderData(self, file_id):
        try:
            meta = self.__service.files().get(fileId=file_id, supportsAllDrives=True).execute()
            if meta.get('mimeType') == self.__G_DRIVE_DIR_MIME_TYPE:
                return meta.get('name')
        except Exception as e:
            LOGGER.error(f"Error getting folder data: {e}")

    @retry(wait=wait_exponential(multiplier=2, min=3, max=6), stop=stop_after_attempt(3), retry=retry_if_exception_type(Exception))
    def __set_permission(self, file_id):
        permissions = {'role': 'reader', 'type': 'anyone', 'withLink': True}
        self.__service.permissions().create(fileId=file_id, body=permissions, supportsAllDrives=True).execute()

    @retry(wait=wait_exponential(multiplier=2, min=3, max=6), stop=stop_after_attempt(3), retry=retry_if_exception_type(Exception))
    def __get_file_metadata(self, file_id):
        return self.__service.files().get(fileId=file_id, supportsAllDrives=True, fields='name, id, mimeType, size').execute()

    def deletefile(self, link: str):
        try:
            file_id = self.getIdFromUrl(link)
            self.__service.files().delete(fileId=file_id, supportsAllDrives=True).execute()
            return "Successfully deleted."
        except (KeyError, IndexError):
            return "Invalid G-Drive ID."
        except HttpError as err:
            LOGGER.error(f"Delete error: {err}")
            return str(err)

    def upload(self, file_name, size, gdrive_id):
        gdrive_id = gdrive_id or config_dict.get('GDRIVE_ID')
        self.__is_uploading = True
        item_path = ospath.join(self.__path, file_name)
        LOGGER.info(f"Uploading to G-Drive: {item_path}")

        try:
            if ospath.isfile(item_path):
                if item_path.lower().endswith(tuple(GLOBAL_EXTENSION_FILTER)):
                    raise Exception('File extension is excluded.')
                mime_type = get_mime_type(item_path)
                link = self.__upload_file(item_path, file_name, mime_type, gdrive_id)
            else:
                mime_type = 'Folder'
                dir_id = self.__create_directory(ospath.basename(file_name), gdrive_id)
                self.__upload_dir(item_path, dir_id)
                link = self.__G_DRIVE_DIR_BASE_DOWNLOAD_URL.format(dir_id)

            if self.__is_cancelled:
                if mime_type == 'Folder':
                    self.deletefile(self.__G_DRIVE_DIR_BASE_DOWNLOAD_URL.format(dir_id))
                return

            LOGGER.info(f"Successfully uploaded to G-Drive: {file_name}")
            async_to_sync(self.__listener.onUploadComplete, link, size, 0, 0, mime_type, file_name)
        except Exception as err:
            err_str = str(err).replace('<', '').replace('>', '')
            async_to_sync(self.__listener.onUploadError, err_str)

    def __upload_dir(self, input_directory, dest_id):
        for item in listdir(input_directory):
            if self.__is_cancelled: break
            item_path = ospath.join(input_directory, item)
            if ospath.isdir(item_path):
                current_dir_id = self.__create_directory(item, dest_id)
                self.__upload_dir(item_path, current_dir_id)
            elif not item.lower().endswith(tuple(GLOBAL_EXTENSION_FILTER)):
                mime_type = get_mime_type(item_path)
                self.__upload_file(item_path, item, mime_type, dest_id)
            else:
                osremove(item_path)

    @retry(wait=wait_exponential(multiplier=2, min=3, max=6), stop=stop_after_attempt(3), retry=retry_if_exception_type(Exception))
    def __create_directory(self, name, parent_id):
        name, _ = async_to_sync(format_filename, name, self.__user_id, isMirror=True)
        file_metadata = {'name': name, 'mimeType': self.__G_DRIVE_DIR_MIME_TYPE}
        if parent_id: file_metadata['parents'] = [parent_id]

        file = self.__service.files().create(body=file_metadata, supportsAllDrives=True).execute()
        file_id = file.get("id")

        if not config_dict.get('IS_TEAM_DRIVE'):
            self.__set_permission(file_id)

        LOGGER.info(f'Created G-Drive Folder: {name} (ID: {file_id})')
        return file_id

    @retry(wait=wait_exponential(multiplier=2, min=3, max=6), stop=stop_after_attempt(3), retry=retry_if_exception_type(Exception))
    def __upload_file(self, file_path, file_name, mime_type, parent_id):
        file_name, _ = async_to_sync(format_filename, file_name, self.__user_id, isMirror=True)
        file_metadata = {'name': file_name, 'mimeType': mime_type}
        if parent_id: file_metadata['parents'] = [parent_id]

        media_body = MediaFileUpload(file_path, mimetype=mime_type, resumable=True, chunksize=100 * 1024 * 1024)

        drive_file = self.__service.files().create(body=file_metadata, media_body=media_body, supportsAllDrives=True)

        response = None
        retries = 0
        while not response and not self.__is_cancelled:
            try:
                _, response = drive_file.next_chunk()
            except HttpError as err:
                if err.resp.status in [500, 502, 503, 504] and retries < 10:
                    retries += 1
                    continue
                reason = err.error_details[0].get('reason') if err.error_details else None
                if reason in ['userRateLimitExceeded', 'dailyLimitExceeded'] and config_dict.get('USE_SERVICE_ACCOUNTS'):
                    if self.__sa_count >= self.__sa_number:
                        raise Exception(f"Max SA switches reached: {self.__sa_count}")
                    self.__switch_service_account()
                    return self.__upload_file(file_path, file_name, mime_type, parent_id)
                raise err

        if self.__is_cancelled:
            return

        if not self.__listener.seed or self.__listener.newDir:
            try: osremove(file_path)
            except: pass

        if not config_dict.get('IS_TEAM_DRIVE'):
            self.__set_permission(response['id'])

        return self.__G_DRIVE_BASE_DOWNLOAD_URL.format(response.get('id'))

    async def cancel_download(self):
        self.__is_cancelled = True
        if self.__is_downloading:
            LOGGER.info(f"Cancelling Download: {self.name}")
            await self.__listener.onDownloadError('Download stopped by user!')
        elif self.__is_cloning:
            LOGGER.info(f"Cancelling Clone: {self.name}")
            await self.__listener.onUploadError('your clone has been stopped and cloned data has been deleted!')
        elif self.__is_uploading:
            LOGGER.info(f"Cancelling Upload: {self.name}")
            await self.__listener.onUploadError('your upload has been stopped and uploaded data has been deleted!')
    def clone(self, link, gdrive_id):
        if not gdrive_id:
            gdrive_id = config_dict['GDRIVE_ID']
        self.__is_cloning = True
        self.__start_time = time()
        self.__total_files = 0
        self.__total_folders = 0
        try:
            file_id = self.getIdFromUrl(link)
        except (KeyError, IndexError):
            return "Google Drive ID could not be found in the provided link", None, None, None, None
        msg = ""
        LOGGER.info(f"File ID: {file_id}")
        try:
            meta = self.__getFileMetadata(file_id)
            mime_type = meta.get("mimeType")
            if mime_type == self.__G_DRIVE_DIR_MIME_TYPE:
                dir_id = self.__create_directory(meta.get('name'), gdrive_id)
                self.__cloneFolder(meta.get('name'), meta.get('name'), meta.get('id'), dir_id)
                durl = self.__G_DRIVE_DIR_BASE_DOWNLOAD_URL.format(dir_id)
                if self.__is_cancelled:
                    LOGGER.info("Deleting cloned data from Drive...")
                    self.deletefile(durl)
                    return None, None, None, None, None
                mime_type = 'Folder'
                size = self.__processed_bytes
            else:
                file = self.__copyFile(meta.get('id'), gdrive_id, meta.get('name'))
                msg += f'<b>Name: </b><code>{file.get("name")}</code>'
                durl = self.__G_DRIVE_BASE_DOWNLOAD_URL.format(file.get("id"))
                if mime_type is None:
                    mime_type = 'File'
                size = int(meta.get('size', 0))
            return durl, size, mime_type, self.__total_files, self.__total_folders
        except Exception as err:
            if isinstance(err, RetryError):
                LOGGER.info(f"Total Attempts: {err.last_attempt.attempt_number}")
                err = err.last_attempt.exception()
            err = str(err).replace('>', '').replace('<', '')
            if "User rate limit exceeded" in err:
                msg = "User rate limit exceeded."
            elif "File not found" in err:
                if not self.__alt_auth:
                    token_service = self.__alt_authorize()
                    if token_service is not None:
                        LOGGER.error('File not found. Trying with token.pickle...')
                        self.__service = token_service
                        return self.clone(link)
                msg = "File not found."
            else:
                msg = f"Error.\n{err}"
            async_to_sync(self.__listener.onUploadError, msg)
            return None, None, None, None, None

    def __cloneFolder(self, name, local_path, folder_id, dest_id):
        LOGGER.info(f"Syncing: {local_path}")
        files = self.__getFilesByFolderId(folder_id)
        if len(files) == 0:
            return dest_id
        for file in files:
            if file.get('mimeType') == self.__G_DRIVE_DIR_MIME_TYPE:
                self.__total_folders += 1
                file_path = ospath.join(local_path, file.get('name'))
                current_dir_id = self.__create_directory(file.get('name'), dest_id)
                self.__cloneFolder(file.get('name'), file_path,
                                   file.get('id'), current_dir_id)
            elif not file.get('name').lower().endswith(tuple(GLOBAL_EXTENSION_FILTER)):
                self.__total_files += 1
                self.__copyFile(file.get('id'), dest_id, file.get('name'))
                self.__processed_bytes += int(file.get('size', 0))
                self.__total_time = int(time() - self.__start_time)
            if self.__is_cancelled:
                break

    @retry(wait=wait_exponential(multiplier=2, min=3, max=6), stop=stop_after_attempt(3),
           retry=retry_if_exception_type(Exception))
    def __copyFile(self, file_id, dest_id, file_name):
        file_name, _ = async_to_sync(format_filename, file_name, self.__user_id, isMirror=True)
        body = {'name': file_name,
                'parents': [dest_id]}
        try:
            return self.__service.files().copy(fileId=file_id, body=body, supportsAllDrives=True).execute()
        except HttpError as err:
            if err.resp.get('content-type', '').startswith('application/json'):
                reason = eval(err.content).get(
                    'error').get('errors')[0].get('reason')
                if reason not in ['userRateLimitExceeded', 'dailyLimitExceeded', 'cannotCopyFile']:
                    raise err
                if reason == 'cannotCopyFile':
                    LOGGER.error(err)
                elif config_dict['USE_SERVICE_ACCOUNTS']:
                    if self.__sa_count >= self.__sa_number:
                        LOGGER.info(
                            f"Reached maximum number of service accounts switching, which is {self.__sa_count}")
                        raise err
                    else:
                        if self.__is_cancelled:
                            return
                        self.__switchServiceAccount()
                        return self.__copyFile(file_id, dest_id, file_name)
                else:
                    LOGGER.error(f"Got: {reason}")
                    raise err

    def __escapes(self, estr):
        chars = ['\\', "'", '"', r'\a', r'\b', r'\f', r'\n', r'\r', r'\t']
        for char in chars:
            estr = estr.replace(char, f'\\{char}')
        return estr.strip()

    def __get_recursive_list(self, file, rootid):
        rtnlist = []
        # if not rootid:
        #    rootid = file.get('teamDriveId')
        if rootid == "root":
            rootid = self.__service.files().get(
                fileId='root', fields='id').execute().get('id')
        x = file.get("name")
        y = file.get("id")
        while (y != rootid):
            rtnlist.append(x)
            file = self.__service.files().get(fileId=file.get("parents")[0], supportsAllDrives=True,
                                              fields='id, name, parents').execute()
            x = file.get("name")
            y = file.get("id")
        rtnlist.reverse()
        return rtnlist

    def __drive_query(self, dir_id, fileName, stopDup, isRecursive, itemType):
        try:
            if isRecursive:
                if stopDup:
                    query = f"name = '{fileName}' and "
                else:
                    fileName = fileName.split()
                    query = "".join(
                        f"name contains '{name}' and "
                        for name in fileName
                        if name != ''
                    )
                    if itemType == "files":
                        query += "mimeType != 'application/vnd.google-apps.folder' and "
                    elif itemType == "folders":
                        query += "mimeType = 'application/vnd.google-apps.folder' and "
                query += "trashed = false"
                if dir_id == "root":
                    return self.__service.files().list(q=f"{query} and 'me' in owners",
                                                       pageSize=200, spaces='drive',
                                                       fields='files(id, name, mimeType, size, parents)',
                                                       orderBy='folder, name asc').execute()
                else:
                    return self.__service.files().list(supportsAllDrives=True, includeItemsFromAllDrives=True,
                                                       driveId=dir_id, q=query, spaces='drive', pageSize=150,
                                                       fields='files(id, name, mimeType, size, teamDriveId, parents)',
                                                       corpora='drive', orderBy='folder, name asc').execute()
            else:
                if stopDup:
                    query = f"'{dir_id}' in parents and name = '{fileName}' and "
                else:
                    query = f"'{dir_id}' in parents and "
                    fileName = fileName.split()
                    for name in fileName:
                        if name != '':
                            query += f"name contains '{name}' and "
                    if itemType == "files":
                        query += "mimeType != 'application/vnd.google-apps.folder' and "
                    elif itemType == "folders":
                        query += "mimeType = 'application/vnd.google-apps.folder' and "
                query += "trashed = false"
                return self.__service.files().list(supportsAllDrives=True, includeItemsFromAllDrives=True,
                                                   q=query, spaces='drive', pageSize=150,
                                                   fields='files(id, name, mimeType, size)',
                                                   orderBy='folder, name asc').execute()
        except Exception as err:
            err = str(err).replace('>', '').replace('<', '')
            LOGGER.error(err)
            return {'files': []}

    def drive_list(self, fileName, stopDup=False, noMulti=False, isRecursive=True, itemType="", userId=None):
        msg = f"""<figure><img src='{config_dict["COVER_IMAGE"]}'></figure>"""
        fileName = self.__escapes(str(fileName))
        contents_no = 0
        telegraph_content = []
        Title = False
        merged_dict = list_drives_dict
        if userId and (user_tds := async_to_sync(fetch_user_tds, userId)):
            merged_dict = {**list_drives_dict, **user_tds}
        if len(merged_dict) > 1:
            token_service = self.__alt_authorize()
            if token_service is not None:
                self.__service = token_service
        for no, (drive_name, drives_dict) in enumerate(merged_dict.items(), start=1):
            dir_id = drives_dict['drive_id']
            index_url = drives_dict['index_link']
            isRecur = False if isRecursive and len(
                dir_id) > 23 else isRecursive
            response = self.__drive_query(dir_id, fileName, stopDup, isRecur, itemType)
            if not response["files"]:
                if noMulti:
                    break
                else:
                    continue
            if not Title:
                msg += f'<h4>📌 Drive Query : {fileName}</h4>'
                Title = True
            if drive_name:
                msg += f"<aside>╾──────────────────────╼</aside><br><aside><b>#{no} {drive_name} Drive</b></aside><br><aside>╾──────────────────────╼</aside><br>"
            msg += "<ol>"
            for file in response.get('files', []):
                mime_type = file.get('mimeType')
                msg += "<li>"
                if mime_type == "application/vnd.google-apps.folder":
                    furl = f"https://drive.google.com/drive/folders/{file.get('id')}"
                    msg += f"📁 <code>{file.get('name')}<br>(folder)</code><br>"
                    drive_link = False
                    if userId == OWNER_ID or not config_dict['DISABLE_DRIVE_LINK']:
                        msg += f"<b>🗃 <a href={furl}>Drive Link</a></b>"
                        drive_link = True
                    if index_url:
                        if drive_link:
                            msg += "<b> |</b>"
                        if isRecur:
                            url_path = "/".join([rquote(n, safe='')
                                                for n in self.__get_recursive_list(file, dir_id)])
                        else:
                            url_path = rquote(f'{file.get("name")}', safe='')
                        url = f'{index_url}/{url_path}/'
                        msg += f' <b>⚡️ <a href="{url}">Index Link</a></b>'
                elif mime_type == 'application/vnd.google-apps.shortcut':
                    furl = f"https://drive.google.com/drive/folders/{file.get('id')}"
                    msg += f"⁍<a href='https://drive.google.com/drive/folders/{file.get('id')}'>{file.get('name')}" \
                        f"</a> (shortcut)"
                else:
                    furl = f"https://drive.google.com/uc?id={file.get('id')}&export=download"
                    msg += f"📄 <code>{file.get('name')}<br>({get_readable_file_size(int(file.get('size', 0)))})</code><br>"
                    drive_link = False
                    if userId == OWNER_ID or not config_dict['DISABLE_DRIVE_LINK']:
                        msg += f"<b>🗃 <a href={furl}>Drive Link</a></b>"
                        drive_link = True
                    if index_url:
                        if drive_link:
                            msg += "<b> |</b>"
                        if isRecur:
                            url_path = "/".join(rquote(n, safe='') for n in self.__get_recursive_list(file, dir_id))
                        else:
                            url_path = rquote(f'{file.get("name")}')
                        url = f'{index_url}/{url_path}'
                        msg += f' <b>⚡️ <a href="{url}">Index Link</a></b>'
                        if mime_type.startswith(('image', 'video', 'audio')):
                            urlv = f'{index_url}/{url_path}?a=view'
                            msg += f' <b>| 🔍 <a href="{urlv}">View Link</a></b>'
                msg += '</li><br><br>'
                contents_no += 1
                if len(msg.encode('utf-8')) > 39000:
                    telegraph_content.append(msg)
                    msg = ''
            msg += "</ol>"
            if noMulti:
                break

        if msg != f"""<figure><img src='{config_dict["COVER_IMAGE"]}'></figure>""":
            telegraph_content.append(msg)

        return telegraph_content, contents_no

    def count(self, link):
        try:
            file_id = self.getIdFromUrl(link)
        except (KeyError, IndexError):
            return "Google Drive ID could not be found in the provided link", None, None, None, None
        LOGGER.info(f"File ID: {file_id}")
        try:
            return self.__proceed_count(file_id)
        except Exception as err:
            if isinstance(err, RetryError):
                LOGGER.info(
                    f"Total Attempts: {err.last_attempt.attempt_number}")
                err = err.last_attempt.exception()
            err = str(err).replace('>', '').replace('<', '')
            if "File not found" in err:
                if not self.__alt_auth:
                    token_service = self.__alt_authorize()
                    if token_service is not None:
                        LOGGER.error(
                            'File not found. Trying with token.pickle...')
                        self.__service = token_service
                        return self.count(link)
                msg = "File not found."
            else:
                msg = f"Error.\n{err}"
        return msg, None, None, None, None

    def __proceed_count(self, file_id):
        meta = self.__getFileMetadata(file_id)
        name = meta['name']
        LOGGER.info(f"Counting: {name}")
        mime_type = meta.get('mimeType')
        if mime_type == self.__G_DRIVE_DIR_MIME_TYPE:
            self.__gDrive_directory(meta)
            mime_type = 'Folder'
        else:
            if mime_type is None:
                mime_type = 'File'
            self.__total_files += 1
            self.__gDrive_file(meta)
        return name, mime_type, self.__total_bytes, self.__total_files, self.__total_folders

    def __gDrive_file(self, filee):
        size = int(filee.get('size', 0))
        self.__total_bytes += size

    def __gDrive_directory(self, drive_folder):
        files = self.__getFilesByFolderId(drive_folder['id'])
        if len(files) == 0:
            return
        for filee in files:
            shortcut_details = filee.get('shortcutDetails')
            if shortcut_details is not None:
                mime_type = shortcut_details['targetMimeType']
                file_id = shortcut_details['targetId']
                filee = self.__getFileMetadata(file_id)
            else:
                mime_type = filee.get('mimeType')
            if mime_type == self.__G_DRIVE_DIR_MIME_TYPE:
                self.__total_folders += 1
                self.__gDrive_directory(filee)
            else:
                self.__total_files += 1
                self.__gDrive_file(filee)

    def download(self, link):
        self.__is_downloading = True
        file_id = self.getIdFromUrl(link)
        self.__updater = setInterval(self.__update_interval, self.__progress)
        try:
            meta = self.__getFileMetadata(file_id)
            if meta.get("mimeType") == self.__G_DRIVE_DIR_MIME_TYPE:
                self.__download_folder(file_id, self.__path, self.name)
            else:
                makedirs(self.__path, exist_ok=True)
                self.__download_file(file_id, self.__path,
                                     self.name, meta.get('mimeType'))
        except Exception as err:
            if isinstance(err, RetryError):
                LOGGER.info(
                    f"Total Attempts: {err.last_attempt.attempt_number}")
                err = err.last_attempt.exception()
            err = str(err).replace('>', '').replace('<', '')
            if "downloadQuotaExceeded" in err:
                err = "Download Quota Exceeded."
            elif "File not found" in err:
                if not self.__alt_auth:
                    token_service = self.__alt_authorize()
                    if token_service is not None:
                        LOGGER.error(
                            'File not found. Trying with token.pickle...')
                        self.__service = token_service
                        self.__updater.cancel()
                        return self.download(link)
                err = 'File not found!'
            async_to_sync(self.__listener.onDownloadError, err)
            self.__is_cancelled = True
        finally:
            self.__updater.cancel()
            if self.__is_cancelled:
                return
            async_to_sync(self.__listener.onDownloadComplete)

    def __download_folder(self, folder_id, path, folder_name):
        folder_name = folder_name.replace('/', '')
        if not ospath.exists(f"{path}/{folder_name}"):
            makedirs(f"{path}/{folder_name}")
        path += f"/{folder_name}"
        result = self.__getFilesByFolderId(folder_id)
        if len(result) == 0:
            return
        result = sorted(result, key=lambda k: k['name'])
        for item in result:
            file_id = item['id']
            filename = item['name']
            shortcut_details = item.get('shortcutDetails')
            if shortcut_details is not None:
                file_id = shortcut_details['targetId']
                mime_type = shortcut_details['targetMimeType']
            else:
                mime_type = item.get('mimeType')
            if mime_type == self.__G_DRIVE_DIR_MIME_TYPE:
                self.__download_folder(file_id, path, filename)
            elif not ospath.isfile(f"{path}{filename}") and not filename.lower().endswith(tuple(GLOBAL_EXTENSION_FILTER)):
                self.__download_file(file_id, path, filename, mime_type)
            if self.__is_cancelled:
                break

    @retry(wait=wait_exponential(multiplier=2, min=3, max=6), stop=stop_after_attempt(3),
           retry=(retry_if_exception_type(Exception)))
    def __download_file(self, file_id, path, filename, mime_type):
        request = self.__service.files().get_media(
            fileId=file_id, supportsAllDrives=True)
        filename = filename.replace('/', '')
        if len(filename.encode()) > 255:
            ext = ospath.splitext(filename)[1]
            filename = f"{filename[:245]}{ext}"
            if self.name.endswith(ext):
                self.name = filename
        if self.__is_cancelled:
            return
        fh = FileIO(f"{path}/{filename}", 'wb')
        downloader = MediaIoBaseDownload(
            fh, request, chunksize=100 * 1024 * 1024)
        done = False
        retries = 0
        while not done:
            if self.__is_cancelled:
                fh.close()
                break
            try:
                self.__status, done = downloader.next_chunk()
            except HttpError as err:
                if err.resp.status in [500, 502, 503, 504] and retries < 10:
                    retries += 1
                    continue
                if err.resp.get('content-type', '').startswith('application/json'):
                    reason = eval(err.content).get(
                        'error').get('errors')[0].get('reason')
                    if reason not in [
                        'downloadQuotaExceeded',
                        'dailyLimitExceeded',
                    ]:
                        raise err
                    if config_dict['USE_SERVICE_ACCOUNTS']:
                        if self.__sa_count >= self.__sa_number:
                            LOGGER.info(
                                f"Reached maximum number of service accounts switching, which is {self.__sa_count}")
                            raise err
                        else:
                            if self.__is_cancelled:
                                return
                            self.__switchServiceAccount()
                            LOGGER.info(f"Got: {reason}, Trying Again...")
                            return self.__download_file(file_id, path, filename, mime_type)
                    else:
                        LOGGER.error(f"Got: {reason}")
                        raise err
        self.__file_processed_bytes = 0

    def driveclean(self, drive_id: str, trash: bool):
        pass
