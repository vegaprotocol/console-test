import os
from dotenv import load_dotenv

load_dotenv()

console_image_name = os.getenv(
    "CONSOLE_IMAGE_NAME", default="vegaprotocol/trading:develop"
)
