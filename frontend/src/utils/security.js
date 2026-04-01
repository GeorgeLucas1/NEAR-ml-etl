/**
 * PC Health Monitor - Security Utilities
 * XSS Protection and Input Validation
 */

/**
 * Escapes HTML special characters to prevent XSS
 * @param {string} str - Input string
 * @returns {string} - Escaped string safe for HTML
 */
export function escapeHtml(str) {
  if (!str) return ''
  
  const map = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#x27;',
    '/': '&#x2F;',
    '`': '&#96;'
  }
  
  return String(str).replace(/[&<>"'/`]/g, char => map[char])
}

/**
 * Sanitizes a metric value for safe display
 * @param {*} value - Input value
 * @param {string} type - Expected type ('number', 'string', 'boolean')
 * @returns {*} - Sanitized value
 */
export function sanitizeMetricValue(value, type = 'string') {
  if (value === null || value === undefined) return null
  
  switch (type) {
    case 'number':
      return typeof value === 'number' && !isNaN(value) && isFinite(value) ? value : null
    case 'string':
      return escapeHtml(String(value).slice(0, 500))
    case 'boolean':
      return Boolean(value)
    default:
      return escapeHtml(String(value))
  }
}

/**
 * Validates API response structure
 * @param {Object} data - API response
 * @param {string[]} requiredFields - Required fields
 * @returns {boolean} - Whether data is valid
 */
export function validateApiResponse(data, requiredFields = []) {
  if (!data || typeof data !== 'object') return false
  
  for (const field of requiredFields) {
    if (!(field in data)) return false
  }
  
  return true
}

/**
 * Sanitizes URL for safe use in fetch
 * @param {string} url - Input URL
 * @returns {string|null} - Validated URL or null
 */
export function sanitizeUrl(url) {
  if (!url) return null
  
  try {
    const parsed = new URL(url)
    // Only allow http and https
    if (!['http:', 'https:'].includes(parsed.protocol)) return null
    return parsed.href
  } catch {
    return null
  }
}

/**
 * Prevents prototype pollution by checking dangerous keys
 * @param {Object} obj - Input object
 * @returns {Object} - Safe object copy
 */
export function safeObjectCopy(obj) {
  if (!obj || typeof obj !== 'object') return {}
  
  const dangerousKeys = ['__proto__', 'constructor', 'prototype']
  const safe = {}
  
  for (const key of Object.keys(obj)) {
    if (!dangerousKeys.includes(key)) {
      safe[key] = obj[key]
    }
  }
  
  return safe
}

/**
 * Rate limiter for API calls
 */
export class RateLimiter {
  constructor(maxCalls = 10, timeWindow = 1000) {
    this.maxCalls = maxCalls
    this.timeWindow = timeWindow
    this.calls = []
  }
  
  canMakeCall() {
    const now = Date.now()
    // Remove old calls outside the time window
    this.calls = this.calls.filter(time => now - time < this.timeWindow)
    
    if (this.calls.length >= this.maxCalls) {
      return false
    }
    
    this.calls.push(now)
    return true
  }
}
