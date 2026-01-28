# Finnegans Wake Band Name Generator

A Flask web application that generates band names by extracting patterns from James Joyce's *Finnegans Wake*.

Written by Patrick J. Burns, 2.1.19, updated 1.28.26.

## Features

- **Pattern-based extraction**: Uses regex patterns to find band name candidates directly from the text
- **Weighted distribution**: Generates names matching real-world band name patterns (45% single words, 25% two words, 15% "The [X]s", etc.)
- **Case-insensitive matching**: Extracts from Joyce's unconventional capitalization while maintaining variety
- **Capitalization styles**: 99% title case, with rare variations (UPPER, lower, CamelCase)
- **Quality filtering**: Validates names to avoid common words and boring combinations
- **Duplicate detection**: Warns when a generated name matches an existing band from a database of 63,000+ bands
- **Wiki ID filtering**: Excludes non-band entries from duplicate checking
- **Named routes**: Flask routes with named endpoints for easy URL management
- **Shareable URLs**: Each generated band name gets a unique URL for easy sharing
- **Copy to clipboard**: Click the shareable link to copy it to your clipboard
- **Minimalist UI**: Clean design with refresh icon and subtle interactions
- **User accounts**: Email/password and OAuth (Google, GitHub) authentication
- **Band name claims**: Claim up to 5 generated band names as "trading cards"
- **Public gallery**: Browse all claimed band names with pagination
- **Public leaderboard**: See top collectors ranked by claim count

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
uv run flask run --port 5001
```

Visit http://127.0.0.1:5001/ in your browser. Click the refresh icon to generate new band names, or use the shareable link to save and share specific names.

## Configuration

### Environment Variables

Create a `.env` file in the project root (see `.env.example`):

```bash
# Required
SECRET_KEY=your-secret-key-here
FLASK_ENV=development

# Database (optional for dev - defaults to SQLite)
DATABASE_URL=sqlite:///instance/app.db

# OAuth (optional - enables social login)
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret

# Registration toggle (optional - defaults to true)
REGISTRATION_ENABLED=true
```

### OAuth Setup (Optional)

To enable Google and GitHub login:

**Google OAuth:**
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Navigate to APIs & Services > Credentials
4. Create OAuth 2.0 Client ID (Web application)
5. Add authorized redirect URI: `http://localhost:5001/auth/oauth/google/callback`
6. Copy Client ID and Secret to `.env`

