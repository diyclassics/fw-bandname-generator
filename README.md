# Finnegans Wake Band Name Generator

A Flask web application that generates band names by extracting patterns from James Joyce's *Finnegans Wake*.

## Features

- **Pattern-based extraction**: Uses regex patterns to find band name candidates directly from the text
- **Weighted distribution**: Generates names matching real-world band name patterns (45% single words, 25% two words, 15% "The [X]s", etc.)
- **Case-insensitive matching**: Extracts from Joyce's unconventional capitalization while maintaining variety
- **Capitalization styles**: 99% title case, with rare variations (UPPER, lower, CamelCase)
- **Quality filtering**: Validates names to avoid common words and boring combinations
- **Duplicate detection**: Warns when a generated name matches an existing band from a database of 63,000+ bands
- **Wiki ID filtering**: Excludes non-band entries from duplicate checking

## Installation

Requires Python 3.11+

```bash
# Install dependencies using uv
uv sync

# Or install with pip
pip install -r requirements.txt  # if using traditional pip
```

## Usage

Run the Flask development server:

```bash
uv run python app.py
```

Visit http://127.0.0.1:5001/ in your browser. Refresh to generate new band names.

## How It Works

### Pattern Matching

The generator uses case-insensitive regex patterns weighted by real band name distribution:

- **Single words** (45%): `\b[a-z]{4,12}\b` - Examples: *Umwalloped*, *Gandon*, *Futuerism*
- **Two words** (25%): `\b[a-z]+\s+[a-z]+\b` - Examples: *Ruddled Cinnabar*, *Bigdud Dadder*
- **The [word]s** (15%): `\bthe\s+\w+s\b` - Examples: *The Brividies*, *The Gripes*
- **The [word]** (8%): `\bthe\s+\w+\b` - Examples: *The Laneway*, *The Younging*
- **Three words** (5%): `\b[a-z]+\s+[a-z]+\s+[a-z]+\b` - Example: *Shotland to Guinness*
- **[word] of [word]** (2%): `\b[a-z]+\s+of\s+[a-z]+\b` - Example: *Frocks of Redferns*

### Quality Filtering

Names are validated to ensure:
- Length between 3-50 characters
- 1-4 words maximum
- Not entirely composed of common words
- Multi-word names don't start/end with very common words (except "The")
- Multi-word names include at least one substantial word (4+ characters)

### Capitalization Layer

After extraction, names receive capitalization based on real band distributions:
- **99.0%** Title Case (*The Brividies*)
- **0.1%** UPPERCASE (*UMWALLOPED*)
- **0.1%** lowercase (*gandon*)
- **0.1%** CamelCase (*BigdudDadder*)

## Project Structure

```
fw-bandname-generator/
├── app/
│   ├── __init__.py          # Flask app initialization
│   ├── routes.py            # Main application logic & patterns
│   └── templates/
│       └── index.html       # Bootstrap-based UI
├── static/
│   ├── data/
│   │   └── bands.txt        # 71,105 existing band names
│   └── texts/               # 626 Finnegans Wake text files
├── app.py                   # Application entry point
└── pyproject.toml          # Project metadata & dependencies
```

## Technical Details

- **Flask 3.0+** with Bootstrap UI
- **Case-insensitive regex** with `re.IGNORECASE` for maximum variety
- **Retry logic** with quality validation (max 10 attempts per generation)
- **In-memory text loading** for fast pattern matching
- **Set-based duplicate checking** for O(1) lookups

## Version History

### v0.2.0
- Added case-insensitive pattern matching
- Implemented capitalization layer with weighted styles
- Enhanced validation to filter low-quality names
- Expanded pattern variety from 5 to 6 different types
- Added duplicate detection with warning alerts
- Filtered wiki IDs from bands database

### v0.1.0
- Initial release with basic pattern matching

## License

Source text: *Finnegans Wake* by James Joyce (public domain)
Band names database: Compiled from public sources
Code: See LICENSE file

## Credits

Built with Flask, powered by Joyce's linguistic brilliance.
