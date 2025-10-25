/**
 * SWING MATRIX Design System
 * Bloomberg-class Trading Interface
 * Based on industry best practices for financial dashboards
 */

// ============================================================================
// COLOR PALETTE
// ============================================================================

export const colors = {
  // Background Gradients (Dark Theme - avoiding pure black #000)
  bg: {
    primary: '#0B0E14',      // Main dark
    secondary: '#141921',    // Slightly lighter
    tertiary: '#1a1f2e',     // Card backgrounds
    elevated: '#1f2937',     // Elevated surfaces
    input: '#0f1419',        // Input fields
  },

  // Accent Colors (Neon highlights on dark)
  accent: {
    cyan: '#00F6FF',         // Primary action, long positions
    magenta: '#FF3CAD',      // Short positions, errors
    amber: '#FFB300',        // Warnings, B-tier
    emerald: '#10b981',      // Success, profit, up movements
    rose: '#f43f5e',         // Danger, loss, down movements
    purple: '#a855f7',       // Micro confluence
    blue: '#3b82f6',         // Bid depth, info
  },

  // Text (off-white for readability, 87% opacity per Material Design)
  text: {
    primary: '#e5e7eb',      // ~87% white - main text
    secondary: '#9ca3af',    // ~60% white - secondary text
    tertiary: '#6b7280',     // ~38% white - subtle text
    disabled: '#4b5563',     // Disabled state
    inverse: '#0B0E14',      // Text on light backgrounds
  },

  // Borders & Dividers (subtle, desaturated)
  border: {
    default: 'rgba(255, 255, 255, 0.08)',
    hover: 'rgba(255, 255, 255, 0.12)',
    focus: 'rgba(0, 246, 255, 0.3)',    // Cyan glow
    success: 'rgba(16, 185, 129, 0.3)',  // Emerald
    error: 'rgba(244, 63, 94, 0.3)',     // Rose
    warning: 'rgba(255, 179, 0, 0.3)',   // Amber
  },

  // Status Colors
  status: {
    active: '#10b981',       // Green dot
    inactive: '#6b7280',     // Gray dot
    warning: '#FFB300',      // Amber dot
    error: '#f43f5e',        // Red dot
  },

  // Chart-specific (consistent with trading convention)
  chart: {
    bullish: '#10b981',      // Green candles, up moves
    bearish: '#f43f5e',      // Red candles, down moves
    neutral: '#6b7280',      // Gray for flat
    volume: '#3b82f6',       // Blue for volume bars
    grid: '#1f2937',         // Subtle grid lines
  },
};

// ============================================================================
// TYPOGRAPHY
// ============================================================================

export const typography = {
  fonts: {
    primary: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
    mono: '"IBM Plex Mono", "Fira Code", Consolas, Monaco, monospace',
    display: '"Space Grotesk", "Inter", sans-serif',  // For headers
  },

  sizes: {
    xs: '0.75rem',      // 12px
    sm: '0.875rem',     // 14px
    base: '1rem',       // 16px
    lg: '1.125rem',     // 18px
    xl: '1.25rem',      // 20px
    '2xl': '1.5rem',    // 24px
    '3xl': '1.875rem',  // 30px
    '4xl': '2.25rem',   // 36px
    '5xl': '3rem',      // 48px
    '6xl': '3.75rem',   // 60px
  },

  weights: {
    normal: 400,
    medium: 500,
    semibold: 600,
    bold: 700,
    black: 900,
  },

  lineHeights: {
    tight: 1.2,
    normal: 1.5,
    relaxed: 1.75,
  },
};

// ============================================================================
// SPACING (8px grid system)
// ============================================================================

export const spacing = {
  0: '0',
  1: '0.25rem',   // 4px
  2: '0.5rem',    // 8px
  3: '0.75rem',   // 12px
  4: '1rem',      // 16px
  5: '1.25rem',   // 20px
  6: '1.5rem',    // 24px
  8: '2rem',      // 32px
  10: '2.5rem',   // 40px
  12: '3rem',     // 48px
  16: '4rem',     // 64px
  20: '5rem',     // 80px
  24: '6rem',     // 96px
};

// ============================================================================
// SHADOWS (subtle elevation)
// ============================================================================

export const shadows = {
  none: 'none',
  sm: '0 1px 2px 0 rgba(0, 0, 0, 0.3)',
  default: '0 1px 3px 0 rgba(0, 0, 0, 0.4), 0 1px 2px 0 rgba(0, 0, 0, 0.3)',
  md: '0 4px 6px -1px rgba(0, 0, 0, 0.4), 0 2px 4px -1px rgba(0, 0, 0, 0.3)',
  lg: '0 10px 15px -3px rgba(0, 0, 0, 0.4), 0 4px 6px -2px rgba(0, 0, 0, 0.3)',
  xl: '0 20px 25px -5px rgba(0, 0, 0, 0.4), 0 10px 10px -5px rgba(0, 0, 0, 0.3)',
  glow: {
    cyan: '0 0 20px rgba(0, 246, 255, 0.3)',
    emerald: '0 0 20px rgba(16, 185, 129, 0.3)',
    rose: '0 0 20px rgba(244, 63, 94, 0.3)',
    amber: '0 0 20px rgba(255, 179, 0, 0.3)',
  },
};

// ============================================================================
// BORDER RADIUS
// ============================================================================

export const borderRadius = {
  none: '0',
  sm: '0.25rem',    // 4px
  default: '0.5rem', // 8px
  md: '0.75rem',    // 12px
  lg: '1rem',       // 16px
  xl: '1.5rem',     // 24px
  full: '9999px',   // Pills/circles
};

// ============================================================================
// ANIMATION TIMING
// ============================================================================

