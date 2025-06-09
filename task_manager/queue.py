import threading
import asyncio
from queue import Queue
from task_manager.rclone_operator import RcloneCommand
from utils.db import mongo_db

class TaskQueue:
    def __init__(self, num_threads=5):
        self.queue = Queue()
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop = asyncio.get_event_loop()
        self.num_threads = num_threads
        self.threads = []
        self._create_threads()

    def _create_threads(self):
        for _ in range(self.num_threads):
            thread = threading.Thread(target=self._worker)
            thread.daemon = True
            thread.start()
            self.threads.append(thread)

    def _worker(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        while True:
            task_id = self.queue.get()
            if task_id is None:
                break
            rclone_command = RcloneCommand({'task_id': task_id})
            rclone_command.run()
            self.queue.task_done()
            
            # Wait for a new task if the queue is empty
            if self.queue.empty():
                self.queue.join()

    def add_task(self, task):
        self.queue.put(task)

    def set_num_threads(self, num_threads):
        self.num_threads = num_threads
        self._create_threads()

    def stop(self):
        for _ in self.threads:
            self.queue.put(None)
        for thread in self.threads:
            thread.join()

    def check_task_to_queue(self, delay):
        collection = mongo_db.get_collection('tasks')
        tasks = collection.find({'status': 0})
        for task in tasks:
            self.add_task(str(task['_id']))
            collection.update_one({'_id': task['_id']}, {'$set': {'status': 1}})
        self.loop.call_later(delay, self.check_task_to_queue, delay)

    def add_task_with_delay(self, delay):
        self.loop.call_later(delay, self.check_task_to_queue, delay)
        self.loop.run_forever()