from loguru import logger
from tqdm.asyncio import tqdm

CONSOLE_LOG_FORMAT = "<white>{time:HH:mm:ss}</white> | <level>{level: <8}</level> | <white>{message}</white>"


def set_logger():
    logger.remove()
    logger.add(lambda msg: tqdm.write(msg, end=''), colorize=True, format=CONSOLE_LOG_FORMAT)
