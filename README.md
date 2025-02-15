```markdown
# TraktHub

A Python package and CLI tool to scrape and retrieve data from [Trakt.tv](https://trakt.tv/). TraktHub allows you to fetch trending, popular, and anticipated movies/shows, check box office stats, and query detailed information about titles or people.

---

## Features

- **Retrieve Data**:
  - Trending movies/shows.
  - Popular and anticipated titles.
  - Current box office statistics.
  - Calendar events (e.g., premieres, finales).
  - Detailed metadata for movies, shows, and people.
- **Check Status**:
  - Determine if a title is trending, popular, or anticipated.
- **CLI Integration**:
  - Run commands directly from the terminal.
  - Verbose output mode for debugging.

---

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/trakthub.git
   cd trakthub
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   
**Dependencies**:  
- `aiohttp`==3.9.0b0
- `async_lru`==2.0.4
- `beautifulsoup4`==4.13.3
- `rapidfuzz`==3.3.1

---

## Usage

### CLI Commands

#### Get Data
| Command                | Description                              | Example                              |
|------------------------|------------------------------------------|--------------------------------------|
| `get-trending`         | Fetch trending movies/shows.             | `get-trending --tshows`              |
| `get-popular`          | Fetch popular movies/shows.              | `get-popular --pmovies`              |
| `get-anticipated`      | Fetch anticipated movies/shows.          | `get-anticipated --ashows`           |
| `get-boxoffice`        | Fetch current box office movies.         | `get-boxoffice`                      |

#### Check Status
| Command                | Description                              | Example                              |
|------------------------|------------------------------------------|--------------------------------------|
| `is-trending`          | Check if a title is trending.            | `is-trending -q "Inception" -c movies` |
| `is-popular`           | Check if a title is popular.             | `is-popular -q "Breaking Bad" -c shows` |
| `is-anticipated`       | Check if a title is anticipated.         | `is-anticipated -q "Dune 2" -c movies` |

#### General Options
- `--verbose`: Enable detailed output.
- `--query` / `-q`: Specify a title or person to query.
- `--category` / `-c`: Specify category (`movies`, `shows`, `people`, `calendars`).

### Python API

```python
from trakthub import TraktHub

# Fetch trending movies
trending_movies = TraktHub(category="movies").track_hub(section="trending")

# Check if "Inception" is popular
is_popular = TraktHub(query="Inception", category="movies").is_popular()

# Get detailed info for a show
show_details = TraktHub(query="Breaking Bad", category="shows").search()
```

---

## Examples

### CLI Output Examples
```bash
$ get-trending --tmovies --verbose

~ Trakt.tv has been successfully accessed and the data has been retrieved.
~ Formatting the data for display...
~ Creating a formatted display for ''.
~ This may take a few seconds...
~ The formatted data will now be displayed.


----------------------------------------------------------------

-------------------TraktHub - Trending Movies-------------------

----------------------------------------------------------------
Time Now: 02/15/2025 01:28 PM

1-The Gorge (2025)
     • Watch Count: 328
2-Undercover (2024)
     • Watch Count: 96
3-Flight Risk (2025)
     • Watch Count: 92
...
```

```bash
$ is-trending -q "Inception" -c movies
False
```

```bash

$ get-boxoffice

----------------------------------------------------------------

------------------TraktHub - Current Boxoffice------------------

----------------------------------------------------------------
Time Now: 02/15/2025 01:40 PM

1-Dog Man (2025)
     • Total Budget: $14,000,000
2-Heart Eyes (2025)
     • Total Budget: $8,500,000
3-Love Hurts (2025)
     • Total Budget: $5,800,000

```


### Python Output Example
```python
{
    "Time Now": "02/15/2025 01:28 PM",
    "Movies": {
        "The Gorge (2025)": {
            "Watch Count": 328
        },
        "Undercover (2024)": {
            "Watch Count": 96
        },
        "Flight Risk (2025)": {
            "Watch Count": 92
        },
        ...
    }
}
```





---

## Contributing

Contributions are welcome!  
1. Fork the repository.  
2. Create a feature branch: `git checkout -b feature/new-feature`.  
3. Commit changes: `git commit -m "Add new feature"`.  
4. Push to the branch: `git push origin feature/new-feature`.  
5. Submit a pull request.

---

## License

MIT License. See [LICENSE](LICENSE) for details.
```