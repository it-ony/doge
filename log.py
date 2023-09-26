import logging
import os

logger = logging.getLogger("doge")
formatter = logging.Formatter(
    "%(asctime)s ; %(name)s ; %(levelname)s ; %(lineno)d; %(message)s"
)
logHandler = logging.FileHandler(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "doge.log"), mode="w"
)
logHandler.setFormatter(formatter)
logHandler.flush()
logger.addHandler(logHandler)
