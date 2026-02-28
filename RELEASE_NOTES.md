# Release Notes

## Version 0.4.1 — 28 Feb 2026

### ✨ Improvements

- **Version display in UI** - Application version is now shown in the interface
- **Fix project name** - Updated branding across all UI elements
- **Static asset caching** - Added no-cache headers to prevent stale assets after updates

---

## Version 0.4.0 — 27 Feb 2026

### 🎉 Major Features

**Non-GoPro Video Support**

Full support for non-GoPro video files with external GPS data.

- **MOV format support** - Upload and render `.mov` video files alongside existing formats
- **External GPX/FIT fallback** - Automatically use external GPS data when video has no embedded telemetry
- **Video rotation handling** - Detect and apply correct rotation for videos with non-standard orientation
- **Order-independent uploads** - Upload GPX/FIT file first, then video — the session is reused instead of creating a new one

### 🐞 Fixes

- Fixed pillarbox temp file timestamp being set to current time, breaking GPS time alignment with `--video-time-start file-modified`
- Fixed pillarbox/letterbox preview now uses fit-to-canvas instead of stretch

---

## Version 0.3.0 — 04 Feb 2026

### 🎉 Major Features

**GPS Quality Analysis**

Automatic GPS signal quality analysis for uploaded videos with visual feedback and warnings before rendering.

- **Quality scoring** - Analyzes GPS lock rate and DOP (Dilution of Precision) values to classify signal quality as Excellent, Good, OK, Poor, or No Signal
- **Quality indicator in header** - Compact badge shows current GPS quality with detailed tooltip
- **Quality distribution card** - Visual breakdown of GPS point quality with statistics (DOP average, lock rate, usable percentage)
- **Pre-render warnings** - Modal warns before rendering files with poor GPS quality, explaining potential overlay issues
- **Batch quality check** - Table view of GPS quality for all files in batch render, with option to skip files with issues

### 🆕 New

- **Overwrite confirmation dialog** - Shows list of existing files before batch render with Skip Existing option

### ✨ Improvements

- GPS filter settings (DOP max, speed max) added to rendering parameters

---

## Version 0.2.0

Initial feature release with GPS filter settings.

---

## Version 0.1.0

Initial release.
