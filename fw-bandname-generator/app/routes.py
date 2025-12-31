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
    existing_bands = {line.strip().lower() for line in f}

def remove_punctuation(s):
    punctuation ="\"#$%&\'()*+,-/:;<=>@[\]^_`{|}~.?!«»—"
    translator = str.maketrans({key: " " for key in punctuation})
    s = s.translate(translator)
    return s

def prep_bandname(word):
    word = remove_punctuation(word)
    return titlecase(word.lower())

def get_bandname(texts, pattern):
    bandnames = re.findall(pattern, texts)
    bandname = random.choice(bandnames)
    return prep_bandname(bandname)

@app.route('/')
def return_word():
    patterns = [r"\b(?!the)\w\w\w+\b",
                r'\bThe\s+\w+s\b',
                r'\bThe\s+\w+ed\b',
                r'\bThe\s+\w+\b',
                r'\b\w+\s+of\s+(?!a|the|my|your|his|hers|its|our|their)\w+\b']
    pattern = random.choices(patterns, weights=[.05, .8, .05, .05, .05])
    bandname = get_bandname(text, pattern[0])

    is_duplicate = bandname.lower() in existing_bands

    return render_template('index.html', bandname=bandname, is_duplicate=is_duplicate)
