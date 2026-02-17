/**
 * GRID Brand Configuration Module
 * Loads and applies brand settings from branding.json
 */

class BrandConfig {
  constructor() {
    this.config = null;
    this.loaded = false;
  }

  async load() {
    try {
      const response = await fetch('./branding.json');
      this.config = await response.json();
      this.loaded = true;
      this.apply();
      return this.config;
    } catch (error) {
      console.warn('Brand config load failed, using defaults:', error);
      this.config = this.getDefaults();
      this.loaded = true;
      return this.config;
    }
  }

  getDefaults() {
    return {
      brand: {
        name: 'GRID Analyzer',
        shortName: 'GRID',
        tagline: 'Understand Any Codebase in Minutes'
      },
      colors: {
        graphite: { 950: '#0A0A0F', 900: '#14141A', 50: '#FAFAFC' },
        cyan: { 500: '#00D9FF', 400: '#33E0FF', 600: '#00B8D4' },
        amber: { 500: '#F59E0B' }
      },
      typography: {
        display: { family: "'Space Grotesk', sans-serif" },
        body: { family: "'Manrope', sans-serif" },
        mono: { family: "'JetBrains Mono', monospace" }
      }
    };
  }

  apply() {
    if (!this.config) return;

    // Apply CSS variables first (needed for other elements)
    this.applyCSSVariables();

    // Update document title
    document.title = this.config.meta?.title || this.config.brand.name;

    // Update meta tags
    this.updateMetaTag('description', this.config.meta?.description);
    this.updateMetaTag('og:title', this.config.meta?.title);
    this.updateMetaTag('og:description', this.config.meta?.description);
    this.updateMetaTag('og:image', this.config.meta?.ogImage);
    this.updateMetaTag('twitter:title', this.config.meta?.title);
    this.updateMetaTag('twitter:description', this.config.meta?.description);

    // Update favicon and apple-touch-icon
    this.applyFavicon();

    // Update brand name elements
    document.querySelectorAll('[data-brand-name]').forEach(el => {
      el.textContent = this.config.brand.name;
    });

    document.querySelectorAll('[data-brand-short]').forEach(el => {
      el.textContent = this.config.brand.shortName;
    });

    // Update logo icons (handle both SVG and emoji)
    this.applyLogo();
  }

  applyCSSVariables() {
    if (!this.config?.colors) return;

    const root = document.documentElement;
    const colors = this.config.colors;

    // Graphite colors
    if (colors.graphite) {
      Object.entries(colors.graphite).forEach(([shade, value]) => {
        root.style.setProperty(`--graphite-${shade}`, value);
      });
    }

    // Cyan colors
    if (colors.cyan) {
      Object.entries(colors.cyan).forEach(([shade, value]) => {
        root.style.setProperty(`--cyan-${shade}`, value);
      });
    }

    // Amber colors
    if (colors.amber) {
      Object.entries(colors.amber).forEach(([shade, value]) => {
        root.style.setProperty(`--amber-${shade}`, value);
      });
    }

    // Semantic colors
    if (colors.semantic) {
      Object.entries(colors.semantic).forEach(([name, value]) => {
        root.style.setProperty(`--${name}`, value);
      });
    }

    // White color
    if (colors.white) {
      root.style.setProperty('--white', colors.white);
    }
  }

  applyFavicon() {
    if (!this.config?.assets?.logo) return;

    const logo = this.config.assets.logo;

    // Update favicon
    if (logo.favicon) {
      let faviconLink = document.querySelector('link[rel="icon"]');
      if (!faviconLink) {
        faviconLink = document.createElement('link');
        faviconLink.setAttribute('rel', 'icon');
        document.head.appendChild(faviconLink);
      }
      faviconLink.setAttribute('href', logo.favicon);
      // If SVG, set type
      if (logo.favicon.endsWith('.svg')) {
        faviconLink.setAttribute('type', 'image/svg+xml');
      }
    }

    // Update apple-touch-icon
    if (logo.appleTouch) {
      let appleTouchLink = document.querySelector('link[rel="apple-touch-icon"]');
      if (!appleTouchLink) {
        appleTouchLink = document.createElement('link');
        appleTouchLink.setAttribute('rel', 'apple-touch-icon');
        document.head.appendChild(appleTouchLink);
      }
      appleTouchLink.setAttribute('href', logo.appleTouch);
    }
  }

  applyLogo() {
    if (!this.config?.assets?.logo) return;

    const logoIcon = this.config.assets.logo.icon;
    if (!logoIcon) return;

    // Handle data-brand-icon attributes
    document.querySelectorAll('[data-brand-icon]').forEach(el => {
      // Check if it's an img element or text element
      if (el.tagName === 'IMG') {
        // Update img src
        el.setAttribute('src', logoIcon);
        el.setAttribute('alt', '');
      } else {
        // For text elements, check if icon is SVG path or emoji
        if (logoIcon.endsWith('.svg') || logoIcon.startsWith('assets/')) {
          // SVG path - convert to img element
          const img = document.createElement('img');
          img.setAttribute('src', logoIcon);
          img.setAttribute('alt', '');
          img.className = el.className || 'logo-icon';
          el.parentNode.replaceChild(img, el);
        } else {
          // Emoji - set as text content
          el.textContent = logoIcon;
        }
      }
    });

    // Also update .logo-icon img elements directly (for cases without data-brand-icon)
    document.querySelectorAll('.logo-icon').forEach(el => {
      if (el.tagName === 'IMG' && logoIcon.endsWith('.svg')) {
        el.setAttribute('src', logoIcon);
      }
    });
  }

  updateMetaTag(name, content) {
    if (!content) return;
    const selector = name.startsWith('og:') 
      ? `meta[property="${name}"]` 
      : `meta[name="${name}"]`;
    const tag = document.querySelector(selector);
    if (tag) tag.setAttribute('content', content);
  }

  get(path) {
    return path.split('.').reduce((obj, key) => obj?.[key], this.config);
  }

  getColor(category, shade) {
    return this.config?.colors?.[category]?.[shade];
  }

  getFont(type) {
    return this.config?.typography?.[type]?.family;
  }
}

// Create global instance
window.brand = new BrandConfig();

// Auto-load on DOM ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => window.brand.load());
} else {
  window.brand.load();
}

export default BrandConfig;
