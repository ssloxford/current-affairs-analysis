"""
Build static website from the result viewer webserver.
To use, launch the webserver and then run this script.

Downlaods all result pages, and compresses photos.
"""

import os

from . import publish
from . import path_tools
from . import metadata
from . import process_data
from .webserver import webserver

from multiprocessing import Process

import asyncio
import requests
import functools

from PIL import Image

def my_wget(s: requests.Session, path):
    dst = os.path.join(path_tools.DATA_BASE_DIR, path)
    os.makedirs(os.path.dirname(dst), exist_ok=True)

    res = s.get("http://localhost:8000/" + path)
    if res.status_code == 200:
        with open(os.path.join(path_tools.DATA_BASE_DIR, path), "wb") as f:
            f.write(res.content)

def check_server_running(s: requests.Session):
    try:
        return s.get("http://localhost:8000/").status_code == 200
    except Exception as e:
        print(e)
        return False


async def main():
    #Start webserver
    p = Process(target=webserver.syncmain)
    p.start()

    meta =  metadata.read_charger_metadata_table()

    s = requests.Session()

    while not check_server_running(s):
        print("Waiting for webserver to start")
        await asyncio.sleep(1)

    # Get home page
    my_wget(s, "index.html")
    my_wget(s, "static/index.css")
    my_wget(s, "static/index.js")
    for park in meta.parks.values():
        my_wget(s, "page/" + park.id + ".html") 

    print("Stopping server")
    p.terminate()
    p.join()

if __name__ == '__main__':
    asyncio.run(main())