export const animation = {
  duration: {
    fast: '150ms',
    normal: '300ms',
    slow: '500ms',
  },

  easing: {
    linear: 'linear',
    easeIn: 'cubic-bezier(0.4, 0, 1, 1)',
    easeOut: 'cubic-bezier(0, 0, 0.2, 1)',
    easeInOut: 'cubic-bezier(0.4, 0, 0.2, 1)',
    spring: 'cubic-bezier(0.34, 1.56, 0.64, 1)',
  },

  // Framer Motion presets
  spring: {
    type: 'spring',
    stiffness: 500,
    damping: 30,
  },

  springGentle: {
    type: 'spring',
    stiffness: 300,
    damping: 30,
  },

  fade: {
    initial: { opacity: 0 },
    animate: { opacity: 1 },
    exit: { opacity: 0 },
  },

  slideUp: {
    initial: { y: 20, opacity: 0 },
    animate: { y: 0, opacity: 1 },
    exit: { y: -20, opacity: 0 },
  },

  scale: {
    initial: { scale: 0.9, opacity: 0 },
    animate: { scale: 1, opacity: 1 },
    exit: { scale: 0.9, opacity: 0 },
  },
};

// ============================================================================
// BREAKPOINTS (Responsive)
// ============================================================================

export const breakpoints = {
  xs: '480px',
  sm: '640px',
  md: '768px',
  lg: '1024px',
  xl: '1280px',
  '2xl': '1536px',
};

// ============================================================================
// Z-INDEX LAYERS
// ============================================================================

export const zIndex = {
  base: 0,
  dropdown: 1000,
  sticky: 1020,
  fixed: 1030,
  modalBackdrop: 1040,
  modal: 1050,
  popover: 1060,
  tooltip: 1070,
};

// ============================================================================
// COMPONENT VARIANTS (Pre-defined styles)
// ============================================================================

export const components = {
  // Card variants
  card: {
    default: {
      background: `linear-gradient(135deg, ${colors.bg.tertiary} 0%, ${colors.bg.elevated} 100%)`,
      border: `1px solid ${colors.border.default}`,
      borderRadius: borderRadius.xl,
      backdropFilter: 'blur(12px)',
      boxShadow: shadows.md,
    },
    elevated: {
      background: `linear-gradient(135deg, ${colors.bg.elevated} 0%, ${colors.bg.tertiary} 100%)`,
      border: `1px solid ${colors.border.hover}`,
      borderRadius: borderRadius.xl,
      backdropFilter: 'blur(16px)',
      boxShadow: shadows.lg,
    },
    glow: {
      long: {
        border: `2px solid ${colors.border.success}`,
        boxShadow: shadows.glow.emerald,
      },
      short: {
        border: `2px solid ${colors.border.error}`,
        boxShadow: shadows.glow.rose,
      },
      tierA: {
        border: `2px solid ${colors.accent.cyan}`,
        boxShadow: shadows.glow.cyan,
      },
      tierB: {
        border: `2px solid ${colors.accent.amber}`,
        boxShadow: shadows.glow.amber,
      },
    },
  },

  // Button variants
  button: {
    primary: {
      background: colors.accent.cyan,
      color: colors.text.inverse,
      border: 'none',
      fontWeight: typography.weights.semibold,
      boxShadow: shadows.glow.cyan,
    },
    success: {
      background: colors.accent.emerald,
      color: colors.text.inverse,
      border: 'none',
      fontWeight: typography.weights.semibold,
      boxShadow: shadows.glow.emerald,
    },
    danger: {
      background: colors.accent.rose,
      color: colors.text.inverse,
      border: 'none',
      fontWeight: typography.weights.semibold,
      boxShadow: shadows.glow.rose,
    },
    ghost: {
      background: 'transparent',
      color: colors.text.primary,
      border: `1px solid ${colors.border.default}`,
      fontWeight: typography.weights.medium,
    },
  },

  // Badge/Tag variants
  badge: {
    tierA: {
      background: 'rgba(0, 246, 255, 0.15)',
      border: `1px solid ${colors.accent.cyan}`,
      color: colors.accent.cyan,
      fontWeight: typography.weights.bold,
    },
    tierB: {
      background: 'rgba(255, 179, 0, 0.15)',
      border: `1px solid ${colors.accent.amber}`,
      color: colors.accent.amber,
      fontWeight: typography.weights.bold,
    },
    success: {
      background: 'rgba(16, 185, 129, 0.15)',
      border: `1px solid ${colors.accent.emerald}`,
      color: colors.accent.emerald,
      fontWeight: typography.weights.semibold,
    },
    error: {
      background: 'rgba(244, 63, 94, 0.15)',
      border: `1px solid ${colors.accent.rose}`,
      color: colors.accent.rose,
      fontWeight: typography.weights.semibold,
    },
  },
};

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

export const utils = {
  // Generate gradient background
  gradientBg: (from = colors.bg.primary, to = colors.bg.secondary, deg = 135) => 
    `linear-gradient(${deg}deg, ${from} 0%, ${to} 100%)`,

  // Generate glow effect
  glow: (color, intensity = 0.3) => 
    `0 0 20px rgba(${color}, ${intensity})`,

  // Responsive helper
  mediaQuery: (breakpoint) => 
    `@media (min-width: ${breakpoints[breakpoint]})`,

  // Alpha channel helper
  alpha: (color, opacity) => 
    `rgba(${color}, ${opacity})`,
};

// ============================================================================
// EXPORT DEFAULT THEME
// ============================================================================

const theme = {
  colors,
  typography,
  spacing,
  shadows,
  borderRadius,
  animation,
  breakpoints,
  zIndex,
  components,
  utils,
};

export default theme;
