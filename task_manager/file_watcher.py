"""
初始化文件夹监听器,并在后台运行,初始化前先遍历所有文件夹下的文件
"""
import os
import sys
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from utils.db import get_db
from models.folder import Folder
from services.folder_service import FolderService

def check_file_to_task(file_path):
    pass


class CodeHandler(FileSystemEventHandler):
    def on_modified(self, event):
        print("File modified:", event.src_path)


class FileWatcher:
    def __init__(self, path):
        self.path = path
        self.observer = Observer()
        self.observer.schedule(CodeHandler(), path, recursive=True)

    def start(self):
        self.initial_scan()
        self.observer.start()

    def initial_scan(self):
        for root, dirs, files in os.walk(self.path):
            for file in files:
                filepath = os.path.join(root, file)
                check_file_to_task(filepath)

