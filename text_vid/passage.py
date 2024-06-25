from typing import Optional

from text_vid.tts import TextUnit


def parse_raw_text(raw_text: str) -> (str, str, list[str]):
    lines = raw_text.splitlines()

    title = ""
    author = ""
    contents = []
    title_set = False
    author_set = False

    for line in lines:
        if line is None or len(line) == 0:
            continue
        if not title_set:
            title = line
            title_set = True
        elif not author_set:
            author = line
            author_set = True
        else:
            line = line.strip()
            contents.append(line)

    return title, author, contents


class Passage:
    def __init__(self, raw_text: str):
        """
        Create a Passage object with the given raw text.
        :param raw_text: The raw text of the passage.
        """

        title, author, contents = parse_raw_text(raw_text)
        self.title: str = title
        self.author: str = author
        self.contents: list[str] = contents

        self.title_unit: Optional[TextUnit] = None
        self.content_units: list[TextUnit] = []

    def __repr__(self) -> str:
        return (f"Passage author: {self.author}, "
                f"title: {self.title}, "
                f"contents count: {len(self.contents)}")
