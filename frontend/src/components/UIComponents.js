/**
 * Reusable UI Components for SWING MATRIX
 * Bloomberg-class Trading Interface Components
 */

import React from 'react';
import { motion } from 'framer-motion';
import theme from './design-system';

// ============================================================================
// CARD COMPONENT
// ============================================================================

export const Card = ({ 
  children, 
  variant = 'default', 
  className = '',
  glow = null,
  ...props 
}) => {
  const baseStyle = theme.components.card[variant] || theme.components.card.default;
  const glowStyle = glow ? theme.components.card.glow[glow] : {};

  const style = {
    ...baseStyle,
    ...glowStyle,
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={theme.animation.springGentle}
      style={style}
      className={`p-6 ${className}`}
      {...props}
    >
      {children}
    </motion.div>
  );
};

// ============================================================================
// BUTTON COMPONENT
// ============================================================================

export const Button = ({ 
  children, 
  variant = 'primary',
  size = 'md',
  fullWidth = false,
  leftIcon = null,
  rightIcon = null,
  loading = false,
  disabled = false,
  onClick,
  className = '',
  ...props 
}) => {
  const variantStyle = theme.components.button[variant] || theme.components.button.primary;
  
  const sizeClasses = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-5 py-2.5 text-base',
    lg: 'px-7 py-3.5 text-lg',
  };

  const baseClasses = `
    inline-flex items-center justify-center gap-2 rounded-lg 
    font-semibold transition-all duration-200
    hover:scale-105 active:scale-95
    disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100
    ${sizeClasses[size]}
    ${fullWidth ? 'w-full' : ''}
    ${className}
  `;

  return (
    <motion.button
      whileHover={{ scale: disabled || loading ? 1 : 1.05 }}
      whileTap={{ scale: disabled || loading ? 1 : 0.95 }}
      style={variantStyle}
      className={baseClasses}
      disabled={disabled || loading}
      onClick={onClick}
      {...props}
    >
      {loading && (
        <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
      )}
      {!loading && leftIcon && <span>{leftIcon}</span>}
      {children}
      {!loading && rightIcon && <span>{rightIcon}</span>}
    </motion.button>
  );
};

// ============================================================================
// BADGE COMPONENT
// ============================================================================

export const Badge = ({ 
  children, 
  variant = 'tierA',
  size = 'md',
  className = '',
  ...props 
}) => {
  const variantStyle = theme.components.badge[variant] || theme.components.badge.tierA;
  
  const sizeClasses = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-3 py-1 text-sm',
    lg: 'px-4 py-1.5 text-base',
  };

  return (
    <span
      style={variantStyle}
      className={`inline-flex items-center rounded-lg font-bold uppercase tracking-wide ${sizeClasses[size]} ${className}`}
      {...props}
    >
      {children}
    </span>
  );
};

// ============================================================================
// METRIC DISPLAY COMPONENT
// ============================================================================

