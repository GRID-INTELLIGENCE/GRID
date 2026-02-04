// GRID Analyzer Landing Page JavaScript
// ============================================================
// CONFIGURATION - Update these values before launch
// ============================================================

// ============================================================
// THEME CONFIGURATION - Loaded from branding.json via brand.js
// ============================================================

// Get theme from brand.js config (loaded asynchronously)
function getTheme() {
    // Use brand.js config if available, otherwise return fallback
    if (window.brand && window.brand.config) {
        return window.brand.config;
    }
    // Fallback for when brand.js hasn't loaded yet
    return {
        brand: {
            name: "GRID Analyzer",
            shortName: "GRID",
            iconEmoji: "🛞"
        },
        colors: {
            semantic: {
                warning: "#F59E0B"
            }
        }
    };
}

// Wait for brand.js to load, then use its config
async function waitForBrand() {
    if (window.brand && window.brand.loaded) {
        return window.brand.config;
    }
    // Wait for brand.js to load
    return new Promise((resolve) => {
        const checkBrand = setInterval(() => {
            if (window.brand && window.brand.loaded) {
                clearInterval(checkBrand);
                resolve(window.brand.config);
            }
        }, 50);
        // Timeout after 2 seconds
        setTimeout(() => {
            clearInterval(checkBrand);
            resolve(getTheme()); // Return fallback
        }, 2000);
    });
}

// ============================================================
// SECURITY MODULE - Based on grid/src/grid/security patterns
// ============================================================

