import os
import time
from typing import Optional, Any

import edge_tts

from text_vid.tts.text_unit import TextUnit, TextTimestamp


class Processor:
    def __init__(
            self,
            tmp_dir: str,
            voice: str = "zh-CN-YunjianNeural",
            rate: str = "+0%",
            volume: str = "+0%",
            pitch: str = "+0Hz",
            proxy: Optional[str] = None,
            connect_timeout: int = 10,
            receive_timeout: int = 60
    ):
        """
        Initialize the text-to-speech processor.
        :param tmp_dir: Path of the temporary directory used to store temporary voice files.
        :param voice: Name of the voice used by the text-to-speech engine.
        :param rate: Speech rate required by text-to-speech engine.
        :param volume: Speech volume required by text-to-speech engine.
        :param pitch: Speech pitch required by text-to-speech engine.
        :param proxy: The network proxy used to connect to the online engine. None if no proxy.
        :param connect_timeout: Connecting timeout to the online engine (in seconds).
        :param receive_timeout: Receiving timeout to the online engine (in seconds).
        """

        self.tmp_dir = tmp_dir
        self.voice = voice
        self.rate = rate
        self.volume = volume
        self.pitch = pitch
        self.proxy = proxy
        self.connect_timeout = connect_timeout
        self.receive_timeout = receive_timeout

        self.__start_index = 0

        if not os.path.exists(self.tmp_dir):
            os.makedirs(self.tmp_dir)

    def process(self, unit: TextUnit):
        """
        Process the given text unit with this text-to-speech processor.
        :param unit: The text unit to be processed.
        """

        # Select an audio output path.
        output_name = f"audio_{int(time.time())}.mp3"
        output_path = os.path.join(self.tmp_dir, output_name)
        unit.audio_file_path = output_path

        # Then begin to process.
        communicate = edge_tts.Communicate(
            unit.text,
            self.voice,
            rate=self.rate,
            volume=self.volume,
            pitch=self.pitch,
            proxy=self.proxy,
            connect_timeout=self.connect_timeout,
            receive_timeout=self.receive_timeout
        )

        self.__start_index = 0
        with open(output_path, 'wb') as f:
            for chunk in communicate.stream_sync():
                if chunk["type"] == "audio":
                    f.write(chunk["data"])
                elif chunk["type"] == "WordBoundary":
                    self.__process_word_boundary(unit, chunk)

    def __process_word_boundary(self, unit: TextUnit, chunk: dict[str, Any]):
        offset: float = chunk["offset"]
        duration: float = chunk["duration"]
        text: str = chunk["text"]
        text_length = len(text)

        timestamp = TextTimestamp(text, offset, duration, self.__start_index, text_length)
        unit.text_timestamps.append(timestamp)
        self.__start_index += text_length
