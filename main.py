import os
import json
from tqdm import tqdm
from zipfile import ZipFile
from urllib import request
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

# TODO: make the backup filename as an input or implement a way to grab the latest backup in the folder
zip_path = 'boorusphere_backup_2024-04-14-19-26-15.zip'

def readJsonFromZip(zip_path, json_filename):
    with ZipFile(zip_path, mode='r') as myzip:
        with myzip.open(json_filename) as myfile:
            return myfile.read()
        
def listFolderStruct(illust_list):
    folder_struct = defaultdict(set)
    for illust in illust_list:
        post = illust['post']
        folder_struct[post['serverId']].add(post['rateValue'])
    return folder_struct

def createFolderStruct(current_path, folder_struct):
    for k, v in folder_struct.items():
        for rating in v:
            os.makedirs(current_path + '/downloads/'+ k + '/' + rating, exist_ok=True)

def downloadIllust(DownloadInfo):
    with DownloadProgressBar(unit='B', unit_scale= True,
                                miniters=1, desc=DownloadInfo.filename) as t:
            download_path = '/'.join([DownloadInfo.current_path, 'downloads', DownloadInfo.serverId, DownloadInfo.rateValue]) + '/' + DownloadInfo.filename
            request.urlretrieve(DownloadInfo.url, download_path, reporthook=t.update_to)

def addHeadersToRequest():
    headers=[('User-Agent', 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11'),
        ('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'),
        ('Accept-Charset', 'ISO-8859-1,utf-8;q=0.7,*;q=0.3'),
        ('Accept-Encoding', 'none'),
        ('Accept-Language', 'en-US,en;q=0.8'),
        ('Connection', 'keep-alive')]
    opener = request.build_opener()
    opener.addheaders = headers
    request.install_opener(opener)

class DownloadInfo:
    def __init__(self, url, current_path, filename, serverId, rateValue):
        self.url = url
        self.current_path = current_path
        self.filename = filename
        self.serverId = serverId
        self.rateValue = rateValue

class DownloadProgressBar(tqdm):
    def update_to(self, b=1, bsize=1, tsize=None):
        if tsize is not None:
            self.total = tsize
        self.update(b * bsize - self.n)

def main():
    json_file = readJsonFromZip(zip_path, 'favorites.json')
    illust_list = json.loads(json_file)
    folder_struct = listFolderStruct(illust_list)

    current_path = os.path.abspath(os.getcwd())
    createFolderStruct(current_path, folder_struct)

    danbooru_download_list = []
    other_download_list = []

    for illust in illust_list:
        illust_p = illust['post']
        filename = str(illust_p['id']) + '.' + illust_p['originalFile'].split('.')[-1]
        url = illust_p['originalFile']
        serverId = illust_p['serverId']
        rateValue = illust_p['rateValue']

        download_path = '/'.join([current_path, 'downloads', serverId, rateValue]) + '/' + filename
        if not os.path.isfile(download_path):
            if serverId == 'Danbooru':
                danbooru_download_list.append(DownloadInfo(url, current_path, filename, serverId, rateValue))
            else:
                other_download_list.append(DownloadInfo(url, current_path, filename, serverId, rateValue))
        # downloadIllust(url, current_path, filename, serverId, rateValue)

    # execute without headers
    with ThreadPoolExecutor(max_workers=32) as executor:
        executor.map(downloadIllust, danbooru_download_list)

    # Added headers to avoid 403 Forbidden code in Konachan
    addHeadersToRequest()

    # execute with headers
    with ThreadPoolExecutor(max_workers=32) as executor:
        executor.map(downloadIllust, other_download_list)

if __name__ ==  '__main__':
    main()

# Test code for requesting images from a specific url

#if not os.path.isfile(os.path.abspath(os.getcwd()) + '/sample/s1.jpg'):
#    request.urlretrieve('https://cdn.donmai.us/original/18/c8/18c8af0b2988de82c8b6e1d3e2c3af2e.png', 
#                    os.path.abspath(os.getcwd()) + '/sample/s1.png')