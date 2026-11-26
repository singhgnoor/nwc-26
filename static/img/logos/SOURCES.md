# Logo sources

Rebuild these files with `python tools/prepare_logos.py` (dev-only; see `tools/requirements-dev.txt`).

| File | Source | What was done |
|---|---|---|
| `emblem-of-india.webp` | State Emblem of India with the motto सत्यमेव जयते. Wikimedia Commons, `File:Emblem_of_India.svg`: https://upload.wikimedia.org/wikipedia/commons/5/55/Emblem_of_India.svg (public domain, Government of India). Downloaded 26 Nov 2026. | Rendered **unaltered** to a transparent lossless WebP (pixel-identical), 288 px tall. The SVG is 437 KB, too heavy for a 72 px slot. No recolouring, cropping, effects, outline or squashing; the aspect ratio is kept. |
| `mmttp.png` | Malaviya Mission Teacher Training Programme logo, from the programme's official portal: https://mmc.ugc.ac.in/newtheme/img/ugc_logo.png (450 × 106, transparent PNG). Downloaded 26 Nov 2026. | Copied byte for byte. It is the official horizontal lockup (mark + name); it is shown whole, never cropped or redrawn. Swap in a vector if the Dean's office provides one. |
| `iit-ropar-seal.webp` | IIT Ropar seal, `imgaes/iitrpr-logo.svg` in this repository. That file is a 946 × 1039 PNG wrapped in an SVG (not a true vector). | The embedded PNG, resized to 288 px tall (WebP, quality 90). |
| `iit-ropar-seal-white.webp` | Same as above. | White line version for the indigo footer: the artwork is mapped to white and its white paper to transparent. Allowed for the institute's own seal. |

The Ministry of Education / Department of Higher Education lockup is the emblem plus live HTML text ("Ministry of Education", "Department of Higher Education", "Government of India", as in the Figma component `3:10`), so it stays Hindi-ready.
