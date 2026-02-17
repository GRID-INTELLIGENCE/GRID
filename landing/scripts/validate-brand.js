#!/usr/bin/env node
/**
 * Brand Validation Script
 * 
 * Validates brand configuration consistency and checks for hardcoded values.
 * 
 * Usage: node scripts/validate-brand.js
 */

const fs = require('fs');
const path = require('path');

let errors = [];
let warnings = [];

// Read branding.json
const brandPath = path.join(__dirname, '..', 'branding.json');
let brand;
try {
    brand = JSON.parse(fs.readFileSync(brandPath, 'utf8'));
} catch (error) {
    errors.push(`Failed to read branding.json: ${error.message}`);
    process.exit(1);
}

// 1. Validate branding.json schema
console.log('✓ Validating branding.json schema...');
const requiredFields = [
    'brand.name',
    'brand.shortName',
    'colors.graphite',
    'colors.cyan',
    'typography.display',
    'typography.body',
    'assets.logo.icon'
];

requiredFields.forEach(field => {
    const keys = field.split('.');
    let value = brand;
    for (const key of keys) {
        value = value?.[key];
        if (value === undefined) {
            errors.push(`Missing required field: ${field}`);
            break;
        }
    }
});

// 2. Check for hardcoded hex codes in styles.css
console.log('✓ Checking for hardcoded hex codes in styles.css...');
const stylesPath = path.join(__dirname, '..', 'styles.css');
if (fs.existsSync(stylesPath)) {
    const stylesContent = fs.readFileSync(stylesPath, 'utf8');
    // Match hex codes (but exclude :root definitions which are the variable definitions themselves)
    const hexPattern = /#[0-9A-Fa-f]{6}|#[0-9A-Fa-f]{3}/g;
    const matches = stylesContent.match(hexPattern);
    
    if (matches) {
        // Filter out :root section (variable definitions are OK)
        const rootSection = stylesContent.match(/:root\s*\{[^}]*\}/s);
        const rootHexCodes = rootSection ? rootSection[0].match(hexPattern) || [] : [];
        
        // Find hex codes outside :root
        const lines = stylesContent.split('\n');
        lines.forEach((line, index) => {
            if (line.includes(':root') || line.trim().startsWith('--')) {
                return; // Skip :root section
            }
            const lineMatches = line.match(hexPattern);
            if (lineMatches) {
                lineMatches.forEach(match => {
                    if (!rootHexCodes.includes(match)) {
                        warnings.push(`Potential hardcoded hex code in styles.css line ${index + 1}: ${match}`);
                    }
                });
            }
        });
    }
} else {
    warnings.push('styles.css not found');
}

// 3. Check for hardcoded font names
console.log('✓ Checking for hardcoded font names...');
if (fs.existsSync(stylesPath)) {
    const stylesContent = fs.readFileSync(stylesPath, 'utf8');
    const fontPattern = /font-family:\s*['"](Space Grotesk|Manrope|JetBrains Mono)['"]/gi;
    const matches = stylesContent.match(fontPattern);
    if (matches) {
        matches.forEach(match => {
            warnings.push(`Potential hardcoded font name: ${match.trim()}`);
        });
    }
}

// 4. Verify required assets exist
console.log('✓ Verifying required assets...');
const assetsDir = path.join(__dirname, '..', 'assets', 'logo');
const requiredAssets = [
    brand.assets?.logo?.icon,
    brand.assets?.logo?.favicon,
    brand.assets?.logo?.appleTouch
].filter(Boolean);

requiredAssets.forEach(assetPath => {
    const fullPath = path.join(__dirname, '..', assetPath);
    if (!fs.existsSync(fullPath)) {
        warnings.push(`Missing asset: ${assetPath} (expected at ${fullPath})`);
    }
});

// 5. Check that brand.js is loaded on all pages
console.log('✓ Checking brand.js integration...');
const htmlFiles = ['index.html', 'privacy.html', 'terms.html'];
htmlFiles.forEach(file => {
    const htmlPath = path.join(__dirname, '..', file);
    if (fs.existsSync(htmlPath)) {
        const htmlContent = fs.readFileSync(htmlPath, 'utf8');
        if (!htmlContent.includes('brand.js')) {
            errors.push(`${file} does not load brand.js`);
        }
    } else {
        warnings.push(`${file} not found`);
    }
});

// 6. Check for deprecated theme.json usage
console.log('✓ Checking for deprecated theme.json usage...');
const scriptJsPath = path.join(__dirname, '..', 'script.js');
if (fs.existsSync(scriptJsPath)) {
    const scriptContent = fs.readFileSync(scriptJsPath, 'utf8');
    // Check for actual usage (fetch, require, import) not just mention
    const themeJsonUsage = /(fetch|require|import).*theme\.json|theme\.json.*fetch/gi;
    if (themeJsonUsage.test(scriptContent)) {
        warnings.push('script.js actively uses theme.json (check for deprecated usage)');
    }
}

// Report results
console.log('\n=== Validation Results ===\n');

if (errors.length === 0 && warnings.length === 0) {
    console.log('✅ All checks passed!');
    process.exit(0);
}

if (errors.length > 0) {
    console.log('❌ Errors:');
    errors.forEach(error => console.log(`  - ${error}`));
}

if (warnings.length > 0) {
    console.log('\n⚠️  Warnings:');
    warnings.forEach(warning => console.log(`  - ${warning}`));
}

process.exit(errors.length > 0 ? 1 : 0);
