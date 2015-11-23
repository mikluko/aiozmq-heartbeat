import asyncio
import aiozmq.rpc
import logging
from collections import OrderedDict


class Handler(aiozmq.rpc.AttrHandler):

    def __init__(self, events, *, logger=None):
        self.events = events
        self.logger = logger or logging.getLogger(__name__)

    @aiozmq.rpc.method
    def bump(self, who):
        event = self.events.get(who)
        if event:
            event.set()
            self.logger.debug('received bump form %s', who)


class Subscribe(object):

    def __init__(self, events, *, timeout=5, loop=None, logger=None):
        self.events = events
        self.timeout = timeout
        self.loop = loop or asyncio.get_event_loop()
        self.logger = logger or logging.getLogger(__name__)

        self.stop = asyncio.Event()
        self.term = asyncio.Event()
        self.avail = asyncio.Event()

        self.loop.create_task(self.monitor())
        self.logger.debug('started')

    def close(self):
        self.stop.set()

    async def wait_closed(self):
        return await self.term.wait()

    async def monitor(self):
        expect = [asyncio.ensure_future(ev.wait()) for ev in self.events]
        done, pending = await asyncio.wait(expect, timeout=self.timeout, loop=self.loop)

        if len(pending):
            if self.avail.is_set():
                self.avail.clear()
                self.logger.debug('become unavailable')
            for fut in pending:
                fut.cancel()
        else:
            if not self.avail.is_set():
                self.logger.debug('become available')
                self.avail.set()
            for ev in self.events:
                ev.clear()

        if self.stop.is_set():
            self.logger.debug('terminated')
            self.term.set()
        else:
            self.loop.create_task(self.monitor())

    async def wait(self):
        await self.avail.wait()


async def subscribe(watch, *, timeout=5, bind=None, connect=None, logger=None):
    ''' Returns asyncio.Event which triggers once all watched instances are available '''
    assert bind or connect
    events = OrderedDict([(name, asyncio.Event()) for name in watch])
    handler = Handler(events, logger=logger)
    server = await aiozmq.rpc.serve_pubsub(handler,
        bind=bind, connect=connect, subscribe='heartbeat')
    subscribe = Subscribe(events.values(), timeout=timeout, logger=logger)

    async def wait():
        await subscribe.wait_closed()
        server.close()
        await server.wait_closed()
    subscribe.loop.create_task(wait())

    return subscribe
