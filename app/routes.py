from app import app
from flask import Flask, render_template, flash


import os
import random

import re

TEXTPATH = 'static/texts'

textfiles = [file for file in os.listdir(TEXTPATH) if file.endswith('.txt')]

texts = []

for textfile in textfiles:
    with open(TEXTPATH + '/' + textfile, 'r') as f:
        texts.append(f.read())

text = ' '.join(texts)
text = re.sub(r'- \n', '', text)

def remove_punctuation(s):
    punctuation ="\"#$%&\'()*+,-/:;<=>@[\]^_`{|}~.?!«»—"
    translator = str.maketrans({key: " " for key in punctuation})
    s = s.translate(translator)
    return s

def prep_bandname(word):
    word = remove_punctuation(word)
    return word.title()

def get_bandname(texts, pattern):
    bandnames = re.findall(pattern, texts)
    bandname = random.choice(bandnames)
    return prep_bandname(bandname)

@app.route('/')
def return_word():
    patterns = [r"\b\w+\b",
                r'\bThe\s+\w+s\b']
    pattern = random.choice(patterns)
    pattern = r'\bThe\s+\w+s\b' # Override for now
    return render_template('index.html', bandname = get_bandname(text, pattern))
