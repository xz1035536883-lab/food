/**
 * Common utility functions.
 */

/**
 * Format date to YYYY-MM-DD.
 */
function formatDate(date) {
  if (typeof date === 'string') return date;
  const d = date || new Date();
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

/**
 * Get today's date as YYYY-MM-DD string.
 */
function getToday() {
  return formatDate(new Date());
}

function parseDateString(dateString) {
  if (!dateString) return new Date();
  const parts = dateString.split('-').map((item) => parseInt(item, 10));
  return new Date(parts[0], parts[1] - 1, parts[2]);
}

function addDays(dateString, offset) {
  const date = parseDateString(dateString);
  date.setDate(date.getDate() + offset);
  return formatDate(date);
}

/**
 * Format timestamp to readable date-time.
 */
function formatDateTime(isoString) {
  if (!isoString) return '';
  const d = new Date(isoString);
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  const hour = String(d.getHours()).padStart(2, '0');
  const min = String(d.getMinutes()).padStart(2, '0');
  return `${year}-${month}-${day} ${hour}:${min}`;
}

/**
 * Format time only HH:MM.
 */
function formatTime(isoString) {
  if (!isoString) return '';
  const d = new Date(isoString);
  const hour = String(d.getHours()).padStart(2, '0');
  const min = String(d.getMinutes()).padStart(2, '0');
  return `${hour}:${min}`;
}

/**
 * Get meal type label.
 */
function getMealLabel(type) {
  const labels = {
    breakfast: '早餐',
    lunch: '午餐',
    dinner: '晚餐',
    snack: '零食',
  };
  return labels[type] || type;
}

/**
 * Get calorie progress color based on percentage.
 */
function getCalorieColor(percent) {
  if (percent > 100) return '#F44336';
  if (percent > 80) return '#FF9800';
  return '#4CAF50';
}

/**
 * Show toast with loading state.
 */
function showLoading(title = '加载中...') {
  wx.showLoading({ title, mask: true });
}

function hideLoading() {
  wx.hideLoading();
}

module.exports = {
  formatDate,
  getToday,
  parseDateString,
  addDays,
  formatDateTime,
  formatTime,
  getMealLabel,
  getCalorieColor,
  showLoading,
  hideLoading,
};