const SecurityModule = {
    // Threat patterns from InputSanitizer
    DANGEROUS_PATTERNS: [
        { pattern: /<script[^>]*>/i, type: 'XSS', severity: 'CRITICAL' },
        { pattern: /javascript\s*:/i, type: 'XSS', severity: 'HIGH' },
        { pattern: /on\w+\s*=/i, type: 'XSS', severity: 'HIGH' },
        { pattern: /union\s+select/i, type: 'SQL_INJECTION', severity: 'CRITICAL' },
        { pattern: /eval\s*\(/i, type: 'CODE_INJECTION', severity: 'CRITICAL' },
        { pattern: /\.\.\/|\.\.\\/, type: 'PATH_TRAVERSAL', severity: 'HIGH' }
    ],

    // Validate and sanitize input
    validateInput(text, config = {}) {
        const result = {
            isValid: true,
            sanitized: text,
            threats: [],
            severity: 'NONE'
        };

        // Check length
        if (config.maxLength && text.length > config.maxLength) {
            result.sanitized = text.slice(0, config.maxLength);
            result.threats.push({ type: 'OVERSIZED_INPUT', severity: 'MEDIUM' });
        }

        // Check threat patterns
        for (const { pattern, type, severity } of this.DANGEROUS_PATTERNS) {
            if (pattern.test(text)) {
                result.threats.push({ type, severity });
                result.sanitized = result.sanitized.replace(pattern, '');
                result.severity = this.maxSeverity(result.severity, severity);
            }
        }

        // Determine action based on AI Safety framework
        if (result.severity === 'CRITICAL') {
            result.isValid = false;
            result.action = 'BLOCK';
        } else if (result.severity === 'HIGH') {
            result.action = 'REVIEW';  // Log for review
        } else {
            result.action = 'ALLOW';
        }

        return result;
    },

    // HTML encode for safe display (from InputSanitizer)
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },

    // Safe DOM update (never innerHTML)
    safeSetContent(element, content) {
        if (element) {
            element.textContent = content;
        }
    },

    maxSeverity(a, b) {
        const levels = ['NONE', 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'];
        return levels[Math.max(levels.indexOf(a), levels.indexOf(b))];
    },

    // Log security events (from audit_logger patterns)
    logSecurityEvent(eventType, details) {
        console.warn(`[SECURITY] ${eventType}:`, details);
        // In production: send to analytics/monitoring
        if (typeof trackEvent === 'function') {
            trackEvent('security_event', eventType, JSON.stringify(details));
        }
    }
};

// Security Contracts
const INPUT_VALIDATION_CONTRACT = {
    email: {
        maxLength: 254,  // RFC 5321
        pattern: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
        threatPatterns: [
            /javascript:/i,      // XSS
            /<script/i,          // XSS
            /union\s+select/i,   // SQL injection
            /'\s*or\s+'1/i       // SQL injection
        ],
        action: 'BLOCK'  // If threat detected
    },
    useCase: {
        maxLength: 500,
        threatPatterns: [
            /<script/i,
            /eval\s*\(/i,
            /__import__/i,
            /subprocess\./i
        ],
        action: 'SANITIZE'  // Strip dangerous content, allow submission
    }
};

const DOM_SAFETY_CONTRACT = {
    allowedMethods: ['textContent', 'setAttribute'],  // Safe
    blockedMethods: ['innerHTML', 'outerHTML'],       // XSS risk
    attributeAllowlist: ['aria-*', 'data-*', 'class', 'id', 'href'],
    hrefValidation: /^(https?:\/\/|#|\/)/  // No javascript: URLs
};

// Stripe Configuration
// Get your keys from: https://dashboard.stripe.com/apikeys
// For testing, use pk_test_... keys. For production, use pk_live_...
const STRIPE_CONFIG = {
    // IMPORTANT: Replace with your actual Stripe publishable key
    publishableKey: 'pk_test_51EXAMPLE_REPLACE_WITH_YOUR_KEY',
    
    // Price IDs from Stripe Dashboard > Products > Prices
    // Create these at: https://dashboard.stripe.com/products
    prices: {
        professional_monthly: 'price_REPLACE_professional_monthly',
        professional_annual: 'price_REPLACE_professional_annual',
        team_monthly: 'price_REPLACE_team_monthly',
        team_annual: 'price_REPLACE_team_annual'
    },
    
    // Your backend endpoints (or use Stripe Payment Links as alternative)
    endpoints: {
        createCheckoutSession: '/api/create-checkout-session',
        // Alternative: Use Stripe Payment Links (no backend needed)
        // paymentLinks: {
        //     professional: 'https://buy.stripe.com/your_professional_link',
        //     team: 'https://buy.stripe.com/your_team_link'
        // }
    }
};

// Formspree Configuration for Beta Signup
// Sign up at: https://formspree.io and create a form
const FORMSPREE_CONFIG = {
    // Replace with your Formspree form ID (e.g., 'xpznqwer')
    formId: 'xpznqwer',
    endpoint: function() {
        return `https://formspree.io/f/${this.formId}`;
    }
};

// ============================================================
// STRIPE INITIALIZATION
// ============================================================

let stripe = null;

// Initialize Stripe only if a valid key is provided
function initStripe() {
    if (STRIPE_CONFIG.publishableKey && 
        !STRIPE_CONFIG.publishableKey.includes('REPLACE') &&
        !STRIPE_CONFIG.publishableKey.includes('YOUR_KEY')) {
        try {
            stripe = Stripe(STRIPE_CONFIG.publishableKey);
            console.log('%c✓ Stripe initialized', 'color: #10B981');
        } catch (error) {
            console.warn('Stripe initialization failed:', error);
        }
    } else {
        console.warn('%c⚠ Stripe not configured - Update STRIPE_CONFIG in script.js', 'color: #F59E0B; font-weight: bold');
    }
}

// Initialize on load
if (typeof Stripe !== 'undefined') {
    initStripe();
}

// ============================================================
// BETA FORM SUBMISSION (Formspree Integration)
// ============================================================

const betaForm = document.getElementById('betaForm');
if (betaForm) {
    betaForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const submitBtn = betaForm.querySelector('button[type="submit"]');
        const originalText = submitBtn.textContent;
        addLoadingState(submitBtn, originalText);

        const email = document.getElementById('email').value;
        const useCase = document.getElementById('useCase').value;

        // SECURITY: Validate email
        const emailValidation = SecurityModule.validateInput(email, {
            maxLength: INPUT_VALIDATION_CONTRACT.email.maxLength
        });

        // Check email format
        if (!INPUT_VALIDATION_CONTRACT.email.pattern.test(email)) {
            SecurityModule.logSecurityEvent('BLOCKED_SUBMISSION', {
                field: 'email',
                reason: 'Invalid email format'
            });
            removeLoadingState(submitBtn);
            showMessage('Invalid email format', 'error');
            return;
        }

        if (!emailValidation.isValid) {
            SecurityModule.logSecurityEvent('BLOCKED_SUBMISSION', {
                field: 'email',
                threats: emailValidation.threats
            });
            removeLoadingState(submitBtn);
            showMessage('Invalid email format', 'error');
            return;
        }

        try {
            const response = await fetch(FORMSPREE_CONFIG.endpoint(), {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify({ 
                    email: emailValidation.sanitized,
                    useCase: 'Not specified',
                    source: 'landing_page_beta',
                    timestamp: new Date().toISOString(),
                    referrer: localStorage.getItem('referral_source') || 'direct'
                })
            });

            if (response.ok) {
                // Show success message
                betaForm.style.display = 'none';
                document.getElementById('betaSuccess').style.display = 'block';
                
                // Scroll success into view
                document.getElementById('betaSuccess').scrollIntoView({ 
                    behavior: 'smooth', 
                    block: 'center' 
                });

                // Track conversion
                trackEvent('beta_signup', 'conversion', 'beta_form_success');
                
                showMessage('Welcome to the beta! Check your email for next steps.', 'success');
            } else {
                const data = await response.json();
                throw new Error(data.error || 'Submission failed');
            }
        } catch (error) {
            console.error('Beta signup error:', error);
            
            // Fallback: Open email client
            const subject = encodeURIComponent('GRID Analyzer Beta Access Request');
            const body = encodeURIComponent(
                `Hi GRID Team,\n\nI'd like to join the beta!\n\nEmail: ${email}\nUse Case: ${useCase || 'Not specified'}\n\nThanks!`
            );
            
            showMessage('Redirecting to email...', 'info');
            removeLoadingState(submitBtn);
            setTimeout(() => {
                window.location.href = `mailto:hello@grid-analyzer.com?subject=${subject}&body=${body}`;
            }, 1000);
        }
    });
}

// ============================================================
// STRIPE CHECKOUT FUNCTIONS
// ============================================================

async function checkoutProfessional() {
    await initiateCheckout('professional_monthly', 'Professional');
}

async function checkoutTeam() {
    await initiateCheckout('team_monthly', 'Team');
}

async function initiateCheckout(priceKey, tierName) {
    // Check if Stripe is configured
    if (!stripe) {
        showMessage(`Checkout coming soon! Join the beta for early access to ${tierName}.`, 'info');
        document.getElementById('beta').scrollIntoView({ behavior: 'smooth' });
        return;
    }

    const button = event.target;
    const originalText = button.textContent;
    button.textContent = 'Loading...';
    button.disabled = true;

    try {
        const response = await fetch(STRIPE_CONFIG.endpoints.createCheckoutSession, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                priceId: STRIPE_CONFIG.prices[priceKey],
                mode: 'subscription',
                successUrl: window.location.origin + '/success?session_id={CHECKOUT_SESSION_ID}',
                cancelUrl: window.location.href
            })
        });

        if (!response.ok) {
            throw new Error('Failed to create checkout session');
        }

        const session = await response.json();
        
        const result = await stripe.redirectToCheckout({
            sessionId: session.id
        });

        if (result.error) {
            throw new Error(result.error.message);
        }
    } catch (error) {
        console.error('Checkout error:', error);
        showMessage(`Unable to start checkout. Join the beta while we resolve this!`, 'error');
        document.getElementById('beta').scrollIntoView({ behavior: 'smooth' });
    } finally {
        button.textContent = originalText;
        button.disabled = false;
    }
}

