"""
Runs all 5 sensor simulators concurrently, each on its own configurable
interval, dispatching readings to the fog node over HTTP.

Usage:
    python -m sensor_simulators.simulator
"""
import asyncio
import logging
import signal

from .config import settings
from .dispatcher import FogDispatcher
from .sensors import ALL_SENSOR_CLASSES

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")
logger = logging.getLogger("sensor_simulators")


async def main():
    logger.info("Starting %d sensor simulators, dispatching to %s", len(ALL_SENSOR_CLASSES), settings.FOG_NODE_URL)

    async with FogDispatcher() as dispatcher:
        sensors = [cls(dispatcher.send) for cls in ALL_SENSOR_CLASSES]
        tasks = [asyncio.create_task(sensor.run()) for sensor in sensors]

        stop_event = asyncio.Event()
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(sig, stop_event.set)
            except NotImplementedError:
                # add_signal_handler isn't available on some platforms (e.g. Windows)
                pass

        await stop_event.wait()
        logger.info("Shutting down sensor simulators...")
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
