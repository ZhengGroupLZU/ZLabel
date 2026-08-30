# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.5] - 2026-08-29

### Added

- Theme switching: Auto / Light / Dark with persisted `theme_mode`
  - Auto mode follows the OS `colorScheme` and reacts to changes
  - Fusion style with light/dark palettes and canvas background sync

### Changed

- Removed the multi-level CPU display pyramid
  - Canvas now keeps a single full-resolution display texture (capped at 8192)
  - GPU mipmaps handle zoomed-out filtering instead of CPU level switching
  - Display settings: `display_max_side` default raised to 8192, `pyramid_levels` removed
- Updated image performance benchmark to measure single display build / texture upload

## [0.3.4] - 2026-08-29

### Added

- GPU-accelerated canvas rendering via a custom `GLImageItem`:
  - Persistent `QOpenGLTexture` uploaded per pyramid level, no per-frame CPU `QImage` rebuild
  - RGB / grayscale / RGBA compact texture formats
  - Automatic mipmap generation for smooth zoomed-out quality
  - Safe RGB/R8 uploads for non-4-byte-aligned pyramid widths
  - QPainter / QImage fallback for offscreen, export and software rendering
- Standalone image performance benchmark: `benchmarks/image_performance.py`
  - Canvas pan/zoom FPS
  - `setImage()` FPS for `ImageItem` / `RawImageWidget` / `RawImageGLWidget`
  - Pyramid build, level-switch, `ImageItem.render()` and GL texture-upload timings
- Asynchronous `ZPrepareImageWorker` for already-loaded images, avoiding UI-thread pyramid builds
- Settings toggle to enable/disable GL mipmap anti-aliasing
- Build scripts:
  - cx-Freeze build now excludes unused packages and prunes runtime-unnecessary files
  - Nuitka build produces a portable `-green.7z` and an Inno Setup `-installer.exe`
  - Nuitka uses `--nofollow-import-to` to keep unused modules out of `zlabel.exe`
  - Both build paths use `resources/icons/logo.ico`
- Dependency cleanup: `rich` moved to dev dependencies, `imageio` and PyInstaller-related files removed
- Shortcut adjustment: `G` groups instances, `Ctrl+G` merges shapes
- Settings toggle to enable/disable GL mipmap anti-aliasing
- GLImageItem unit tests and performance regression coverage

### Changed

- Canvas image pipeline switched to `axisOrder="row-major"`:
  - Row-major, C-contiguous display pyramids
  - Removed runtime `rot90` / `flipud` copies
  - Disabled `ImageItem` built-in auto-downsampling to avoid double CPU downsample
- Default display pyramid levels raised from 3 to 5
- Higher-resolution top pyramid level (up to the full image or 8192 long edge)
- `set_rgb()` / pyramid activation now uploads the display array once per image load
- README documents the new performance settings and benchmark usage

### Fixed

- Fixed a crash when uploading RGB/R8 textures with odd row widths
- Fixed a triangular gap in the GL image quad by drawing two explicit `GL_TRIANGLES`
- Fixed a `TypeError` from the delayed pyramid-level timer after the canvas is closed

## [0.3.3] - 2026-08-28

### Added

- Circular magnifier overlay for the annotation canvas
- Appearance / performance settings tab with color pickers, display max side and magnifier options
- Settings split into Application / Remote / Inference tabs
- Dock group toggle actions and equal-height right docks
- Fullscreen toggle (`F11`)
- About dialog showing version, license and disclaimer
- Delete hovered polygon vertex with `Backspace`
- Cross-platform CI build and test workflow
- Async image loading, instance bbox rendering and batch bbox rebuilds
- Large-image display pyramid, timeline thumbnail cache + LRU, drag auto-scroll
- SAM dish-crop prompt mapping

### Changed

- Use dot cursor while drawing polygons
- Batch UI rebuilds during group/merge operations
- Refresh translation sources

### Fixed

- Box-select / label sync issues
- Remove unused DLLs from builds
- Multiprocess pool bootstrap for frozen builds

## [0.3.0] - 2026-08-19

### Added

- Seed-germination workflow:
  - Per-frame instance IDs and timeline tracking
  - Instance status labels and merging / splitting
  - Copy previous frame with dish alignment
- SAM3 local inference and in-process MNN inference backend
- WeChat OCR integration for rectangle timestamp extraction
- COCO / Ultralytics YOLO export dialog
- Keypoint annotation with dynamic point scaling
- Fully-local storage mode and remote mode
- GUI test suite with offscreen Qt
- Polygon merge, Catmull-Rom smoothing, random task selection
- Chinese / English UI

### Changed

- Replaced `poe` with `uv` project scripts
- Switched packaging to `uv_build` + cx_Freeze / Inno Setup
- Moved local inference away from bundled ONNX models to MNN model files

### Fixed

- Rotated rectangle prompt bbox mapping
- Canvas save / `Ctrl+S` flow
- Label selection when clicking canvas objects

## [0.2.0] - 2025-11-13

### Added

- Project import / export
- Window state and geometry persistence
- Number keys `1` – `9` for quick label selection
- Dialog shortcuts
- Random task selection
- Language switching
- Docks show / hide / restore
- cx_Freeze + Inno Setup packaging

### Changed

- Switched build system to `uv`
- Moved settings storage into `~/.zlabel`

### Fixed

- Rectangle handle crashes
- Nuitka / frozen build issues
- Project directory and settings path handling
