import asyncio
import logging
import sys
from aiozmq import rpc
from aiozmq_heartbeat import publish, subscribe


logging.basicConfig(level=logging.INFO, format='%(relativeCreated)05d %(name)15s: %(message)s')

def echo(logger, message, level=logging.INFO):
    logger = logging.getLogger(logger)
    logger.log(level, message)


class Worker(rpc.AttrHandler):

    def __init__(self, name, sink):
        self.name = name
        self.sink = sink

    @rpc.method
    async def ping(self, ii):
        echo(self.name, ii)
        self.sink.notify.pong(ii)


class Sink(rpc.AttrHandler):

    @rpc.method
    async def pong(self, ii):
        echo('sink', ii)


HEARTBEAT_SOCK = 'tcp://127.0.0.1:7771'
VENT_SOCK = 'tcp://127.0.0.1:7772'
SINK_SOCK = 'tcp://127.0.0.1:7773'


async def run_vent():
    heartbeat = await subscribe(['worker', 'sink'], timeout=2,
        bind=HEARTBEAT_SOCK, logger=logging.getLogger('vent.heartbeat'))
    vent = await rpc.connect_pipeline(bind=VENT_SOCK)
    echo('vent', 'started')

    for ii in range(15):
        try:
            await asyncio.wait_for(heartbeat.wait(), timeout=1)
        except asyncio.TimeoutError:
            echo('vent', 'throttle')
        else:
            vent.notify.ping(ii)
            echo('vent', ii)
            await asyncio.sleep(1)

    heartbeat.close()
    await heartbeat.wait_closed()

    vent.close()
    await vent.wait_closed()

    echo('vent', 'stopped')


async def run_worker(name, startup, shutdown):
    await asyncio.sleep(startup)
    echo(name, 'started')
    sink = await rpc.connect_pipeline(connect=SINK_SOCK)
    worker = await rpc.serve_pipeline(Worker(name, sink), connect=VENT_SOCK)
    heartbeat = await publish('worker', connect=HEARTBEAT_SOCK)
    await asyncio.sleep(shutdown)
    echo(name, 'stopped')
    heartbeat.close()
    worker.close()
    sink.close()


async def run_sink(startup, shutdown):
    await asyncio.sleep(startup)
    echo('sink', 'started')
    sink = await rpc.serve_pipeline(Sink(), bind=SINK_SOCK)
    heartbeat = await publish('sink', connect=HEARTBEAT_SOCK)
    await asyncio.sleep(shutdown)
    echo('sink', 'stopped')
    heartbeat.close()
    sink.close()


def main():
    loop = asyncio.get_event_loop()
    loop.create_task(run_sink(5, 5))
    loop.create_task(run_worker('worker-1', 2.5, 4))
    loop.create_task(run_worker('worker-2', 3.5, 7))
    loop.run_until_complete(run_vent())

if __name__ == '__main__':
    main()
