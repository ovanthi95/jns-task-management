/**
 * Presentation helpers shared by the tasks views.
 *
 * These are here rather than in the logic layer because nothing below the view
 * needs them - a badge colour and a date string are decisions about how a row
 * looks, not about what the data is.
 *
 * Nothing here imports the fixtures. The names come down with the rows from
 * API 07, so these only ever map an id to a colour.
 */

/**
 * Formats the plain 'YYYY-MM-DD' a DateField puts on the wire.
 *
 * The string is split by hand instead of going through Date, because
 * new Date('2026-09-30') is parsed as UTC midnight and renders as the 29th for
 * anyone west of Greenwich. A due date that silently shifts a day is worse
 * than one that is not prettified at all.
 */
export function formatDate(value) {
  if (!value) return '-';

  const [year, month, day] = value.split('-');
  if (!year || !month || !day) return value;

  const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  return `${Number(day)} ${monthNames[Number(month) - 1]} ${year}`;
}

/**
 * estimated_hours and actual_hours arrive as strings such as '12.00', because
 * DRF coerces decimals to strings. Null means not recorded, which is different
 * from zero and is shown as a dash rather than '0'.
 */
export function formatHours(value) {
  if (value === null || value === undefined || value === '') return '-';
  return Number(value).toFixed(2);
}

// Ids come from seed_lookups.py. Anything unmapped falls through to a neutral
// badge rather than throwing, so a lookup row added later still renders.
const STATUS_VARIANTS = {
  1: 'secondary', // New
  2: 'info', // Assigned
  3: 'primary', // In Progress
  4: 'warning', // Waiting for Information
  5: 'warning', // Under Review
  6: 'success' // Completed
};

const PRIORITY_VARIANTS = {
  1: 'secondary', // Low
  2: 'info', // Medium
  3: 'warning', // High
  4: 'danger' // Urgent
};

export function statusVariant(statusId) {
  return STATUS_VARIANTS[statusId] ?? 'secondary';
}

export function priorityVariant(priorityId) {
  return PRIORITY_VARIANTS[priorityId] ?? 'secondary';
}
