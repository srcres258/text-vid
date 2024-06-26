import math
import os
import random

import cv2
import numpy as np
from PIL import ImageFont, ImageDraw, Image
from tqdm import tqdm
from loguru import logger

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
            bg_video_path: str,
            pause_duration_per_unit: float = 0.25
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
        :param pause_duration_per_unit: Pause duration between
         every subtitle (in seconds).
        """

        self.target_path = target_path
        self.fps = fps
        self.width = width
        self.height = height
        self.subtitle_text_units = subtitle_text_units
        self.font_path = font_path
        self.font_size = font_size
        self.bg_video_path = bg_video_path
        self.pause_duration_per_unit = pause_duration_per_unit

        self.font = ImageFont.truetype(font_path, font_size)
        self.frame_span_subtitles: list[FrameSpanSubtitle] = []
        self.bg_video_files: list[str] = []

        dir_list = os.listdir(bg_video_path)
        for file in dir_list:
            self.bg_video_files.append(os.path.join(bg_video_path, file))

    def generate(self) -> bool:
        """
        Generate the video file.
        :return: True if the video file was generated,
         False if an error occurred.
        """

        if len(self.frame_span_subtitles) == 0:
            self.generate_frame_span_subtitles()

        bg_vc = self.cv_open_random_bg_video_capture()
        if not bg_vc.isOpened():
            return False

        size = (self.width, self.height)
        vw = cv2.VideoWriter(
            self.target_path,
            cv2.VideoWriter_fourcc(*'mp4v'),
            self.fps,
            size
        )

        try:
            frame_count = self.calc_total_frames()
            fss_iter = iter(self.frame_span_subtitles)
            cur_fss = next(fss_iter)

            for cur_frame in tqdm(range(frame_count)):
                # Read a frame from the video capture.
                ret, image = bg_vc.read()
                if (not ret) or (image is None):
                    # If the current video capture is ended, open a new one.
                    bg_vc = self.cv_open_random_bg_video_capture()
                    # Then read again.
                    ret, image = bg_vc.read()
                # Resize it to the current size.
                image = cv2.resize(image, dsize=size)

                # If subtitle exists and should be displayed,
                # generate the subtitle frame and add it onto the background.
                if cur_fss and cur_frame >= cur_fss.start_frame:
                    fss_frames, fss_x, fss_y, fss_width, fss_height = (
                        self.cv_generate_subtitle_text_frame(cur_fss.subtitle.text))
                    # Do coordinate checks to avert drawing operations outside the frame.
                    if fss_x + fss_width > self.width:
                        fss_width = self.width - fss_x
                    if fss_y + fss_height > self.height:
                        fss_height = self.height - fss_y

                    # Dig a rectangle in the image to contain the subtitle.
                    image[fss_y:fss_y + fss_height, fss_x:fss_x + fss_width, 0] = 0  # B channel
                    image[fss_y:fss_y + fss_height, fss_x:fss_x + fss_width, 1] = 0  # G channel
                    image[fss_y:fss_y + fss_height, fss_x:fss_x + fss_width, 2] = 0  # R channel
                    # Then add the subtitle into the image.
                    for fss_frame in fss_frames:
                        image = cv2.add(image, fss_frame)

                    if cur_frame >= cur_fss.end_frame:
                        try:
                            cur_fss = next(fss_iter)
                        except StopIteration:
                            cur_fss = None

                # Write the current frame to the writer.
                vw.write(image)
        except BaseException:
            return False
        finally:
            bg_vc.release()
            vw.release()

        return True

    def generate_frame_span_subtitles(self):
        """
        Generate the frame span subtitles for this video.
        """

        cur_unit_start_frame = 0

        for i, unit in enumerate(self.subtitle_text_units):
            if len(unit.subtitles) > 0:
                for subtitle in unit.subtitles:
                    start_frame = cur_unit_start_frame + self.raw_duration_to_frames(subtitle.start)
                    end_frame = start_frame + self.raw_duration_to_frames(subtitle.duration)
                    fss = FrameSpanSubtitle(subtitle, start_frame, end_frame)
                    self.frame_span_subtitles.append(fss)

            cur_unit_start_frame += self.duration_to_frames(unit.get_audio_duration())
            if i < len(self.subtitle_text_units) - 1:
                cur_unit_start_frame += self.duration_to_frames(self.pause_duration_per_unit)

    def calc_total_duration(self) -> float:
        """
        Calculate the total duration (in seconds) of the video.
        :return: Total duration (in seconds) of the video.
        """

        result = 0.0

        for i, unit in enumerate(self.subtitle_text_units):
            result += unit.get_audio_duration()
            if i < len(self.subtitle_text_units) - 1:
                result += self.pause_duration_per_unit

        return result

    def calc_total_frames(self) -> int:
        """
        Calculate the total number of frames in the video.
        :return: Total number of frames in the video.
        """

        result = 0

        for i, unit in enumerate(self.subtitle_text_units):
            result += self.duration_to_frames(unit.get_audio_duration())
            if i < len(self.subtitle_text_units) - 1:
                result += self.duration_to_frames(self.pause_duration_per_unit)

        return result

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

    def cv_generate_empty_frame(self) -> cv2.typing.MatLike:
        """
        Generate an empty OpenCV image frame.
        :return: The empty OpenCV image frame.
        """

        size = (self.width, self.height)

        # Create blank image
        image = Image.new("RGB", size, (0, 0, 0))
        # Convert PIL image into OpenCV image
        opencv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

        return opencv_image

    def cv_generate_subtitle_text_frame(
            self,
            text: str,
            y_offset: int = 0,
            max_chars_per_line: int = 30
    ) -> tuple[list[cv2.typing.MatLike], int, int, int, int]:
        """
        Generate an OpenCV image containing a subtitle with the text given.

        If the text is too long to fit the video size, automatic line-breaking will
        be used to make it well-displayed in the video.

        :param text: The text string used to generate the subtitle.
        :param y_offset: Offset value of y coordinate when drawing the subtitle.
        :param max_chars_per_line: The maximum number of characters allowed per line
        for automatic line-breaking.
        :return: The OpenCV image frame; x, y, width and height of the subtitle text.
        """

        lines = []
        for i in range(0, len(text), max_chars_per_line):
            end = i + max_chars_per_line
            if end > len(text):
                end = len(text)
            lines.append(text[i:end])

        x = None
        y = None
        width = 0
        height = 0
        results = []

        for line in lines:
            opencv_image, cur_x, cur_y, cur_width, cur_height = (
                self.cv_generate_subtitle_text_frame_single(line, y_offset=height + y_offset))

            if x is None or y is None:
                x = cur_x
                y = cur_y
            if cur_width > width:
                width = cur_width
                x = cur_x
            height += cur_height

            results.append(opencv_image)

        return results, x, y, width, height

    def cv_generate_subtitle_text_frame_single(
            self,
            text: str,
            y_offset: int = 0
    ) -> tuple[cv2.typing.MatLike, int, int, int, int]:
        """
        Generate an OpenCV image containing a subtitle with the text given.

        Note that automatic line-breaking will not be performed even if the text is
        too long to fit in the video within this method.

        :param text: The text string used to generate the subtitle.
        :param y_offset: Offset value of y coordinate when drawing the subtitle.
        :return: The OpenCV image frame; x, y, width and height of the subtitle text.
        """

        size = (self.width, self.height)

        # Create blank image
        image = Image.new("RGB", size, (0, 0, 0))
        draw = ImageDraw.Draw(image)

        # Draw text on image
        _, _, text_width, text_height = draw.textbbox((0, 0), text=text, font=self.font)
        x = int((image.width - text_width) / 2)
        # y = (image.height - text_height) / 2
        y = image.height - text_height - BOTTOM_DISTANCE + y_offset
        draw.text((x, y), text, font=self.font, fill=(255, 255, 255))

        # Convert PIL image into OpenCV image
        opencv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

        return opencv_image, x, y, text_width, text_height

    def cv_open_random_bg_video_capture(self):
        """
        Open a random OpenCV video capture as the background of the video.
        :return: The random OpenCV video capture
        """

        file = random.choice(self.bg_video_files)
        logger.info(f"{file} is chosen as the background video.")

        return cv2.VideoCapture(file)
