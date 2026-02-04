#!/usr/bin/env node
/**
 * Generate CSS Variables from branding.json
 * 
 * This script reads branding.json and generates CSS custom properties
 * that can be included in styles.css, eliminating manual duplication.
 * 
 * Usage: node scripts/generate-css-variables.js
 */

const fs = require('fs');
const path = require('path');

// Read branding.json (single source of truth)
const brandPath = path.join(__dirname, '..', 'branding.json');
const brand = JSON.parse(fs.readFileSync(brandPath, 'utf8'));

// Generate CSS variables
let css = '/* Auto-generated CSS Variables from branding.json */\n';
css += '/* DO NOT EDIT MANUALLY - Run: node scripts/generate-css-variables.js */\n\n';
css += ':root {\n';

// Graphite colors (sort by shade number for consistency)
css += '    /* Graphite Base System */\n';
const graphiteEntries = Object.entries(brand.colors.graphite).sort((a, b) => {
    const numA = parseInt(a[0]);
    const numB = parseInt(b[0]);
    return numA - numB;
});
graphiteEntries.forEach(([shade, value]) => {
    css += `    --graphite-${shade}: ${value};\n`;
});

// Cyan colors (sort by shade number)
css += '\n    /* Electric Cyan Accent System */\n';
const cyanEntries = Object.entries(brand.colors.cyan).sort((a, b) => {
    const numA = parseInt(a[0]);
    const numB = parseInt(b[0]);
    return numA - numB;
});
cyanEntries.forEach(([shade, value]) => {
    css += `    --cyan-${shade}: ${value};\n`;
});

// Amber colors (if exists, sort by shade number)
if (brand.colors.amber) {
    css += '\n    /* Amber Accent System */\n';
    const amberEntries = Object.entries(brand.colors.amber).sort((a, b) => {
        const numA = parseInt(a[0]);
        const numB = parseInt(b[0]);
        return numA - numB;
    });
    amberEntries.forEach(([shade, value]) => {
        css += `    --amber-${shade}: ${value};\n`;
    });
}

// Semantic colors
css += '\n    /* Semantic Colors */\n';
Object.entries(brand.colors.semantic).forEach(([name, value]) => {
    css += `    --${name}: ${value};\n`;
});

// White color
if (brand.colors.white) {
    css += `    --white: ${brand.colors.white};\n`;
}

// Primary color mappings
css += '\n    /* Primary Colors (using Graphite + Cyan) */\n';
css += '    --primary: var(--cyan-500);\n';
css += '    --primary-hover: var(--cyan-400);\n';
css += '    --primary-active: var(--cyan-600);\n';
css += '    --primary-light: var(--cyan-300);\n';
css += '    --primary-dark: var(--cyan-700);\n';

// Background colors
css += '\n    /* Background Colors - Light Theme */\n';
css += '    --bg-primary: var(--graphite-50);\n';
css += '    --bg-secondary: var(--white);\n';
css += '    --bg-tertiary: var(--graphite-100);\n';
css += '    --bg-card: var(--white);\n';
css += '    --bg-overlay: rgba(10, 10, 15, 0.5);\n';

// Text colors
css += '\n    /* Text Colors - Light Theme */\n';
css += '    --text-primary: var(--graphite-900);\n';
css += '    --text-secondary: var(--graphite-600);\n';
css += '    --text-tertiary: var(--graphite-500);\n';
css += '    --text-muted: var(--graphite-400);\n';
css += '    --text-inverse: var(--white);\n';

// Border colors
css += '\n    /* Border Colors */\n';
css += '    --border-primary: var(--graphite-200);\n';
css += '    --border-secondary: var(--graphite-300);\n';
css += '    --border-accent: var(--cyan-500);\n';

// Base colors
css += '\n    /* Base Colors */\n';
css += '    --white: #FFFFFF;\n';
css += '    --black: #000000;\n';

// Legacy support (for gradual migration)
css += '\n    /* Legacy support (for gradual migration) */\n';
css += '    --primary-indigo: var(--cyan-500);\n';
css += '    --primary-indigo-hover: var(--cyan-400);\n';
css += '    --primary-indigo-light: var(--cyan-300);\n';
css += '    --primary-indigo-dark: var(--cyan-700);\n';
css += '    --accent-cyan: var(--cyan-500);\n';
css += '    --accent-emerald: var(--success);\n';
css += '    --accent-amber: var(--warning);\n';
css += '    --accent-rose: var(--error);\n';
css += '    --gray-950: var(--graphite-950);\n';
css += '    --gray-900: var(--graphite-900);\n';
css += '    --gray-800: var(--graphite-800);\n';
css += '    --gray-700: var(--graphite-700);\n';
css += '    --gray-600: var(--graphite-600);\n';
css += '    --gray-500: var(--graphite-500);\n';
css += '    --gray-400: var(--graphite-400);\n';
css += '    --gray-300: var(--graphite-300);\n';
css += '    --gray-200: var(--graphite-200);\n';
css += '    --gray-100: var(--graphite-100);\n';
css += '    --gray-50: var(--graphite-50);\n';

// Typography (handle nested structure in branding.json)
css += '\n    /* Typography */\n';
if (brand.typography && brand.typography.display) {
    // branding.json has nested structure: typography.display.family
    css += `    --font-display: ${brand.typography.display.family};\n`;
    css += `    --font-body: ${brand.typography.body.family};\n`;
    css += `    --font-mono: ${brand.typography.mono.family};\n`;
} else if (brand.fonts) {
    // Fallback for flat structure
    css += `    --font-display: '${brand.fonts.display}', -apple-system, BlinkMacSystemFont, sans-serif;\n`;
    css += `    --font-body: '${brand.fonts.body}', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;\n`;
    css += `    --font-mono: '${brand.fonts.mono}', 'Fira Code', 'Monaco', monospace;\n`;
}

// Shadows
css += '\n    /* Shadows with Cyan Glow */\n';
css += '    --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);\n';
css += '    --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);\n';
css += '    --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);\n';
css += '    --shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);\n';
css += '    --shadow-glow: 0 0 40px rgba(0, 217, 255, 0.3);\n';
css += '    --shadow-glow-strong: 0 0 60px rgba(0, 217, 255, 0.4);\n';
css += '    --shadow-cyan: 0 4px 20px rgba(0, 217, 255, 0.25);\n';

css += '}\n';

// Output to file
const outputPath = path.join(__dirname, '..', 'css-variables.css');
fs.writeFileSync(outputPath, css, 'utf8');

console.log('✅ CSS variables generated successfully!');
console.log(`📄 Output: ${outputPath}`);
console.log('\n💡 Next steps:');
console.log('   1. Review css-variables.css');
console.log('   2. Replace the :root section in styles.css with the generated variables');
console.log('   3. Run this script whenever branding.json is updated');
