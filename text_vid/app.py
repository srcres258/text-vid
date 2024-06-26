import os

from loguru import logger

from text_vid.passage import Passage
from text_vid import tts
from text_vid.tts import TextUnit
from text_vid.tts.audio_generator import AudioGenerator
from text_vid.video.video_generator import VideoGenerator


class App:
    def __init__(
            self,
            text_path: str,
            output_path: str,
            tmp_dir_path: str,
            font_path: str,
            bg_video_path: str,
            rate: str = "+0%",
            volume: str = "+0%",
            pitch: str = "+0Hz"
    ):
        """
        Initialise the application.
        """

        self.text_path = text_path
        self.output_path = output_path
        self.tmp_dir_path = tmp_dir_path
        self.font_path = font_path
        self.bg_video_path = bg_video_path
        self.rate = rate
        self.volume = volume
        self.pitch = pitch

        self.passage: Passage = None
        self.tts_processor: tts.Processor = None
        self.audio_generator: AudioGenerator = None
        self.video_generator: VideoGenerator = None

    def run(self):
        """
        Run the application.
        """

        # Initialize the passage at first.
        logger.info(f"Reading passage from: {self.text_path}")
        self.__init_passage()
        logger.info(f"Passage title: {self.passage.title}")
        logger.info(f"Passage author: {self.passage.author}")
        logger.info(f"Passage has {len(self.passage.contents)} content(s).")

        # Then initialize the processor.
        logger.info("Initializing TTS processor...")
        self.__init_processor()

        # Then process the text.
        logger.info("Processing passage TTS...")
        self.__process_text()

        # Then generate the audio.
        logger.info("Generating audio...")
        self.__generate_audio()

        # Then generate the video.
        logger.info("Generating video...")
        self.__generate_video()

    def __init_passage(self):
        with open(self.text_path, 'r', encoding='utf-8') as f:
            content = f.read()
            self.passage = Passage(content)

    def __init_processor(self):
        processor_tmp_dir = os.path.join(self.tmp_dir_path, "processor")
        if not os.path.exists(processor_tmp_dir):
            os.makedirs(processor_tmp_dir)
        self.tts_processor = tts.Processor(
            processor_tmp_dir,
            rate=self.rate,
            volume=self.volume,
            pitch=self.pitch
        )

    def __process_text(self):
        # Process the passage title at first.
        logger.info(f"Processing passage title: {self.passage.title}")
        self.passage.title_unit = TextUnit(self.passage.title)
        self.tts_processor.process(self.passage.title_unit)

        # Then process the content.
        for i, content in enumerate(self.passage.contents):
            logger.info(f"Processing content {i}/{len(self.passage.contents)} ...")
            unit = TextUnit(content)
            self.tts_processor.process(unit)
            logger.info("Making subtitles...")
            unit.make_subtitles()
            logger.info(f"Done. Found {len(unit.subtitles)} subtitle(s).")
            self.passage.content_units.append(unit)

    def __generate_audio(self):
        self.audio_generator = AudioGenerator(self.passage.content_units, os.path.join(self.tmp_dir_path, "audio.mp3"))
        self.audio_generator.generate()

    def __generate_video(self):
        self.video_generator = VideoGenerator(self.output_path, 30.0, 1280, 720, self.passage.content_units,
                                              self.font_path, 32, self.bg_video_path)
        self.video_generator.generate_frame_span_subtitles()
        self.video_generator.generate()