**GitHub OAuth:**
1. Go to [GitHub Developer Settings](https://github.com/settings/developers)
2. Create a new OAuth App
3. Set Authorization callback URL: `http://localhost:5001/auth/oauth/github/callback`
4. Copy Client ID and Secret to `.env`

For production, update redirect URIs to your domain (e.g., `https://yourdomain.com/auth/oauth/google/callback`).

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
│   ├── __init__.py          # Flask app factory
│   ├── routes.py            # Main routes (generator, leaderboard, gallery)
│   ├── auth_routes.py       # Authentication routes (login, register, OAuth)
│   ├── user_routes.py       # User routes (dashboard, claims)
│   ├── models.py            # Database models (User, ClaimedBandName)
│   └── templates/
│       ├── base.html        # Base template with navbar
│       ├── index.html       # Band name generator
│       ├── leaderboard.html # Public leaderboard
│       ├── gallery.html     # Public gallery of claims
│       ├── auth/            # Login, register templates
│       └── user/            # Dashboard template
├── static/
│   ├── data/
│   │   └── bands.txt        # 170,000+ band names
│   └── texts/               # 626 Finnegans Wake text files
├── migrations/              # Alembic database migrations
├── tests/                   # Pytest test suite
├── config.py                # Environment configuration
├── app.py                   # Application entry point
└── pyproject.toml          # Project metadata & dependencies
```

## Technical Details

- **Flask 3.0+** with Bootstrap UI
- **Case-insensitive regex** with `re.IGNORECASE` for maximum variety
- **Retry logic** with quality validation (max 10 attempts per generation)
- **In-memory text loading** for fast pattern matching
- **Set-based duplicate checking** for O(1) lookups

## Changelog

### 2026-01-05 - ClaimedBandName Model & Relationships
- Added: ClaimedBandName model for trading card claims system
- Added: User ← many → ClaimedBandName relationship (one-to-many)
- Added: band_name_lower unique constraint (global uniqueness across all users)
- Added: ClaimedBandName.normalize_name() for consistent deduplication
- Changed: User.can_claim now checks actual claimed_bands count < 5
- Infrastructure: Cascade delete (claims removed when user deleted)
- Infrastructure: Indexed band_name_lower for fast duplicate checking

### 2026-01-04 - Database Foundation
- Added: Database configuration with dev/prod/test environments
- Added: User model with OAuth and email/password authentication support
- Added: Database dependencies (flask-sqlalchemy, flask-migrate, flask-login, psycopg2-binary)
- Changed: Configuration supports SQLite (dev) and PostgreSQL (production)
- Infrastructure: Session security, Heroku DATABASE_URL compatibility

### 2026-01-03 - TSV Format with Wikidata IDs
- Added: TSV format (Q-ID + label) for band data with rich metadata support
- Added: LOCAL_XXXXXX IDs for existing 71K non-Wikidata bands
- Added: CLI options --dry-run and --output for script control
- Changed: Converted bands.txt to TSV format (170,471 total bands)
- Changed: Script captures both Wikidata Q-ID and English label
- Changed: Deduplication by Q-ID instead of label text
- Added: Backward compatibility - generates bands.txt from TSV
- Merged: 71,105 existing + 106,382 Wikidata = 170,471 unique bands

### 2026-01-02 - Wikidata Full Dataset Fetching
- Added: Pagination logic to fetch complete Wikidata dataset (103K+ bands)
- Added: Deduplication using lowercase normalization
- Added: Progress bar with tqdm showing batch progress and unique count
- Added: Rate limiting (1 second between requests) for API etiquette
- Changed: Script now fetches all bands instead of 100-record test limit
- Testing: Successfully fetched 103,028 unique bands from Wikidata

### 2026-01-01 - Wikidata Automation Foundation
- Added: Wikidata SPARQL script for automated band name updates
- Added: Comprehensive pytest test suite (8 tests, 48% coverage)
- Added: Dev dependencies for testing and data fetching (pytest, pytest-cov, requests, tqdm)
- Testing: Script successfully fetches 100+ band names from Wikidata endpoint
- Testing: All tests passing with mocked HTTP responses

## Version History

### v0.5.0 (2026-01-28)
- Added public gallery page showing all claimed band names
- Added pagination for gallery (24 items per page)
- Added OAuth setup documentation to README
- Added Gallery link to navbar
- Deployed to production at https://fwbng.exploratoryphilology.org

### v0.4.0 (2026-01-21)
- Added user authentication (email/password + Google/GitHub OAuth)
- Added band name claiming system (max 5 claims per user)
- Added user dashboard showing claimed bands
- Added public leaderboard ranking users by claim count
- Added application factory pattern for better testability
- Added Flask-Migrate for database migrations
- Infrastructure: Blueprint architecture (main, auth, user routes)

### v0.3.0 (2025-12-31)
- Added named routes with Flask `url_for()` for maintainable URL management
- Implemented shareable URLs via `/band?name=` endpoint for indexing band names
- Added copy-to-clipboard functionality for easy link sharing
- Redesigned UI with minimalist refresh icon (UXWing)
- Fixed circular import issue in Flask app initialization
- Configured static folder path for proper asset serving

### v0.2.0 (2025-12-30)
- Added case-insensitive pattern matching
- Implemented capitalization layer with weighted styles
- Enhanced validation to filter low-quality names
- Expanded pattern variety from 5 to 6 different types
- Added duplicate detection with warning alerts
- Filtered wiki IDs from bands database

### v0.1.0 (2019-02-01)
- Initial release with basic pattern matching

## License

Source text: *Finnegans Wake* by James Joyce (public domain)  
Band names database: Compiled from public sources  
Code: See LICENSE file  

## Credits

Written by Patrick J. Burns (v0.2.0-0.5.0 with Claude Opus 4.5). Built with Flask, powered by Joyce's linguistic brilliance.
