"""
Signal two: the style signal. ← YOU BUILD THIS IN MILESTONE 4

Signal one reads the text for meaning. This one measures it *as text* — the
shape of it, without understanding a word.

Three measures are stubbed below because the brief names those three. They are
stubs, not implementations: what they compute is yours, and so is how you
combine them.

    sentence_length_spread   do sentences vary in length, or march in step?
    type_token_ratio         how much of the vocabulary repeats?
    punctuation_density      how much punctuation, and how varied?

Why these might differ between human and AI writing: generated prose tends
toward even, mid-length sentences and a narrower band of vocabulary, because
that's what "most likely next word" produces on average. Human writing is
lumpier — a three-word sentence next to a forty-word one.

⚠️ **The blind spot, which you have to name in Milestone 1.**

This signal cannot read. It has no idea what the text says. Anything that
changes the shape without changing the substance moves it — adding typos,
breaking up sentences, pasting in a quotation. That is a very cheap thing for
someone to do on purpose, and unit 8's attack set will do it to you.

Build each function on its own and call it from a terminal before you wire
anything together:

    python stylometry.py "some text to look at"
"""

import re
import statistics


def sentences(text: str) -> list[str]:
    """Split into sentences. Rough and good enough — given to you."""
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p for p in parts if p.strip()]


def words(text: str) -> list[str]:
    """Split into lowercase words, punctuation stripped. Given to you."""
    return re.findall(r"[a-z0-9']+", text.lower())


# ── The three measures — YOU BUILD THESE ─────────────────────────────────────

def sentence_length_spread(text: str) -> float:
    """
    Measure how much sentence lengths vary relative to their average length.

    Higher values mean sentence lengths vary more.
    Lower values mean sentence lengths are more uniform.
    """
    sentence_list = sentences(text)

    if len(sentence_list) < 2:
        return 0.0

    lengths = [len(words(sentence)) for sentence in sentence_list]
    mean_length = statistics.mean(lengths)

    if mean_length == 0:
        return 0.0

    return statistics.stdev(lengths) / mean_length


def type_token_ratio(text: str) -> float:
    """
    Measure vocabulary variety.

    Returns:
        Unique words divided by total words.
        Higher values mean more varied vocabulary.
    """
    word_list = words(text)

    if not word_list:
        return 0.0

    unique_words = set(word_list)
    return len(unique_words) / len(word_list)


def punctuation_density(text: str) -> float:
    """
    Measure punctuation use relative to the number of words.

    Counts punctuation marks that tend to vary between writing styles.
    """
    word_list = words(text)

    if not word_list:
        return 0.0

    punctuation_marks = re.findall(r"[,;:!?—-]", text)

    return len(punctuation_marks) / len(word_list)


# ── Combining them ───────────────────────────────────────────────────────────

def style_signal(text: str) -> float:
    """
    Combine the three stylometric measures into a 0-1 score.

    Higher means more AI-like.
    """

    spread = sentence_length_spread(text)
    ttr = type_token_ratio(text)
    punct = punctuation_density(text)

    # Lower sentence-length variation looks more AI-like.
    # Treat spread >= 1.0 as fully human-like for this feature.
    spread_ai = 1.0 - min(spread, 1.0)

    # In the calibration examples, higher TTR appeared more AI-like.
    # TTR is length-sensitive, so keep this feature lightly weighted.
    ttr_ai = (ttr - 0.65) / 0.25
    ttr_ai = max(0.0, min(ttr_ai, 1.0))

    # Lower punctuation density looks more AI-like.
    # Around 0.12 punctuation marks per word or higher is treated
    # as strongly human-like for this feature.
    punct_ai = 1.0 - min(punct / 0.12, 1.0)

    score = (
        0.50 * spread_ai
        + 0.20 * ttr_ai
        + 0.30 * punct_ai
    )

    return round(max(0.0, min(score, 1.0)), 4)


if __name__ == "__main__":
    import sys

    text = " ".join(sys.argv[1:]) or (
        "The system works well. It handles most cases correctly and provides "
        "good results. Users generally find it easy to use and understand."
    )

    print(f"{len(sentences(text))} sentences, {len(words(text))} words\n")
    print(f"sentence_length_spread   {sentence_length_spread(text)}")
    print(f"type_token_ratio         {type_token_ratio(text)}")
    print(f"punctuation_density      {punctuation_density(text)}")
    print(f"style_signal             {style_signal(text)}   (higher = more likely AI)")
    print("\nAll zeros? These are stubs — Milestone 4 is where you build them.")