// Export for inline onclick handlers
window.checkoutProfessional = checkoutProfessional;
window.checkoutTeam = checkoutTeam;

// ============================================================
// INTERACTIVE TERMINAL DEMO
// ============================================================

const terminalCommands = [
    {
        command: 'grid analyze ./my-legacy-codebase',
        output: [
            '⠋ Indexing codebase...',
            '✓ Found 2,847 files across 156 directories',
            '✓ Parsed 847 Python modules, 423 TypeScript files',
            '✓ Built relationship graph (12,456 edges)',
            '✓ Index complete in 2.3 minutes',
            '',
            '📊 Codebase Summary:',
            '   • 142,856 lines of code',
            '   • 5 circular dependencies detected',
            '   • 23 design patterns identified'
        ],
        delay: 80
    },
    {
        command: 'grid query "Where is user authentication handled?"',
        output: [
            '🔍 Searching semantic index...',
            '',
            '✓ Primary: src/auth/login.py:42-89',
            '  └─ authenticate_user() - Main auth entry point',
            '',
            '✓ Related: src/middleware/auth_middleware.py:15',
            '  └─ AuthMiddleware - Request validation',
            '',
            '✓ Depends on: src/models/user.py:23',
            '  └─ User model with password hashing',
            '',
            '📎 3 files, 5 functions, 2 classes'
        ],
        delay: 60
    },
    {
        command: 'grid map --output arch.svg',
        output: [
            '🎨 Generating architecture visualization...',
            '',
            '✓ Created: arch.svg (interactive)',
            '✓ Modules: 47 components mapped',
            '✓ Detected patterns:',
            '   • Repository Pattern (src/repositories/)',
            '   • Factory Pattern (src/factories/)',
            '   • Observer Pattern (src/events/)',
            '',
            '⚠ Warning: Circular dependency detected',
            '  auth → users → permissions → auth'
        ],
        delay: 70
    }
];

let currentCommandIndex = 0;
let isTyping = false;

function initTerminalDemo() {
    const demoContainer = document.querySelector('.demo-placeholder');
    if (!demoContainer) return;

    // Create terminal structure
    demoContainer.innerHTML = `
        <div class="terminal-window">
            <div class="terminal-header">
                <div class="terminal-buttons">
                    <span class="terminal-btn close"></span>
                    <span class="terminal-btn minimize"></span>
                    <span class="terminal-btn maximize"></span>
                </div>
                <span class="terminal-title">grid-analyzer — zsh</span>
            </div>
            <div class="terminal-body" id="terminalBody">
                <div class="terminal-line">
                    <span class="prompt">$</span>
                    <span class="command" id="terminalCommand"></span>
                    <span class="cursor">▋</span>
                </div>
                <div class="terminal-output" id="terminalOutput"></div>
            </div>
            <div class="terminal-controls">
                <button class="terminal-replay-btn" onclick="replayTerminal()" title="Replay demo">
                    ↻ Replay
                </button>
            </div>
        </div>
    `;

    // Start the demo
    setTimeout(() => runTerminalDemo(), 1000);
}

async function runTerminalDemo() {
    if (isTyping) return;
    isTyping = true;

    const commandEl = document.getElementById('terminalCommand');
    const outputEl = document.getElementById('terminalOutput');
    
    if (!commandEl || !outputEl) {
        isTyping = false;
        return;
    }

    for (let i = 0; i < terminalCommands.length; i++) {
        const cmd = terminalCommands[i];
        
        // Clear for new command (except first)
        if (i > 0) {
            await sleep(1500);
            outputEl.innerHTML = '';
            commandEl.textContent = '';
        }

        // Type command
        for (let char of cmd.command) {
            commandEl.textContent += char;
            await sleep(50 + Math.random() * 30);
        }

        // Simulate enter press
        await sleep(500);
        
        // Show output line by line
        for (let line of cmd.output) {
            const lineEl = document.createElement('div');
            lineEl.className = 'output-line';
            lineEl.textContent = line;
            outputEl.appendChild(lineEl);
            await sleep(cmd.delay);
        }

        // Pause before next command
        if (i < terminalCommands.length - 1) {
            await sleep(2000);
        }
    }

    isTyping = false;
    
    // Loop after delay
    setTimeout(() => {
        currentCommandIndex = 0;
        runTerminalDemo();
    }, 8000);
}

function replayTerminal() {
    if (isTyping) return;
    const outputEl = document.getElementById('terminalOutput');
    const commandEl = document.getElementById('terminalCommand');
    if (outputEl) outputEl.innerHTML = '';
    if (commandEl) commandEl.textContent = '';
    currentCommandIndex = 0;
    runTerminalDemo();
}

window.replayTerminal = replayTerminal;

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// Initialize terminal on DOM ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initTerminalDemo);
} else {
    initTerminalDemo();
}

// ============================================================
// NAVIGATION & UI
// ============================================================

