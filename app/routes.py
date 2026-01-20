from flask import Blueprint, render_template, request, url_for
from flask_login import current_user

from app.models import ClaimedBandName

# Create main blueprint
main_bp = Blueprint("main_bp", __name__)


import os
import random

import re

from titlecase import titlecase

TEXTPATH = "static/texts"
BANDSPATH = "static/data/bands.txt"

textfiles = [file for file in os.listdir(TEXTPATH) if file.endswith(".txt")]

texts = []

for textfile in textfiles:
    with open(TEXTPATH + "/" + textfile, "r") as f:
        texts.append(f.read())

text = " ".join(texts)
text = re.sub(r"- \n", "", text)

with open(BANDSPATH, "r") as f:
    existing_bands = {
        line.strip().lower()
        for line in f
        if line.strip() and not re.match(r"^Q\d+$", line.strip())
    }


def remove_punctuation(s):
    punctuation = "\"#$%&'()*+,-/:;<=>@[\]^_`{|}~.?!«»—"
    translator = str.maketrans({key: " " for key in punctuation})
    s = s.translate(translator)
    return s


def apply_capitalization(word):
    """Apply capitalization style based on real band name distribution"""
    # 99% title case, 0.1% each for UPPER, lower, CamelCase
    styles = ["title", "UPPER", "lower", "camel"]
    weights = [0.99, 0.001, 0.001, 0.001]
    style = random.choices(styles, weights=weights)[0]

    if style == "UPPER":
        return word.upper()
    elif style == "lower":
        return word.lower()
    elif style == "camel":
        # CamelCase: capitalize first letter of each word, no spaces
        return "".join(w.capitalize() for w in word.split())
    else:  # title (default)
        return titlecase(word.lower())


def prep_bandname(word):
    word = remove_punctuation(word)
    return apply_capitalization(word)


def is_valid_bandname(name):
    """Check if band name meets basic quality criteria"""
    # Remove newlines and extra whitespace
    name = " ".join(name.split())

    word_count = len(name.split())

    # Basic length and word count requirements
    if not (1 <= word_count <= 4 and 3 <= len(name) <= 50):
        return False

    # Filter out names with only common/boring words
    common_words = {
        "the",
        "and",
        "of",
        "in",
        "on",
        "at",
        "to",
        "for",
        "with",
        "from",
        "by",
        "as",
        "is",
        "was",
        "are",
        "were",
        "been",
        "be",
        "this",
        "that",
        "these",
        "those",
        "a",
        "an",
        "her",
        "his",
        "my",
        "your",
        "our",
        "their",
    }
    words = [w.lower() for w in name.split()]

    # If all words are common, reject
    if all(w in common_words for w in words):
        return False

    # Reject if starts or ends with very common words (except "The" at start)
    very_common = {
        "and",
        "of",
        "the",
        "in",
        "on",
        "at",
        "to",
        "with",
        "from",
        "by",
        "are",
        "is",
    }
    if word_count > 1:
        # Don't allow ending with very common words
        if words[-1] in very_common:
            return False
        # Don't allow starting with very common words (except "the")
        if words[0] in very_common and words[0] != "the":
            return False

    # For multi-word names, require at least one word with 4+ characters
    if word_count > 1 and not any(len(w) >= 4 for w in words):
        return False

    return True


def get_bandname(texts, pattern, max_tries=10):
    """Try to get a valid bandname, retry if needed"""
    for _ in range(max_tries):
        bandnames = re.findall(
            pattern, texts, re.IGNORECASE
        )  # Case-insensitive matching
        if not bandnames:
            return "The Rejects"  # Fallback if pattern matches nothing
        bandname = random.choice(bandnames)
        prepared = prep_bandname(bandname)
        if is_valid_bandname(prepared):
            return prepared
    # Give up after max_tries, return whatever we got
    return prep_bandname(bandname) if bandnames else "The Rejects"


def is_band_duplicate(bandname):
    """Check if band name is a real band or already claimed

    Returns: (is_duplicate, is_real_band, claimed_by)
    """
    normalized = bandname.lower().strip()

    # Check against real band names
    if normalized in existing_bands:
        return True, True, None  # Real band

    # Check against claimed names in database
    claim = ClaimedBandName.query.filter_by(band_name_lower=normalized).first()
    if claim:
        return True, False, claim.user.username  # Claimed, not a real band

    return False, False, None


@main_bp.route("/", endpoint="index")
def index():
    # Patterns with case-insensitive matching (results get title-cased)
    # Weights roughly match real band name distribution
    patterns = [
        (r"\b[a-z]{4,12}\b", 0.45),  # Single word, 45%
        (r"\b[a-z]+\s+[a-z]+\b", 0.25),  # Two words, 25%
        (r"\bthe\s+\w+s\b", 0.15),  # The [word]s, 15%
        (r"\bthe\s+\w+\b", 0.08),  # The [word], 8%
        (r"\b[a-z]+\s+[a-z]+\s+[a-z]+\b", 0.05),  # Three words, 5%
        (r"\b[a-z]+\s+of\s+[a-z]+\b", 0.02),  # [word] of [word], 2%
    ]

    pattern_list = [p[0] for p in patterns]
    weights = [p[1] for p in patterns]
    pattern = random.choices(pattern_list, weights=weights)[0]

    bandname = get_bandname(text, pattern)

    # Check if duplicate (real band or claimed)
    is_duplicate, is_real_band, claimed_by = is_band_duplicate(bandname)

    # Generate shareable URL for this band name
    shareable_url = url_for('main_bp.band', name=bandname, _external=True)

    return render_template(
        "index.html",
        bandname=bandname,
        is_duplicate=is_duplicate,
        is_real_band=is_real_band,
        claimed_by=claimed_by,
        shareable_url=shareable_url
    )


@main_bp.route("/band", endpoint="band")
def band():
    """Display a specific band name via query parameter"""
    bandname = request.args.get('name', 'The Rejects')

    # Check if duplicate (real band or claimed)
    is_duplicate, is_real_band, claimed_by = is_band_duplicate(bandname)

    # Generate shareable URL for this band name
    shareable_url = url_for('main_bp.band', name=bandname, _external=True)

    return render_template(
        "index.html",
        bandname=bandname,
        is_duplicate=is_duplicate,
        is_real_band=is_real_band,
        claimed_by=claimed_by,
        shareable_url=shareable_url
    )
