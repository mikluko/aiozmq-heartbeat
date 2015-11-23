import asyncio
import aiozmq.rpc
import logging


class Publish(object):

    def __init__(self, name, publisher, *, interval=1, logger=None, loop=None):
        self.name = name
        self.publisher = publisher
        self.interval = interval
        self.stop = asyncio.Event()
        self.logger = logger or logging.getLogger(__name__)
        self.loop = loop or asyncio.get_event_loop()
        self.loop.create_task(self.push())

    async def push(self):
        while not self.stop.is_set():
            self.logger.debug('sending heartbeat')
            self.publisher.publish('heartbeat').bump(self.name)
            await asyncio.sleep(self.interval)
        self.logger.debug('terminated')

    def close(self):
        self.stop.set()


async def publish(name, *, interval=1, bind=None, connect=None, logger=None):
    assert bind or connect
    publisher = await aiozmq.rpc.connect_pubsub(connect=connect, bind=bind)
    return Publish(name, publisher, interval=interval, logger=logger)
