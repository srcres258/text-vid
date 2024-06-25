import math

import cv2
import numpy as np
from PIL import ImageFont, ImageDraw, Image
from tqdm import tqdm

from text_vid.tts import TextUnit
from text_vid.tts.duration import Duration
from text_vid.tts.text_unit import Subtitle

BOTTOM_DISTANCE: int = 60


class FrameSpanSubtitle:
    def __init__(
            self,
            subtitle: Subtitle,
            start_frame: int,
            end_frame: int
    ):
        """
        Initialize a FrameSpanSubtitle object.
        :param subtitle: The Subtitle object.
        :param start_frame: The start frame of the subtitle in the video.
        :param end_frame: The end frame of the subtitle in the video.
        """

        self.subtitle = subtitle
        self.start_frame = start_frame
        self.end_frame = end_frame


class VideoGenerator:
    def __init__(
            self,
            target_path: str,
            fps: float,
            width: int,
            height: int,
            subtitle_text_units: list[TextUnit],
            font_path: str,
            font_size: int,
            pause_duration_per_subtitle: float = 0.5
    ):
        """
        Initialize a VideoGenerator object.
        :param target_path: Path of the video file to be generated.
        :param fps: FPS of the generated video.
        :param width: Frame width of the generated video.
        :param height: Frame height of the generated video.
        :param subtitle_text_units: Subtitles (list of TextUnits) to be
         displayed in the video.
        :param font_path: Path of the font file to be used.
        :param font_size: Size of the font to be displayed in the video.
        :param pause_duration_per_subtitle: Pause duration between
         every subtitle (in seconds).
        """

        self.target_path = target_path
        self.fps = fps
        self.width = width
        self.height = height
        self.subtitle_text_units = subtitle_text_units
        self.font_path = font_path
        self.font_size = font_size
        self.pause_duration_per_subtitle = pause_duration_per_subtitle

        self.font = ImageFont.truetype(font_path, font_size)
        self.frame_span_subtitles: list[FrameSpanSubtitle] = []

    def generate(self) -> bool:
        """
        Generate the video file.
        :return: True if the video file was generated,
         False if an error occurred.
        """

        if len(self.frame_span_subtitles) == 0:
            self.generate_frame_span_subtitles()

        size = (self.width, self.height)
        vw = cv2.VideoWriter(
            self.target_path,
            cv2.VideoWriter_fourcc(*'mp4v'),
            self.fps,
            size
        )
        frame_count = self.calc_total_frames()

        try:
            for cur_frame in tqdm(range(frame_count)):
                # Create blank image
                image = Image.new("RGB", size, (0, 0, 0))
                draw = ImageDraw.Draw(image)

                # Draw text on image
                text = "第{}帧".format(cur_frame)
                _, _, text_width, text_height = draw.textbbox((0, 0), text=text, font=self.font)
                x = (image.width - text_width) / 2
                # y = (image.height - text_height) / 2
                y = image.height - text_height - BOTTOM_DISTANCE
                draw.text((x, y), text, font=self.font, fill=(255, 255, 255))

                # Convert PIL image into OpenCV image
                opencv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
                vw.write(opencv_image)
        except:
            return False
        finally:
            vw.release()

        return True

    def generate_frame_span_subtitles(self):
        """
        Generate the frame span subtitles for this video.
        """

        cur_unit_start_frame = 0

        for unit in self.subtitle_text_units:
            if len(unit.subtitles) > 0:
                for subtitle in unit.subtitles:
                    pass # TODO

    def calc_total_duration(self) -> float:
        """
        Calculate the total duration (in seconds) of the video.
        :return: Total duration (in seconds) of the video.
        """

        result = 0.0

        for unit in self.subtitle_text_units:
            if len(unit.subtitles) > 0:
                last_subtitle = unit.subtitles[-1]
                start_dur = Duration(last_subtitle.start)
                duration_dur = Duration(last_subtitle.duration)
                dur = start_dur.seconds_in_total() + duration_dur.seconds_in_total()
                dur += self.pause_duration_per_subtitle
                result += dur

        return result

    def calc_total_frames(self) -> int:
        """
        Calculate the total number of frames in the video.
        :return: Total number of frames in the video.
        """

        return self.duration_to_frames(self.calc_total_duration())

    def duration_to_frames(self, duration: float) -> int:
        """
        Converts duration in seconds to frames.
        :param duration: Duration in seconds.
        :return: Frames representing the duration.
        """

        return int(math.ceil(duration * self.fps))

    def raw_duration_to_frames(self, raw_duration: float) -> int:
        """
        Converts raw duration in seconds to frames.
        :param raw_duration: Raw duration in seconds.
        :return: Frames representing the duration.
        """

        dur = Duration(raw_duration)
        return self.duration_to_frames(dur.seconds_in_total())
