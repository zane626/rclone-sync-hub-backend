import asyncio
loop = asyncio.get_event_loop()

def check_task_to_queue():
    print('run check_task_to_queue')
    loop.call_later(1, check_task_to_queue)

loop.call_later(1, check_task_to_queue)

loop.run_forever()