# Logo Assets

This directory contains the GRID Analyzer logo assets.

## Current Assets

- `wheel-icon.svg` - Primary SVG logo (source file)

## Required Assets (To Generate)

- `favicon.ico` - Multi-size ICO file (16x16, 32x32, 48x48)
- `apple-touch-icon.png` - 180x180 PNG for iOS home screen

## Generation Instructions

### Option 1: Automated Script (Recommended)

```bash
# Install sharp (image processing library)
npm install --save-dev sharp

# Run the generator
node scripts/generate-favicons.js
```

This creates `apple-touch-icon.png` and `favicon-32x32.png`. For `favicon.ico`, convert the PNG using https://convertio.co/png-ico/

### Option 2: Online Tools

1. **Favicon Generator:**
   - Visit https://realfavicongenerator.net/
   - Upload `wheel-icon.svg`
   - Download the generated `favicon.ico`
   - Place it in this directory

2. **Apple Touch Icon:**
   - Visit https://www.favicon-generator.org/ or use ImageMagick online
   - Upload `wheel-icon.svg`
   - Generate 180x180 PNG
   - Save as `apple-touch-icon.png`

### Option 3: ImageMagick (Command Line)

If you have ImageMagick installed:

```bash
# Generate favicon.ico (multi-size)
magick wheel-icon.svg -define icon:auto-resize=16,32,48 favicon.ico

# Generate apple-touch-icon.png (180x180)
magick wheel-icon.svg -resize 180x180 apple-touch-icon.png
```

### Option 4: Inkscape (Command Line)

If you have Inkscape installed:

```bash
# Generate favicon.ico (via PNG conversion)
inkscape wheel-icon.svg --export-filename=favicon-32.png --export-width=32 --export-height=32
# Then use an online ICO converter or ImageMagick to create multi-size ICO

# Generate apple-touch-icon.png
inkscape wheel-icon.svg --export-filename=apple-touch-icon.png --export-width=180 --export-height=180
```

### Option 5: Manual (Design Tools)

1. Open `wheel-icon.svg` in Adobe Illustrator, Figma, or similar
2. Export as PNG at required sizes:
   - 16x16, 32x32, 48x48 for favicon.ico
   - 180x180 for apple-touch-icon.png
3. Use an online ICO converter to combine PNGs into favicon.ico

## Verification

After generating assets, verify:
- `favicon.ico` displays correctly in browser tab
- `apple-touch-icon.png` appears when adding to iOS home screen
- Both files are optimized (small file sizes)

## Notes

- The SVG source (`wheel-icon.svg`) is the master file
- All generated assets should maintain the same visual appearance
- Favicon should be recognizable at small sizes (16x16)
- Apple touch icon should be clear at 180x180