export const MetricCard = ({ 
  label, 
  value, 
  subValue = null,
  trend = null, // 'up', 'down', 'neutral'
  color = 'default',
  size = 'md',
  icon = null,
  className = '',
}) => {
  const colorMap = {
    up: theme.colors.accent.emerald,
    down: theme.colors.accent.rose,
    neutral: theme.colors.text.secondary,
    cyan: theme.colors.accent.cyan,
    amber: theme.colors.accent.amber,
    default: theme.colors.text.primary,
  };

  const trendIcons = {
    up: '↗',
    down: '↘',
    neutral: '→',
  };

  const valueColor = trend ? colorMap[trend] : colorMap[color];

  const sizeClasses = {
    sm: { label: 'text-xs', value: 'text-2xl', sub: 'text-xs' },
    md: { label: 'text-sm', value: 'text-4xl', sub: 'text-sm' },
    lg: { label: 'text-base', value: 'text-5xl', sub: 'text-base' },
  };

  return (
    <div className={`bg-black/20 rounded-xl p-4 border border-gray-800/50 ${className}`}>
      <div className="flex items-center justify-between mb-2">
        <span className={`text-gray-500 font-semibold uppercase tracking-wider ${sizeClasses[size].label}`}>
          {label}
        </span>
        {icon && <span className="text-xl">{icon}</span>}
      </div>
      
      <motion.div
        key={value}
        initial={{ scale: 1.2, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={theme.animation.spring}
        className={`font-black mb-1 ${sizeClasses[size].value}`}
        style={{ color: valueColor }}
      >
        {trend && <span className="mr-2">{trendIcons[trend]}</span>}
        {value}
      </motion.div>
      
      {subValue && (
        <div className={`text-gray-600 font-mono ${sizeClasses[size].sub}`}>
          {subValue}
        </div>
      )}
    </div>
  );
};

// ============================================================================
// STATUS INDICATOR
// ============================================================================

export const StatusIndicator = ({ 
  status = 'active', // 'active', 'inactive', 'warning', 'error'
  label = '',
  showLabel = true,
  pulse = false,
  size = 'md',
  className = '',
}) => {
  const statusColors = {
    active: theme.colors.status.active,
    inactive: theme.colors.status.inactive,
    warning: theme.colors.status.warning,
    error: theme.colors.status.error,
  };

  const sizeMap = {
    sm: 'w-1.5 h-1.5',
    md: 'w-2 h-2',
    lg: 'w-3 h-3',
  };

  return (
    <div className={`inline-flex items-center gap-2 ${className}`}>
      <div className="relative">
        <div
          className={`${sizeMap[size]} rounded-full ${pulse ? 'animate-pulse' : ''}`}
          style={{ backgroundColor: statusColors[status] }}
        />
        {pulse && (
          <div
            className={`absolute inset-0 ${sizeMap[size]} rounded-full animate-ping`}
            style={{ backgroundColor: statusColors[status], opacity: 0.5 }}
          />
        )}
      </div>
      {showLabel && label && (
        <span className="text-xs font-mono text-gray-400 uppercase tracking-wider">
          {label}
        </span>
      )}
    </div>
  );
};

// ============================================================================
// PROGRESS BAR
// ============================================================================

export const ProgressBar = ({ 
  value = 0,
  max = 100,
  color = 'cyan',
  showValue = true,
  animated = true,
  height = 'md',
  className = '',
}) => {
  const percentage = Math.min((value / max) * 100, 100);
  
  const colorMap = {
    cyan: theme.colors.accent.cyan,
    emerald: theme.colors.accent.emerald,
    rose: theme.colors.accent.rose,
    amber: theme.colors.accent.amber,
    blue: theme.colors.accent.blue,
  };

  const heightMap = {
    sm: 'h-2',
    md: 'h-4',
    lg: 'h-6',
  };

  return (
    <div className={className}>
      {showValue && (
        <div className="flex justify-between items-center mb-2">
          <span className="text-xs text-gray-500 font-mono">
            {value.toFixed(0)} / {max}
          </span>
          <span className="text-xs text-gray-400 font-bold">
            {percentage.toFixed(1)}%
          </span>
        </div>
      )}
      <div className={`w-full bg-gray-800/50 rounded-full overflow-hidden border border-gray-800/30 ${heightMap[height]}`}>
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${percentage}%` }}
          transition={animated ? theme.animation.springGentle : { duration: 0 }}
          className={`${heightMap[height]} rounded-full`}
          style={{ background: `linear-gradient(90deg, ${colorMap[color]}, ${colorMap[color]}dd)` }}
        />
      </div>
    </div>
  );
};

// ============================================================================
// INPUT FIELD
// ============================================================================

export const Input = ({ 
  label = '',
  value,
  onChange,
  type = 'text',
  placeholder = '',
  error = null,
  helperText = null,
  leftIcon = null,
  rightIcon = null,
  fullWidth = true,
  disabled = false,
  className = '',
  ...props 
}) => {
  return (
    <div className={`${fullWidth ? 'w-full' : ''} ${className}`}>
      {label && (
        <label className="block text-sm font-semibold text-gray-400 mb-2 uppercase tracking-wider">
          {label}
        </label>
      )}
      <div className="relative">
        {leftIcon && (
          <div className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500">
            {leftIcon}
          </div>
        )}
        <input
          type={type}
          value={value}
          onChange={onChange}
          placeholder={placeholder}
          disabled={disabled}
          className={`
            w-full px-4 py-3 rounded-lg
            bg-gray-900/50 border transition-all duration-200
            font-mono text-gray-200
            placeholder-gray-600
            focus:outline-none focus:ring-2
            disabled:opacity-50 disabled:cursor-not-allowed
            ${error 
              ? 'border-rose-500/50 focus:border-rose-500 focus:ring-rose-500/30' 
              : 'border-gray-800 focus:border-cyan-500 focus:ring-cyan-500/30'
            }
            ${leftIcon ? 'pl-10' : ''}
            ${rightIcon ? 'pr-10' : ''}
          `}
          {...props}
        />
        {rightIcon && (
          <div className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500">
            {rightIcon}
          </div>
        )}
      </div>
      {error && (
        <p className="mt-2 text-sm text-rose-400 flex items-center gap-1">
          <span>⚠️</span> {error}
        </p>
      )}
      {helperText && !error && (
        <p className="mt-2 text-xs text-gray-600">
          {helperText}
        </p>
      )}
    </div>
  );
};

// ============================================================================
// TOOLTIP
// ============================================================================

export const Tooltip = ({ children, content, position = 'top' }) => {
  const [show, setShow] = React.useState(false);

  const positionClasses = {
    top: 'bottom-full left-1/2 -translate-x-1/2 mb-2',
    bottom: 'top-full left-1/2 -translate-x-1/2 mt-2',
    left: 'right-full top-1/2 -translate-y-1/2 mr-2',
    right: 'left-full top-1/2 -translate-y-1/2 ml-2',
  };

  return (
    <div 
      className="relative inline-block"
      onMouseEnter={() => setShow(true)}
      onMouseLeave={() => setShow(false)}
    >
      {children}
      {show && (
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.9 }}
          transition={{ duration: 0.15 }}
          className={`absolute ${positionClasses[position]} z-50 px-3 py-2 bg-gray-900 border border-gray-700 rounded-lg shadow-xl text-sm text-gray-300 whitespace-nowrap pointer-events-none`}
        >
          {content}
        </motion.div>
      )}
    </div>
  );
};

// ============================================================================
// LOADING SPINNER
// ============================================================================

export const Spinner = ({ size = 'md', color = 'cyan', className = '' }) => {
  const sizeMap = {
    sm: 'w-4 h-4',
    md: 'w-8 h-8',
    lg: 'w-12 h-12',
  };

  const colorMap = {
    cyan: theme.colors.accent.cyan,
    emerald: theme.colors.accent.emerald,
    amber: theme.colors.accent.amber,
  };

  return (
    <svg 
      className={`animate-spin ${sizeMap[size]} ${className}`} 
      xmlns="http://www.w3.org/2000/svg" 
      fill="none" 
      viewBox="0 0 24 24"
    >
      <circle 
        className="opacity-25" 
        cx="12" 
        cy="12" 
        r="10" 
        stroke={colorMap[color]} 
        strokeWidth="4"
      />
      <path 
        className="opacity-75" 
        fill={colorMap[color]} 
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
      />
    </svg>
  );
};

export default {
  Card,
  Button,
  Badge,
  MetricCard,
  StatusIndicator,
  ProgressBar,
  Input,
  Tooltip,
  Spinner,
};
