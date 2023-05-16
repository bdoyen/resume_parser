import re
from fuzzywuzzy import fuzz, process

from utils import get_next_value
from headers import Headers


class TextSegmenter:
    def find_best_match(self, text: str, search_phrases: tuple[str]) -> int:
        """
        Find the best match for a given text among the provided search phrases.

        Args:
            text (str): The input text to search in.
            search_phrases (Tuple[str]): The search phrases to match against the input text.

        Returns:
            int: The starting index of the best match. Returns -1 if no match is found.
        """
        best_match = process.extractOne(text, search_phrases)
        best_match_phrase = best_match[0]
        pattern = re.compile(re.escape(best_match_phrase), re.IGNORECASE)
        match = pattern.search(text)

        if match:
            return match.start()
        else:
            return -1

    def segmenter(self, text: str) -> dict[str, str]:
        """
        Segment the input text into sections based on provided headers.

        Args:
            text (str): The input text to segment.
            headers (Dict[str, List[str]]): A dictionary of header titles and their corresponding keywords.

        Returns:
            Dict[str, str]: A dictionary containing the segmented sections of the input text.
        """

        searchable_text = text.lower()

        indexes = {k: 0 for k, _ in Headers.HEADERS.items()}
        segments = {k: "" for k, _ in Headers.HEADERS.items()}

        # Find starting indexes
        for header_title, header_keywords in Headers.HEADERS.items():
            if header_keywords:
                start_idx = self.find_best_match(searchable_text, header_keywords)
                if start_idx > 0:
                    indexes[header_title] = start_idx

        # Sort indexes
        sorted_indexes = dict(sorted(indexes.items(), key=lambda item: item[1]))

        # Get first and last non-null indexes
        first_non_null_index = min([v for _, v in sorted_indexes.items() if v > 0])
        last_non_null_index = max([v for _, v in sorted_indexes.items()])

        # Find consecutive segments (assuming there are not overlapping between each other)
        for header_title, index in sorted_indexes.items():
            if index > 0:
                try:
                    next_index = sorted_indexes[
                        get_next_value(sorted_indexes, header_title)
                    ]
                    segments[header_title] = text[index:next_index].strip()
                except:
                    segments[header_title] = text[index:].strip()
            else:
                segments[header_title] = text[index:].strip()

        # Treat special cases assuming a certain order among Resume's sections
        for segment_name in Headers.TOP_SEGMENTS:
            if indexes[segment_name] == 0:
                segments[segment_name] = text[:first_non_null_index].strip()

        for segment_name in Headers.BOTTOM_SEGMENTS:
            if indexes[segment_name] == 0:
                segments[segment_name] = text[last_non_null_index:].strip()

        return segments
