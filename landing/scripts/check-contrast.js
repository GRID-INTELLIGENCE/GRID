#!/usr/bin/env node
/**
 * Color Contrast Checker
 * 
 * Validates color contrast ratios for WCAG AA compliance.
 * 
 * Usage: node scripts/check-contrast.js
 */

const fs = require('fs');
const path = require('path');

// Helper: Convert hex to RGB
function hexToRgb(hex) {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result ? {
        r: parseInt(result[1], 16),
        g: parseInt(result[2], 16),
        b: parseInt(result[3], 16)
    } : null;
}

// Helper: Calculate relative luminance
function getLuminance(rgb) {
    const [r, g, b] = [rgb.r, rgb.g, rgb.b].map(val => {
        val = val / 255;
        return val <= 0.03928 ? val / 12.92 : Math.pow((val + 0.055) / 1.055, 2.4);
    });
    return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

// Helper: Calculate contrast ratio
function getContrastRatio(color1, color2) {
    const lum1 = getLuminance(hexToRgb(color1));
    const lum2 = getLuminance(hexToRgb(color2));
    const lighter = Math.max(lum1, lum2);
    const darker = Math.min(lum1, lum2);
    return (lighter + 0.05) / (darker + 0.05);
}

// Read branding.json
const brandPath = path.join(__dirname, '..', 'branding.json');
let brand;
try {
    brand = JSON.parse(fs.readFileSync(brandPath, 'utf8'));
} catch (error) {
    console.error(`Failed to read branding.json: ${error.message}`);
    process.exit(1);
}

console.log('✓ Checking color contrast ratios for WCAG AA compliance...\n');

const colors = brand.colors;
let failures = [];
let passes = [];

// Common text/background combinations to check
const combinations = [
    // Light theme combinations
    { name: 'Text on light background', fg: colors.graphite?.[900], bg: colors.graphite?.[50] },
    { name: 'Secondary text on light', fg: colors.graphite?.[600], bg: colors.graphite?.[50] },
    { name: 'Text on white', fg: colors.graphite?.[900], bg: colors.white },

    // Dark theme combinations
    { name: 'Text on dark background', fg: colors.graphite?.[50], bg: colors.graphite?.[900] },
    { name: 'Text on darkest', fg: colors.graphite?.[50], bg: colors.graphite?.[950] },
    { name: 'Cyan accent on dark', fg: colors.cyan?.[500], bg: colors.graphite?.[900] },

    // Semantic colors (these should meet WCAG AA)
    { name: 'Success text on light', fg: colors.semantic?.success, bg: colors.graphite?.[50] },
    { name: 'Error text on light', fg: colors.semantic?.error, bg: colors.graphite?.[50] },
    { name: 'Warning text on light', fg: colors.semantic?.warning, bg: colors.graphite?.[50] },
    { name: 'Info text on light', fg: colors.semantic?.info, bg: colors.graphite?.[50] },
];

// WCAG AA requirements
const NORMAL_TEXT_MIN = 4.5; // Normal text (smaller than 18pt or 14pt bold)
const LARGE_TEXT_MIN = 3.0;  // Large text (18pt+ or 14pt+ bold)

combinations.forEach(combo => {
    if (!combo.fg || !combo.bg) {
        return; // Skip if colors not defined
    }
    
    const ratio = getContrastRatio(combo.fg, combo.bg);
    const passesNormal = ratio >= NORMAL_TEXT_MIN;
    const passesLarge = ratio >= LARGE_TEXT_MIN;
    
    if (passesNormal) {
        passes.push({
            name: combo.name,
            ratio: ratio.toFixed(2),
            status: 'PASS (normal & large)'
        });
    } else if (passesLarge) {
        passes.push({
            name: combo.name,
            ratio: ratio.toFixed(2),
            status: 'PASS (large text only)'
        });
        failures.push({
            name: combo.name,
            ratio: ratio.toFixed(2),
            required: NORMAL_TEXT_MIN,
            fg: combo.fg,
            bg: combo.bg,
            issue: 'Fails normal text requirement'
        });
    } else {
        failures.push({
            name: combo.name,
            ratio: ratio.toFixed(2),
            required: LARGE_TEXT_MIN,
            fg: combo.fg,
            bg: combo.bg,
            issue: 'Fails both normal and large text requirements'
        });
    }
});

// Report results
console.log('=== Contrast Check Results ===\n');

if (passes.length > 0) {
    console.log('✅ Passing combinations:');
    passes.forEach(pass => {
        console.log(`  ✓ ${pass.name}: ${pass.ratio}:1 (${pass.status})`);
    });
    console.log('');
}

if (failures.length > 0) {
    console.log('❌ Failing combinations:');
    failures.forEach(fail => {
        console.log(`  ✗ ${fail.name}`);
        console.log(`    Ratio: ${fail.ratio}:1 (required: ${fail.required}:1)`);
        console.log(`    Colors: ${fail.fg} on ${fail.bg}`);
        console.log(`    Issue: ${fail.issue}\n`);
    });
    process.exit(1);
} else {
    console.log('✅ All color combinations meet WCAG AA standards!');
    process.exit(0);
}
