from threading import Lock
from concurrent.futures import ThreadPoolExecutor

async_tasks = {}
task_lock = Lock()
executor = ThreadPoolExecutor(max_workers=4)