// Mobile hamburger menu
function initMobileNav() {
    const nav = document.querySelector('.nav-content');
    const navLinks = document.querySelector('.nav-links');
    
    if (!nav || !navLinks) return;

    // Create hamburger button
    const hamburger = document.createElement('button');
    hamburger.className = 'hamburger-btn';
    hamburger.setAttribute('aria-label', 'Toggle navigation menu');
    hamburger.setAttribute('aria-expanded', 'false');
    hamburger.innerHTML = `
        <span class="hamburger-line"></span>
        <span class="hamburger-line"></span>
        <span class="hamburger-line"></span>
    `;

    // Insert hamburger before nav links
    nav.insertBefore(hamburger, navLinks);

    // Toggle menu
    hamburger.addEventListener('click', () => {
        const isOpen = navLinks.classList.toggle('nav-open');
        hamburger.classList.toggle('hamburger-active');
        hamburger.setAttribute('aria-expanded', isOpen);
    });

    // Close menu on link click
    navLinks.querySelectorAll('a').forEach(link => {
        link.addEventListener('click', () => {
            navLinks.classList.remove('nav-open');
            hamburger.classList.remove('hamburger-active');
            hamburger.setAttribute('aria-expanded', 'false');
        });
    });

    // Close on outside click
    document.addEventListener('click', (e) => {
        if (!nav.contains(e.target) && navLinks.classList.contains('nav-open')) {
            navLinks.classList.remove('nav-open');
            hamburger.classList.remove('hamburger-active');
            hamburger.setAttribute('aria-expanded', 'false');
        }
    });
}

// Smooth scrolling for anchor links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// ============================================================
// CONVERSION OPTIMIZATION
// ============================================================

// Live activity notifications
const activityMessages = [
    { city: 'San Francisco', action: 'joined the beta' },
    { city: 'London', action: 'started a free trial' },
    { city: 'Berlin', action: 'joined the beta' },
    { city: 'Tokyo', action: 'analyzed 50K lines of code' },
    { city: 'New York', action: 'joined the beta' },
    { city: 'Singapore', action: 'started a free trial' },
    { city: 'Toronto', action: 'joined the beta' },
    { city: 'Sydney', action: 'analyzed their monorepo' }
];

let activityIndex = 0;

function showLiveActivity() {
    // Only show occasionally to avoid annoyance
    if (Math.random() > 0.3) return;
    
    const activity = activityMessages[activityIndex];
    activityIndex = (activityIndex + 1) % activityMessages.length;
    
    // SECURITY: Sanitize activity data before display
    const sanitizedCity = SecurityModule.escapeHtml(activity.city);
    const sanitizedAction = SecurityModule.escapeHtml(activity.action);
    
    const notification = document.createElement('div');
    notification.className = 'live-activity-notification';
    
    // SECURITY: Use createElement instead of innerHTML
    const iconSpan = document.createElement('span');
    iconSpan.className = 'activity-icon';
    iconSpan.textContent = '🚀';
    
    const textSpan = document.createElement('span');
    textSpan.className = 'activity-text';
    textSpan.appendChild(document.createTextNode('Someone from '));
    const strongEl = document.createElement('strong');
    strongEl.textContent = sanitizedCity;
    textSpan.appendChild(strongEl);
    textSpan.appendChild(document.createTextNode(` just ${sanitizedAction}`));
    
    notification.appendChild(iconSpan);
    notification.appendChild(textSpan);
    
    document.body.appendChild(notification);
    
    // Animate in
    requestAnimationFrame(() => {
        notification.classList.add('show');
    });
    
    // Remove after delay
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => notification.remove(), 300);
    }, 4000);
}

// Show activity periodically (start after 30 seconds)
setTimeout(() => {
    showLiveActivity();
    setInterval(showLiveActivity, 45000);
}, 30000);

// Beta slots counter
function updateBetaSlots() {
    const slotsEl = document.getElementById('betaSlotsCount');
    if (!slotsEl) return;
    
    // Simulate decreasing slots (in production, fetch from backend)
    const baseSlots = 50;
    const randomReduction = Math.floor(Math.random() * 15) + 10;
    const remainingSlots = Math.max(5, baseSlots - randomReduction);
    
    slotsEl.textContent = remainingSlots;
    
    if (remainingSlots <= 10) {
        slotsEl.parentElement.classList.add('slots-urgent');
    }
}

// ============================================================
// ANALYTICS & TRACKING
// ============================================================

function trackEvent(action, category, label) {
    if (typeof gtag !== 'undefined') {
        gtag('event', action, {
            'event_category': category,
            'event_label': label
        });
    }
    // Console log for debugging
    console.log(`📊 Event: ${action} | ${category} | ${label}`);
}

// Track button clicks
document.querySelectorAll('button, .btn-primary, .btn-secondary, .btn-primary-large, .btn-secondary-large').forEach(button => {
    button.addEventListener('click', function() {
        const buttonText = this.textContent.trim();
        trackEvent('button_click', 'engagement', buttonText);
    });
});

// Track scroll depth
let maxScrollDepth = 0;
window.addEventListener('scroll', () => {
    const windowHeight = window.innerHeight;
    const documentHeight = document.documentElement.scrollHeight;
    const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
    const currentDepth = Math.floor((scrollTop + windowHeight) / documentHeight * 100);

    if (currentDepth > maxScrollDepth) {
        maxScrollDepth = currentDepth;
        if (maxScrollDepth % 25 === 0) {
            trackEvent('scroll_depth', 'engagement', `${maxScrollDepth}%`);
        }
    }
});

// Handle URL parameters (referrals)
const urlParams = new URLSearchParams(window.location.search);
const ref = urlParams.get('ref');
if (ref) {
    trackEvent('referral_visit', 'acquisition', ref);
    localStorage.setItem('referral_source', ref);
}

// ============================================================
// UI UTILITIES
// ============================================================

