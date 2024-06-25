from pydub import AudioSegment

from text_vid.tts import TextUnit


class AudioGenerator:
    def __init__(
            self,
            text_units: list[TextUnit],
            output_path: str,
            pause_duration_per_unit: float = 0.25
    ):
        """
        Initialise an AudioGenerator object.
        :param text_units: Source text units used to generate the general audio.
        :param output_path: The path to the output audio file.
        :param pause_duration_per_unit: Pause duration between
         every subtitle (in seconds).
        """

        self.text_units = text_units
        self.output_path = output_path
        self.pause_duration_per_unit = pause_duration_per_unit

    def generate(self):
        """
        Generate the audio file.
        """

        audios = []

        for unit in self.text_units:
            audio = AudioSegment.from_mp3(unit.audio_file_path)
            silence_duration = int(self.pause_duration_per_unit * 1000.)
            silence = AudioSegment.silent(duration=silence_duration)

            audios.append(audio)
            audios.append(silence)

        output = audios[0]
        for i in range(1, len(audios)):
            output += audios[i]

        output_format = self.output_path.split('.')[-1]
        output.export(self.output_path, format=output_format)
