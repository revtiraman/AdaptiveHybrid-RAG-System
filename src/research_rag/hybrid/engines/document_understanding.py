from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import math
import re
import unicodedata


@dataclass(slots=True)
class TextLine:
    text: str
    x0: float
    y0: float
    x1: float
    y1: float
    font_size: float
    font_name: str
    is_bold: bool


class BBoxTextReconstructor:
    def reconstruct(self, fitz_page) -> list[TextLine]:
        words = fitz_page.get_text("words") or []
        if not words:
            return []

        page_width = float(getattr(fitz_page.rect, "width", 0.0) or 0.0)
        columns = self.detect_columns(page_width=page_width, words=words)
        row_groups = self._group_by_y(words, tolerance=3.0)

        lines: list[TextLine] = []
        median_height = self._median([(float(w[3]) - float(w[1])) for w in words]) or 10.0
        paragraph_gap = max(8.0, median_height * 1.5)

        prev_y: float | None = None
        for row in row_groups:
            ordered_words = sorted(row, key=lambda item: float(item[0]))
            if columns == 2 and page_width > 0:
                split_x = page_width / 2.0
                left = [w for w in ordered_words if float(w[0]) <= split_x]
                right = [w for w in ordered_words if float(w[0]) > split_x]
                segmented = [left, right]
            else:
                segmented = [ordered_words]

            for segment in segmented:
                if not segment:
                    continue
                line = self._build_line(segment)
                if not line.text:
                    continue

                if prev_y is not None and (line.y0 - prev_y) > paragraph_gap:
                    # Preserve paragraph boundaries so chunking can keep semantic blocks.
                    lines.append(
                        TextLine(
                            text="",
                            x0=line.x0,
                            y0=line.y0,
                            x1=line.x1,
                            y1=line.y1,
                            font_size=line.font_size,
                            font_name=line.font_name,
                            is_bold=False,
                        )
                    )
                lines.append(line)
                prev_y = line.y0

        return lines

    def detect_columns(self, page_width: float, words: list) -> int:
        if page_width <= 0 or len(words) < 20:
            return 1
        bins = [0] * 20
        for word in words:
            x0 = float(word[0])
            idx = min(19, max(0, int((x0 / page_width) * 20)))
            bins[idx] += 1

        first_half = bins[:10]
        second_half = bins[10:]
        peak_left = max(first_half) if first_half else 0
        peak_right = max(second_half) if second_half else 0
        valley = min(bins[8:12]) if len(bins) >= 12 else 0

        if peak_left > 0 and peak_right > 0 and valley < (0.45 * min(peak_left, peak_right)):
            return 2
        return 1

    def process_pdf(self, pdf_path: Path) -> list[dict[str, object]]:
        try:
            import fitz
        except ModuleNotFoundError as exc:
            raise RuntimeError("PyMuPDF is required for bbox reconstruction fallback") from exc

        pages: list[dict[str, object]] = []
        with fitz.open(str(pdf_path)) as doc:
            for idx, page in enumerate(doc, start=1):
                text_lines = self.reconstruct(page)
                parts: list[str] = []
                for line in text_lines:
                    if line.text:
                        parts.append(line.text)
                    elif parts and parts[-1] != "":
                        parts.append("")
                text = "\n".join(parts)
                quality = extraction_quality_score(text)
                pages.append(
                    {
                        "page_number": idx,
                        "text": text,
                        "layout_columns": self.detect_columns(float(page.rect.width), page.get_text("words") or []),
                        "extraction_quality_score": quality,
                        "elements_by_type": {"paragraph": max(1, len([p for p in parts if p.strip()]))},
                    }
                )
        return pages

    @staticmethod
    def _group_by_y(words: list, tolerance: float) -> list[list]:
        ordered = sorted(words, key=lambda w: float(w[1]))
        groups: list[list] = []
        for word in ordered:
            y0 = float(word[1])
            if not groups:
                groups.append([word])
                continue
            previous_y = float(groups[-1][-1][1])
            if abs(y0 - previous_y) <= tolerance:
                groups[-1].append(word)
            else:
                groups.append([word])
        return groups

    @staticmethod
    def _build_line(words: list) -> TextLine:
        words_sorted = sorted(words, key=lambda item: float(item[0]))
        tokens = [str(item[4]).strip() for item in words_sorted if str(item[4]).strip()]
        joined = " ".join(tokens)
        joined = clean_extracted_text(joined)
        heights = [(float(item[3]) - float(item[1])) for item in words_sorted]
        font_size = sum(heights) / max(1, len(heights))

        x0 = min(float(item[0]) for item in words_sorted)
        y0 = min(float(item[1]) for item in words_sorted)
        x1 = max(float(item[2]) for item in words_sorted)
        y1 = max(float(item[3]) for item in words_sorted)

        return TextLine(
            text=joined,
            x0=x0,
            y0=y0,
            x1=x1,
            y1=y1,
            font_size=font_size,
            font_name="unknown",
            is_bold=False,
        )

    @staticmethod
    def _median(values: list[float]) -> float:
        if not values:
            return 0.0
        ordered = sorted(values)
        mid = len(ordered) // 2
        if len(ordered) % 2 == 1:
            return ordered[mid]
        return (ordered[mid - 1] + ordered[mid]) / 2.0


def clean_extracted_text(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("\u00ad", "")
    text = text.replace("\u200b", "").replace("\ufeff", "")
    # Dehyphenate: join words split at end-of-line with a hyphen (PDF artifact)
    text = re.sub(r"([a-zA-Z])-\s*\n\s*([a-z])", r"\1\2", text)
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"([a-z])([A-Z])", r"\1 \2", text)
    text = re.sub(r"([.,;:!?])([A-Za-z])", r"\1 \2", text)
    return text.strip()


def extraction_quality_score(text: str) -> float:
    words = text.split()
    if not words:
        return 0.0

    avg_word_len = sum(len(word) for word in words) / len(words)
    space_ratio = text.count(" ") / max(len(text), 1)
    alpha_ratio = sum(1 for char in text if char.isalpha()) / max(len(text), 1)

    len_score = max(0.0, 1.0 - abs(avg_word_len - 6.0) / 6.0)
    space_score = min(space_ratio / 0.15, 1.0)
    alpha_score = min(alpha_ratio / 0.65, 1.0)
    score = (len_score * 0.4) + (space_score * 0.3) + (alpha_score * 0.3)
    return float(max(0.0, min(score, 1.0)))