function showMessage(message, type = 'success') {
    // SECURITY: Sanitize message before display
    const sanitizedMessage = SecurityModule.escapeHtml(message);
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `toast-message toast-${type}`;
    
    // SECURITY: Use createElement instead of innerHTML for user content
    const iconSpan = document.createElement('span');
    iconSpan.className = 'toast-icon';
    iconSpan.textContent = type === 'success' ? '✓' : type === 'error' ? '✗' : 'ℹ';
    
    const textSpan = document.createElement('span');
    textSpan.className = 'toast-text';
    textSpan.textContent = sanitizedMessage;
    
    messageDiv.appendChild(iconSpan);
    messageDiv.appendChild(textSpan);
    
    document.body.appendChild(messageDiv);

    requestAnimationFrame(() => {
        messageDiv.classList.add('toast-show');
    });

    setTimeout(() => {
        messageDiv.classList.remove('toast-show');
        setTimeout(() => messageDiv.remove(), 300);
    }, 4000);
}

// FAQ Accordion with Keyboard Navigation
function toggleFAQ() {
    this.classList.toggle('faq-active');
    
    // Close other items
    document.querySelectorAll('.faq-item').forEach(other => {
        if (other !== this) {
            other.classList.remove('faq-active');
        }
    });
}

document.querySelectorAll('.faq-item').forEach(item => {
    item.addEventListener('click', toggleFAQ);
    item.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            toggleFAQ.call(item);
        }
    });
});

// ============================================================
// AUDIENCE TABS WITH KEYBOARD ACCESSIBILITY
// ============================================================

function initAudienceTabs() {
    const tabs = document.querySelectorAll('.segment-tabs .tab');
    const panels = document.querySelectorAll('.segment-content');
    
    if (tabs.length === 0) return;
    
    function activateTab(tab) {
        const audience = tab.getAttribute('data-audience');
        
        tabs.forEach(t => {
            t.classList.remove('active');
            t.setAttribute('aria-selected', 'false');
            t.setAttribute('tabindex', '-1');
        });
        
        tab.classList.add('active');
        tab.setAttribute('aria-selected', 'true');
        tab.setAttribute('tabindex', '0');
        
        panels.forEach(panel => {
            const panelAudience = panel.getAttribute('data-audience');
            if (panelAudience === audience) {
                panel.hidden = false;
                panel.classList.add('active');
            } else {
                panel.hidden = true;
                panel.classList.remove('active');
            }
        });
    }
    
    tabs.forEach((tab, index) => {
        tab.addEventListener('click', () => activateTab(tab));
        
        // Keyboard navigation (security: no user input)
        tab.addEventListener('keydown', (e) => {
            const tabsArray = Array.from(tabs);
            let newIndex;
            
            switch(e.key) {
                case 'ArrowRight':
                case 'ArrowDown':
                    e.preventDefault();
                    newIndex = (index + 1) % tabsArray.length;
                    activateTab(tabsArray[newIndex]);
                    tabsArray[newIndex].focus();
                    break;
                case 'ArrowLeft':
                case 'ArrowUp':
                    e.preventDefault();
                    newIndex = (index - 1 + tabsArray.length) % tabsArray.length;
                    activateTab(tabsArray[newIndex]);
                    tabsArray[newIndex].focus();
                    break;
                case 'Home':
                    e.preventDefault();
                    activateTab(tabsArray[0]);
                    tabsArray[0].focus();
                    break;
                case 'End':
                    e.preventDefault();
                    activateTab(tabsArray[tabsArray.length - 1]);
                    tabsArray[tabsArray.length - 1].focus();
                    break;
            }
        });
    });
    
    // Activate first tab by default
    if (tabs.length > 0) {
        activateTab(tabs[0]);
    }
}

// ============================================================
// PRICING TOGGLE FUNCTIONALITY
// ============================================================

function initPricingToggle() {
    const toggleButtons = document.querySelectorAll('.pricing-toggle .toggle-btn');
    const pricingGrid = document.querySelector('.pricing-grid');
    
    if (toggleButtons.length === 0 || !pricingGrid) return;
    
    toggleButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const period = btn.getAttribute('data-period');
            
            // Update button states
            toggleButtons.forEach(b => {
                b.classList.remove('active');
                b.setAttribute('aria-pressed', 'false');
            });
            btn.classList.add('active');
            btn.setAttribute('aria-pressed', 'true');
            
            // Update pricing display
            pricingGrid.setAttribute('data-billing', period);
        });
    });
}

// ============================================================
// COPY TO CLIPBOARD FUNCTIONALITY
// ============================================================

function initCopyButtons() {
    document.querySelectorAll('.copy-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const textToCopy = btn.getAttribute('data-copy');
            
            // SECURITY: Validate text is a known safe command
            const safeCommands = ['pip install grid-analyzer', 'grid analyze', 'grid query'];
            if (!safeCommands.some(cmd => textToCopy.startsWith(cmd))) {
                SecurityModule.logSecurityEvent('INVALID_COPY_ATTEMPT', { text: textToCopy });
                return;
            }
            
            navigator.clipboard.writeText(textToCopy).then(() => {
                const originalText = btn.textContent;
                SecurityModule.safeSetContent(btn, '✓');
                setTimeout(() => {
                    SecurityModule.safeSetContent(btn, originalText);
                }, 2000);
            }).catch(err => {
                console.warn('Failed to copy to clipboard:', err);
            });
        });
    });
}

// ============================================================
// INITIALIZATION
// ============================================================

// ============================================================
// PHASE 2: SCROLL-TRIGGERED REVEAL ANIMATIONS
// ============================================================

// ============================================================
// PHASE 2: SECTION SCROLL INDICATORS
// ============================================================

