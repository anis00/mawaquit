# Mawaquit Web

Web version of the Mawaquit Islamic prayer times calculator with isochrone visualization.

## Features

- **Prayer Times Calculation**: Accurate prayer times using multiple calculation methods (MWL, ISNA, Egypt, Makkah, Karachi, Tehran, Jafari)
- **Interactive Map**: Leaflet-based map with country boundaries from GADM
- **Isochrone Visualization**: Colored bands showing areas with the same prayer time
- **33 Countries Supported**: From Europe, Middle East, Africa, Asia, and Americas
- **Responsive Design**: Works on desktop and mobile devices

## Usage

1. Select a country from the dropdown
2. Choose your preferred calculation method
3. Set the date (defaults to today)
4. Click anywhere on the map to see prayer times for that location
5. Click a prayer button (Fajr, Dhuhr, Asr, Maghrib, Isha) to display isochrone curves

## Deployment to GitHub Pages

### Option 1: Subtree Push
```bash
git subtree push --prefix web origin gh-pages
```

### Option 2: Manual Deployment
1. Create a `gh-pages` branch
2. Copy contents of `web/` folder to the root
3. Push to GitHub

### Option 3: GitHub Actions
Create `.github/workflows/deploy.yml`:
```yaml
name: Deploy to GitHub Pages

on:
  push:
    branches: [master]
    paths: ['web/**']

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Deploy
        uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./web
```

## Local Development

Simply serve the `web/` directory with any static file server:

```bash
# Using Python
cd web && python -m http.server 8000

# Using Node.js
npx serve web

# Using PHP
cd web && php -S localhost:8000
```

Then open http://localhost:8000 in your browser.

## File Structure

```
web/
├── index.html              # Main HTML page
├── css/
│   └── custom.css          # Custom styles (Tailwind complement)
├── js/
│   ├── app.js              # Main application orchestration
│   ├── praytimes.js        # Prayer times calculator
│   ├── isochrones.js       # Isochrone interface
│   ├── isochrones.worker.js # Web Worker for calculations
│   ├── map.js              # Leaflet map management
│   ├── ui.js               # UI interactions
│   ├── data.js             # Data loading and caching
│   └── utils.js            # Utility functions
├── data/
│   └── countries.json      # Country metadata
└── README.md               # This file
```

## Technologies Used

- **Leaflet.js** - Interactive maps
- **Tailwind CSS** - Styling (via CDN)
- **Web Workers** - Non-blocking isochrone calculations
- **GADM Data** - Geographic boundaries (loaded from geodata.ucdavis.edu)

## Browser Compatibility

- Chrome 70+
- Firefox 65+
- Safari 12+
- Edge 79+

## Calculation Methods

| Method | Fajr Angle | Isha Angle |
|--------|-----------|------------|
| Muslim World League (MWL) | 18° | 17° |
| Islamic Society of North America (ISNA) | 15° | 15° |
| Egyptian General Authority | 19.5° | 17.5° |
| Umm Al-Qura, Makkah | 18.5° | 90 min after Maghrib |
| University of Islamic Sciences, Karachi | 18° | 18° |
| Institute of Geophysics, Tehran | 17.7° | 14° |
| Shia Ithna-Ashari, Qum (Jafari) | 16° | 14° |

## Credits

- Prayer times algorithm based on [PrayTimes.org](http://praytimes.org/)
- Geographic data from [GADM](https://gadm.org/)
- Map tiles from [OpenStreetMap](https://www.openstreetmap.org/)
