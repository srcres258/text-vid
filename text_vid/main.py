import argparse
import os
from loguru import logger

from text_vid.app import App


DEFAULT_TMP_DIR_PATH: str = "./tmp"
DEFAULT_RATE: str = "+0%"
DEFAULT_VOLUME: str = "+0%"
DEFAULT_PITCH: str = "+0Hz"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--text", type=str,
                        required=True,
                        help='Path of the text file.')
    parser.add_argument("-o", "--output", type=str,
                        required=True,
                        help='Path of the output file.')
    parser.add_argument("--tmp-dir", type=str,
                        required=False, default=DEFAULT_TMP_DIR_PATH,
                        help='Path of the temporary directory.')
    parser.add_argument("--rate", type=str,
                        required=False, default=DEFAULT_RATE,
                        help='Incremental rate of the speech speed, defaults to "+0%".')
    parser.add_argument("--volume", type=str,
                        required=False, default=DEFAULT_VOLUME,
                        help='Incremental rate of the speech volume, defaults to "+0%".')
    parser.add_argument("--pitch", type=str,
                        required=False, default=DEFAULT_PITCH,
                        help='Incremental rate of the speech pitch, defaults to "+0Hz".')

    args = parser.parse_args()
    text_path = args.text
    output_path = args.output
    tmp_dir_path = args.tmp_dir
    rate = args.rate
    volume = args.volume
    pitch = args.pitch

    # Ensure the existence of the temporary directory.
    # If already existing, remove at first.
    if not os.path.exists(tmp_dir_path):
        os.makedirs(tmp_dir_path)

    # Initialise and run the application.
    app = App(text_path, output_path, tmp_dir_path, rate, volume, pitch)
    logger.info("Launching application...")
    app.run()