// Initialize section scroll indicators
function initScrollIndicators() {
    const indicators = document.querySelectorAll('.scroll-indicator');
    const sections = document.querySelectorAll('section[id]');
    
    if (indicators.length === 0 || sections.length === 0) return;

    // Update active indicator based on scroll position
    function updateActiveIndicator() {
        const scrollPosition = window.pageYOffset + window.innerHeight / 2;
        
        let currentSection = '';
        sections.forEach(section => {
            const sectionTop = section.offsetTop;
            const sectionHeight = section.offsetHeight;
            const sectionId = section.getAttribute('id');
            
            if (scrollPosition >= sectionTop && scrollPosition < sectionTop + sectionHeight) {
                currentSection = sectionId;
            }
        });

        // Update indicator states
        indicators.forEach(indicator => {
            const targetSection = indicator.getAttribute('data-section');
            if (targetSection === currentSection || 
                (indicator.getAttribute('href') === `#${currentSection}`)) {
                indicator.classList.add('active');
            } else {
                indicator.classList.remove('active');
            }
        });
    }

    // Throttle scroll events
    let ticking = false;
    window.addEventListener('scroll', () => {
        if (!ticking) {
            window.requestAnimationFrame(() => {
                updateActiveIndicator();
                ticking = false;
            });
            ticking = true;
        }
    }, { passive: true });

    // Initial update
    updateActiveIndicator();
}

