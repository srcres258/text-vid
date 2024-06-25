from typing import Optional


SUBTITLE_SPLITING_CHARS = [*list("，。！？；：")]
PUNCTRATION_MARKS = list("，。！？；：、—（）【】《》“”‘’")


class TextTimestamp:
    def __init__(
            self,
            text: str,
            start: float,
            duration: float,
            start_text_index: int,
            text_length: int
    ):
        """
        Initialize a timestamp.
        :param start:
        :param duration:
        :param start_text_index:
        :param text_length:
        """

        self.text = text
        self.start = start
        self.duration = duration
        self.start_text_index = start_text_index
        self.text_length = text_length

    def end(self):
        return self.start + self.duration


class Subtitle:
    def __init__(
            self,
            text: str,
            start: float,
            duration: float
    ):
        """
        Initialize a subtitle.
        :param text: The subtitle text.
        :param start:
        :param duration:
        """

        self.text = text
        self.start = start
        self.duration = duration


class TextUnit:
    def __init__(self, text: str):
        """
        Initializes a TextUnit to be handled by a Processor.
        :param text:  The text to be processed.
        """

        self.text = text

        self.audio_file_path: Optional[str] = None
        self.text_timestamps: list[TextTimestamp] = []
        self.subtitles: list[Subtitle] = []

    def make_subtitles(self):
        """
        Make subtitles according to text timestamps.
        """

        cur_index = 0
        cur_subtitle_content = ""
        cur_subtitle_start = 0
        cur_subtitle_duration = 0

        for timestamp in self.text_timestamps:
            start_text_index = cur_index
            end_text_index = start_text_index + timestamp.text_length
            end_text_index += self.__detect_tail_punctuation_count(end_text_index)
            text = self.text[start_text_index:end_text_index]

            if len(cur_subtitle_content) == 0:
                cur_subtitle_start = timestamp.start
            cur_subtitle_content += text
            cur_subtitle_duration += timestamp.duration

            if self.__should_split_subtitle(cur_index, timestamp):
                subtitle = Subtitle(cur_subtitle_content, cur_subtitle_start, cur_subtitle_duration)
                self.subtitles.append(subtitle)
                cur_subtitle_content = ""
                cur_subtitle_start = 0
                cur_subtitle_duration = 0

            cur_index = end_text_index

    def __should_split_subtitle(
            self,
            cur_index: int,
            timestamp: TextTimestamp
    ) -> bool:
        end_index = cur_index + timestamp.text_length
        tail_punctuation_count = self.__detect_tail_punctuation_count(end_index)
        if tail_punctuation_count > 0:
            for c in self.text[end_index:end_index+tail_punctuation_count]:
                if c in SUBTITLE_SPLITING_CHARS:
                    return True

        return cur_index + timestamp.text_length >= len(self.text) or\
            self.text[cur_index + timestamp.text_length] in SUBTITLE_SPLITING_CHARS

    def __detect_tail_punctuation_count(self, tail_index: int) -> int:
        result = 0
        for i in range(tail_index, len(self.text)):
            if self.text[i] in PUNCTRATION_MARKS:
                result += 1
            else:
                break
        return result
