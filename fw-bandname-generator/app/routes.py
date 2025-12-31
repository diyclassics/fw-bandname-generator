from app import app
from flask import Flask, render_template, flash


import os
import random

import re

from titlecase import titlecase

TEXTPATH = 'static/texts'
BANDSPATH = 'static/data/bands.txt'

textfiles = [file for file in os.listdir(TEXTPATH) if file.endswith('.txt')]

texts = []

for textfile in textfiles:
    with open(TEXTPATH + '/' + textfile, 'r') as f:
        texts.append(f.read())

text = ' '.join(texts)
text = re.sub(r'- \n', '', text)

with open(BANDSPATH, 'r') as f:
    existing_bands = {
        line.strip().lower() for line in f
        if line.strip() and not re.match(r'^Q\d+$', line.strip())
    }

def remove_punctuation(s):
    punctuation ="\"#$%&\'()*+,-/:;<=>@[\]^_`{|}~.?!«»—"
    translator = str.maketrans({key: " " for key in punctuation})
    s = s.translate(translator)
    return s

def prep_bandname(word):
    word = remove_punctuation(word)
    return titlecase(word.lower())

def is_valid_bandname(name):
    """Check if band name meets basic quality criteria"""
    word_count = len(name.split())
    return 1 <= word_count <= 4 and 3 <= len(name) <= 50

def get_bandname(texts, pattern, max_tries=10):
    """Try to get a valid bandname, retry if needed"""
    for _ in range(max_tries):
        bandnames = re.findall(pattern, texts)
        if not bandnames:
            return "The Rejects"  # Fallback if pattern matches nothing
        bandname = random.choice(bandnames)
        prepared = prep_bandname(bandname)
        if is_valid_bandname(prepared):
            return prepared
    # Give up after max_tries, return whatever we got
    return prep_bandname(bandname) if bandnames else "The Rejects"

@app.route('/')
def return_word():
    # Patterns with weights matching real band name distribution
    patterns = [
        (r'\b[A-Z][a-z]{3,12}\b', 0.45),                           # Single word, 45%
        (r'\b[A-Z]\w+\s+[A-Z]\w+\b', 0.23),                       # Two words, 23%
        (r'\bThe\s+[A-Z]\w+s\b', 0.18),                            # The [Word]s, 18%
        (r'\bThe\s+[A-Z]\w+\b', 0.08),                             # The [Word], 8%
        (r'\b[A-Z]\w+\s+[A-Z]\w+\s+[A-Z]\w+\b', 0.04),           # Three words, 4%
        (r'\b[A-Z]\w+\s+of\s+[A-Z]\w+\b', 0.02),                  # [Word] of [Word], 2%
    ]

    pattern_list = [p[0] for p in patterns]
    weights = [p[1] for p in patterns]
    pattern = random.choices(pattern_list, weights=weights)[0]

    bandname = get_bandname(text, pattern)

    is_duplicate = bandname.lower() in existing_bands

    return render_template('index.html', bandname=bandname, is_duplicate=is_duplicate)