// Initialize scroll-triggered reveal animations
function initScrollReveal() {
    // Check for reduced motion preference
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (prefersReducedMotion) {
        // Still add the class but animations will be disabled via CSS
        document.querySelectorAll('.reveal-on-scroll, .reveal-on-scroll-stagger').forEach(el => {
            el.classList.add('revealed');
        });
        return;
    }

    // Create Intersection Observer
    const observerOptions = {
        root: null,
        rootMargin: '0px 0px -50px 0px', // Trigger when element is 50px from bottom of viewport
        threshold: 0.05 // Trigger when 5% of element is visible (lower threshold for better visibility)
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('revealed');
                // Unobserve after revealing to improve performance
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    // Observe all elements with reveal-on-scroll class
    document.querySelectorAll('.reveal-on-scroll, .reveal-on-scroll-stagger').forEach(el => {
        // Check if element is already in viewport on load
        const rect = el.getBoundingClientRect();
        const isInViewport = rect.top < window.innerHeight && rect.bottom > 0;
        
        if (isInViewport) {
            // Reveal immediately if already in view
            el.classList.add('revealed');
        } else {
            // Observe for scroll
            observer.observe(el);
        }
    });
}

// ============================================================
// PHASE 3: DEMO VIDEO FUNCTIONALITY
// ============================================================

// Initialize demo video
function initDemoVideo() {
    const video = document.getElementById('demoVideo');
    const playBtn = document.getElementById('videoPlayBtn');
    const videoContainer = document.querySelector('.demo-video-container');
    const demoPlaceholder = document.querySelector('.demo-placeholder');
    
    if (!video || !playBtn) return;
    
    // Show video container when video is ready
    video.addEventListener('loadedmetadata', () => {
        if (videoContainer) {
            videoContainer.style.display = 'block';
        }
        if (demoPlaceholder) {
            demoPlaceholder.style.display = 'none';
        }
    });
    
    // Play button functionality
    playBtn.addEventListener('click', () => {
        video.play();
        playBtn.classList.add('playing');
        playBtn.setAttribute('aria-label', 'Pause demo video');
    });
    
    // Update play button on video events
    video.addEventListener('play', () => {
        playBtn.classList.add('playing');
    });
    
    video.addEventListener('pause', () => {
        playBtn.classList.remove('playing');
        playBtn.setAttribute('aria-label', 'Play demo video');
    });
    
    // Click on video to pause/play
    video.addEventListener('click', () => {
        if (video.paused) {
            video.play();
        } else {
            video.pause();
        }
    });
}

// Initialize video testimonials
function initVideoTestimonials() {
    const testimonialVideos = document.querySelectorAll('.testimonial-video');
    
    testimonialVideos.forEach((video, index) => {
        const playBtn = video.nextElementSibling;
        if (!playBtn || !playBtn.classList.contains('video-play-btn')) return;
        
        playBtn.addEventListener('click', () => {
            video.play();
            playBtn.style.display = 'none';
        });
        
        video.addEventListener('pause', () => {
            playBtn.style.display = 'flex';
        });
    });
}

// ============================================================
// BACKGROUND MUSIC CONTROLS
// ============================================================

function initBackgroundMusic() {
    const audio = document.getElementById('bgMusic');
    const toggle = document.getElementById('musicToggle');
    if (!audio || !toggle) return;
    
    let isPlaying = false;
    
    // Load saved volume preference
    const savedVolume = localStorage.getItem('grid-music-volume');
    if (savedVolume !== null) {
        audio.volume = parseFloat(savedVolume);
    } else {
        audio.volume = 0.3; // Default 30% volume
    }
    
    // Handle play/pause
    toggle.addEventListener('click', () => {
        if (isPlaying) {
            audio.pause();
            toggle.classList.remove('playing');
            isPlaying = false;
        } else {
            audio.play().catch(err => {
                console.warn('Audio playback failed:', err);
            });
            toggle.classList.add('playing');
            isPlaying = true;
        }
    });
    
    // Update state when audio ends or errors
    audio.addEventListener('ended', () => {
        toggle.classList.remove('playing');
        isPlaying = false;
    });
    
    audio.addEventListener('error', (e) => {
        console.warn('Background music file not found or failed to load:', e);
        toggle.style.display = 'none'; // Hide toggle if audio fails
    });
    
    // Save volume when changed
    audio.addEventListener('volumechange', () => {
        localStorage.setItem('grid-music-volume', audio.volume.toString());
    });
}

document.addEventListener('DOMContentLoaded', async () => {
    // Wait for brand.js to load branding.json (it loads automatically)
    await waitForBrand();
    initDarkMode(); // Initialize dark mode first
    initMobileNav();
    updateBetaSlots();
    initScrollProgress();
    initNavStateChange();
    initScrollReveal(); // Phase 2: Scroll animations
    initScrollIndicators(); // Phase 2: Section scroll indicators
    initDemoVideo(); // Phase 3: Demo video
    initVideoTestimonials(); // Phase 3: Video testimonials
    initBackgroundMusic(); // Initialize background music controls
    initAudienceTabs(); // Audience segmentation tabs
    initCopyButtons(); // Copy to clipboard buttons
    initPricingToggle(); // Pricing monthly/annual toggle
    
    // Add dynamic styles
    addDynamicStyles();
});

function addDynamicStyles() {
    const style = document.createElement('style');
    style.textContent = `
        /* Toast Messages */
        .toast-message {
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 1rem 1.5rem;
            background: #1F2937;
            color: white;
            border-radius: 8px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.2);
            z-index: 9999;
            display: flex;
            align-items: center;
            gap: 0.75rem;
            transform: translateX(120%);
            transition: transform 0.3s ease;
        }
        .toast-show { transform: translateX(0); }
        .toast-success { border-left: 4px solid #10B981; }
        .toast-error { border-left: 4px solid #EF4444; }
        .toast-info { border-left: 4px solid #3B82F6; }
        .toast-icon { font-size: 1.25rem; }

        /* Live Activity Notification */
        .live-activity-notification {
            position: fixed;
            bottom: 20px;
            left: 20px;
            padding: 0.75rem 1rem;
            background: white;
            border-radius: 8px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.15);
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 0.875rem;
            z-index: 9998;
            transform: translateY(120%);
            transition: transform 0.3s ease;
        }
        .live-activity-notification.show { transform: translateY(0); }
        .activity-icon { font-size: 1rem; }

        /* Terminal Styles */
        .terminal-window {
            background: #0D1117;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 25px 50px rgba(0,0,0,0.4);
            font-family: 'JetBrains Mono', 'Fira Code', 'Monaco', monospace;
        }
        .terminal-header {
            background: #161B22;
            padding: 12px 16px;
            display: flex;
            align-items: center;
            gap: 12px;
        }
        .terminal-buttons {
            display: flex;
            gap: 8px;
        }
        .terminal-btn {
            width: 12px;
            height: 12px;
            border-radius: 50%;
        }
        .terminal-btn.close { background: #FF5F56; }
        .terminal-btn.minimize { background: #FFBD2E; }
        .terminal-btn.maximize { background: #27CA40; }
        .terminal-title {
            color: #8B949E;
            font-size: 0.75rem;
            flex: 1;
            text-align: center;
        }
        .terminal-body {
            padding: 1.5rem;
            min-height: 300px;
            color: #E6EDF3;
            font-size: 0.9rem;
            line-height: 1.6;
        }
        .terminal-line {
            display: flex;
            align-items: center;
            margin-bottom: 0.5rem;
        }
        .prompt {
            color: #7EE787;
            margin-right: 0.5rem;
            font-weight: bold;
        }
        .command {
            color: #79C0FF;
        }
        .cursor {
            color: #7EE787;
            animation: blink 1s infinite;
        }
        @keyframes blink {
            0%, 50% { opacity: 1; }
            51%, 100% { opacity: 0; }
        }
        .terminal-output {
            margin-top: 1rem;
        }
        .output-line {
            color: #8B949E;
            margin: 0.25rem 0;
        }
        .output-line:empty {
            height: 1rem;
        }
        .terminal-controls {
            padding: 0.75rem 1rem;
            background: #161B22;
            text-align: right;
        }
        .terminal-replay-btn {
            background: transparent;
            border: 1px solid #30363D;
            color: #8B949E;
            padding: 0.4rem 0.8rem;
            border-radius: 6px;
            cursor: pointer;
            font-size: 0.75rem;
            transition: all 0.2s;
        }
        .terminal-replay-btn:hover {
            background: #21262D;
            color: #E6EDF3;
        }

        /* Mobile Navigation */
        .hamburger-btn {
            display: none;
            flex-direction: column;
            gap: 5px;
            padding: 8px;
            background: transparent;
            border: none;
            cursor: pointer;
            z-index: 1001;
        }
        .hamburger-line {
            width: 24px;
            height: 2px;
            background: #374151;
            transition: all 0.3s;
        }
        .hamburger-active .hamburger-line:nth-child(1) {
            transform: rotate(45deg) translate(5px, 5px);
        }
        .hamburger-active .hamburger-line:nth-child(2) {
            opacity: 0;
        }
        .hamburger-active .hamburger-line:nth-child(3) {
            transform: rotate(-45deg) translate(5px, -5px);
        }

        @media (max-width: 768px) {
            .hamburger-btn {
                display: flex;
            }
            .nav-links {
                position: fixed;
                top: 0;
                right: -100%;
                width: 75%;
                max-width: 300px;
                height: 100vh;
                background: white;
                flex-direction: column;
                padding: 80px 2rem 2rem;
                box-shadow: -5px 0 20px rgba(0,0,0,0.1);
                transition: right 0.3s ease;
                z-index: 1000;
            }
            .nav-links.nav-open {
                right: 0;
            }
            .nav-links a {
                padding: 1rem 0;
                border-bottom: 1px solid #F3F4F6;
            }
            .terminal-body {
                padding: 1rem;
                min-height: 250px;
                font-size: 0.8rem;
            }
            .live-activity-notification {
                left: 10px;
                right: 10px;
                bottom: 10px;
            }
        }

        /* FAQ Accordion */
        .faq-item {
            cursor: pointer;
            transition: all 0.3s;
        }
        .faq-item h3::after {
            content: '+';
            float: right;
            font-weight: normal;
            transition: transform 0.3s;
        }
        .faq-item.faq-active h3::after {
            transform: rotate(45deg);
        }
        .faq-item p {
            max-height: 0;
            overflow: hidden;
            transition: max-height 0.3s, padding 0.3s;
            padding-top: 0;
        }
        .faq-item.faq-active p {
            max-height: 500px;
            padding-top: 0.75rem;
        }

        /* Urgency badge */
        .slots-urgent {
            color: #EF4444 !important;
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.7; }
        }
    `;
    document.head.appendChild(style);
}

// ============================================================
// PHASE 1: SCROLL PROGRESS INDICATOR & NAV STATE
// ============================================================

// Scroll progress indicator
function initScrollProgress() {
    const progressBar = document.getElementById('scrollProgress');
    if (!progressBar) return;

    function updateScrollProgress() {
        const windowHeight = window.innerHeight;
        const documentHeight = document.documentElement.scrollHeight;
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        const scrollPercent = (scrollTop / (documentHeight - windowHeight)) * 100;
        
        progressBar.style.width = Math.min(100, Math.max(0, scrollPercent)) + '%';
    }

    // Throttle scroll events for performance
    let ticking = false;
    window.addEventListener('scroll', () => {
        if (!ticking) {
            window.requestAnimationFrame(() => {
                updateScrollProgress();
                ticking = false;
            });
            ticking = true;
        }
    }, { passive: true });

    // Initial update
    updateScrollProgress();
}

// Sticky nav state change on scroll
function initNavStateChange() {
    const nav = document.querySelector('.nav');
    if (!nav) return;

    const scrollThreshold = 50; // pixels

    function updateNavState() {
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        
        if (scrollTop > scrollThreshold) {
            nav.classList.add('scrolled');
        } else {
            nav.classList.remove('scrolled');
        }
    }

    // Throttle scroll events
    let ticking = false;
    window.addEventListener('scroll', () => {
        if (!ticking) {
            window.requestAnimationFrame(() => {
                updateNavState();
                ticking = false;
            });
            ticking = true;
        }
    }, { passive: true });

    // Initial check
    updateNavState();
}

// ============================================================
// PHASE 1: BUTTON LOADING STATES
// ============================================================

function addLoadingState(button, originalText) {
    if (!button) return;
    
    button.disabled = true;
    button.setAttribute('data-original-text', originalText);
    
    // SECURITY: Use createElement instead of innerHTML
    const spinnerSpan = document.createElement('span');
    spinnerSpan.className = 'loading-spinner';
    spinnerSpan.setAttribute('aria-hidden', 'true');
    
    const textSpan = document.createElement('span');
    textSpan.className = 'loading-text';
    textSpan.textContent = 'Loading...';
    
    // Clear button content and add new elements
    button.textContent = '';
    button.appendChild(spinnerSpan);
    button.appendChild(textSpan);
    button.classList.add('btn-loading');
}

function removeLoadingState(button) {
    if (!button) return;
    
    const originalText = button.getAttribute('data-original-text');
    if (originalText) {
        // SECURITY: Use textContent instead of innerHTML for button text
        SecurityModule.safeSetContent(button, originalText);
        button.removeAttribute('data-original-text');
    }
    button.disabled = false;
    button.classList.remove('btn-loading');
}

// ============================================================
// DARK MODE TOGGLE
// ============================================================

// Initialize dark mode based on system preference or saved preference
function initDarkMode() {
    // Check for saved theme preference or default to system preference
    const savedTheme = localStorage.getItem('grid-theme');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    
    if (savedTheme === 'dark' || (!savedTheme && prefersDark)) {
        document.documentElement.setAttribute('data-theme', 'dark');
    } else {
        document.documentElement.setAttribute('data-theme', 'light');
    }
    
    // Listen for system theme changes
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
        if (!localStorage.getItem('grid-theme')) {
            document.documentElement.setAttribute('data-theme', e.matches ? 'dark' : 'light');
            updateThemeToggle();
        }
    });

    // Initialize theme toggle button
    initThemeToggle();
}

