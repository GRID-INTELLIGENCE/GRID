#!/usr/bin/env node
/**
 * Favicon Generator
 *
 * Generates favicon.ico and apple-touch-icon.png from wheel-icon.svg
 *
 * Usage: node scripts/generate-favicons.js
 *
 * Requirements: npm install sharp
 */

const fs = require('fs');
const path = require('path');

async function generateFavicons() {
    try {
        // Try to require sharp
        let sharp;
        try {
            sharp = require('sharp');
        } catch (err) {
            console.error('❌ Error: sharp package not installed');
            console.log('\n📦 Install sharp first:');
            console.log('   npm install --save-dev sharp');
            console.log('\n💡 Or use one of the manual methods in assets/logo/README.md');
            process.exit(1);
        }

        const logoDir = path.join(__dirname, '..', 'assets', 'logo');
        const svgPath = path.join(logoDir, 'wheel-icon.svg');

        if (!fs.existsSync(svgPath)) {
            console.error(`❌ Error: wheel-icon.svg not found at ${svgPath}`);
            process.exit(1);
        }

        console.log('🎨 Generating favicon assets from wheel-icon.svg...\n');

        // Generate apple-touch-icon.png (180x180)
        console.log('⏳ Generating apple-touch-icon.png (180x180)...');
        await sharp(svgPath)
            .resize(180, 180)
            .png()
            .toFile(path.join(logoDir, 'apple-touch-icon.png'));
        console.log('✅ apple-touch-icon.png created');

        // Generate favicon.png (32x32) - we'll use this for the ICO
        console.log('⏳ Generating favicon-32x32.png...');
        await sharp(svgPath)
            .resize(32, 32)
            .png()
            .toFile(path.join(logoDir, 'favicon-32x32.png'));
        console.log('✅ favicon-32x32.png created');

        // Generate additional sizes for favicon
        console.log('⏳ Generating favicon-16x16.png...');
        await sharp(svgPath)
            .resize(16, 16)
            .png()
            .toFile(path.join(logoDir, 'favicon-16x16.png'));
        console.log('✅ favicon-16x16.png created');

        console.log('⏳ Generating favicon-48x48.png...');
        await sharp(svgPath)
            .resize(48, 48)
            .png()
            .toFile(path.join(logoDir, 'favicon-48x48.png'));
        console.log('✅ favicon-48x48.png created');

        // Note about .ico generation
        console.log('\n📝 For favicon.ico, use one of these methods:');
        console.log('   1. Online: https://convertio.co/png-ico/ (upload favicon-32x32.png)');
        console.log('   2. Online: https://realfavicongenerator.net/ (upload wheel-icon.svg)');
        console.log('   Note: The existing favicon.ico was generated previously and is still valid.');

        console.log('\n✨ Done! Check assets/logo/ directory');

    } catch (error) {
        console.error('❌ Error generating favicons:', error.message);
        process.exit(1);
    }
}

generateFavicons();