function initThemeToggle() {
    const themeToggle = document.getElementById('themeToggle');
    if (!themeToggle) return;

    // Set initial state
    updateThemeToggle();

    // Add click handler
    themeToggle.addEventListener('click', () => {
        toggleDarkMode();
    });

    // Keyboard support
    themeToggle.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            toggleDarkMode();
        }
    });
}

function updateThemeToggle() {
    const themeToggle = document.getElementById('themeToggle');
    if (!themeToggle) return;

    const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
    const isDark = currentTheme === 'dark';

    themeToggle.setAttribute('aria-pressed', isDark.toString());
    themeToggle.setAttribute('aria-label', isDark ? 'Switch to light mode' : 'Switch to dark mode');
    themeToggle.setAttribute('title', isDark ? 'Switch to light mode' : 'Switch to dark mode');
}

// Toggle dark mode (called from theme toggle button)
function toggleDarkMode() {
    const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('grid-theme', newTheme);
    
    // Update toggle button state
    updateThemeToggle();
}

// Console branding (use brand.js config when available)
(async function initConsoleBranding() {
    const theme = await waitForBrand();
    const iconEmoji = theme.brand?.iconEmoji || '🛞';
    const brandName = theme.brand?.name || 'GRID Analyzer';
    const description = theme.brand?.description || 'Privacy-first code analysis with local AI';
    const warningColor = theme.colors?.semantic?.warning || '#F59E0B';
    
    console.log(`%c${iconEmoji} ${brandName}`, `font-size: 24px; font-weight: bold; color: ${warningColor};`);
    console.log(`%c${description}`, 'font-size: 14px; color: #6B7280;');
    console.log('%c\n🔧 Developer? We\'re hiring! Check our GitHub.', 'font-size: 12px; color: #10B981;');
})();
