/**
 * Stand-in data for the tasks pages, shaped exactly like the responses
 * API 06 and API 07 return.
 *
 * It lives beside the service rather than inside the views so that the swap to
 * real HTTP touches one file and no component. Anything the views read from a
 * task here is a field the real endpoint already returns:
 *
 *   application/django/tasks/serializers.py  TaskSerializer
 *
 * Decimals are strings and dates are plain ISO strings because that is what
 * Django REST Framework puts on the wire, not because the UI wants them that
 * way. Getting this wrong in the mock would hide a formatting bug until the
 * endpoint was connected.
 *
 * Lookup values match users/management/commands/seed_lookups.py, so the ids in
 * a dropdown here are the ids the seeded database actually holds.
 */

// Task types, statuses and priorities are global lookups. There is no endpoint
// for them on the agreed REST list yet, so the dropdowns read them from here.
export const TASK_TYPES = [
  { task_type_id: 1, type_name: 'Accounting' },
  { task_type_id: 2, type_name: 'Taxation' },
  { task_type_id: 3, type_name: 'Funding Application' }
];

export const TASK_STATUSES = [
  { status_id: 1, status_name: 'New' },
  { status_id: 2, status_name: 'Assigned' },
  { status_id: 3, status_name: 'In Progress' },
  { status_id: 4, status_name: 'Waiting for Information' },
  { status_id: 5, status_name: 'Under Review' },
  { status_id: 6, status_name: 'Completed' }
];

export const PRIORITIES = [
  { priority_id: 1, priority_name: 'Low' },
  { priority_id: 2, priority_name: 'Medium' },
  { priority_id: 3, priority_name: 'High' },
  { priority_id: 4, priority_name: 'Urgent' }
];

// Projects the signed-in user is a member of. API 05 (Jessie) will supply
// these; the selector on the list page needs something to point at until then.
export const PROJECTS = [
  { project_id: 1, project_name: 'Community Grant Round 2026' },
  { project_id: 2, project_name: 'Annual Accounts Clean-up' }
];

// Members of each project. API 06 will only accept an assignee who holds a
// ProjectMember row, so the assignee dropdown is per project rather than a
// list of every user in the organisation.
export const PROJECT_MEMBERS = {
  1: [
    { user_id: 11, first_name: 'Jane', last_name: 'Smith' },
    { user_id: 12, first_name: 'Ravi', last_name: 'Patel' },
    { user_id: 13, first_name: 'Aroha', last_name: 'Williams' }
  ],
  2: [
    { user_id: 12, first_name: 'Ravi', last_name: 'Patel' },
    { user_id: 14, first_name: 'Tom', last_name: 'Becker' }
  ]
};

// Seed rows for API 07. Kept in one flat array keyed by project_id so the
// service can filter it the same way the endpoint filters the queryset.
export const TASKS = [
  {
    task_id: 101,
    project_id: 1,
    task_type_id: 3,
    task_type_name: 'Funding Application',
    status_id: 3,
    status_name: 'In Progress',
    priority_id: 4,
    priority_name: 'Urgent',
    title: 'Draft the funding application narrative',
    description: 'First pass at sections 1 to 4, ready for the manager to review.',
    start_date: '2026-09-21',
    due_date: '2026-09-30',
    estimated_hours: '12.00',
    actual_hours: '4.50',
    assignees: [{ user_id: 11, first_name: 'Jane', last_name: 'Smith', assignment_role: null }],
    created_by_id: 1,
    created_at: '2026-09-21T09:15:00Z',
    updated_at: '2026-09-22T08:02:00Z'
  },
  {
    task_id: 102,
    project_id: 1,
    task_type_id: 1,
    task_type_name: 'Accounting',
    status_id: 2,
    status_name: 'Assigned',
    priority_id: 2,
    priority_name: 'Medium',
    title: 'Reconcile the Q3 donations ledger',
    description: null,
    start_date: '2026-09-23',
    due_date: '2026-10-07',
    estimated_hours: '8.00',
    actual_hours: null,
    assignees: [{ user_id: 12, first_name: 'Ravi', last_name: 'Patel', assignment_role: null }],
    created_by_id: 1,
    created_at: '2026-09-20T14:40:00Z',
    updated_at: '2026-09-20T14:40:00Z'
  },
  {
    task_id: 103,
    project_id: 1,
    task_type_id: 2,
    task_type_name: 'Taxation',
    status_id: 6,
    status_name: 'Completed',
    priority_id: 1,
    priority_name: 'Low',
    title: 'File the GST return for August',
    description: 'Filed and acknowledged.',
    start_date: '2026-09-01',
    due_date: '2026-09-15',
    estimated_hours: '3.00',
    actual_hours: '2.75',
    // Two rows, because task_assignees allows several per task even though
    // API 06 creates one. The table has to render that without a change.
    assignees: [
      { user_id: 13, first_name: 'Aroha', last_name: 'Williams', assignment_role: 'Reviewer' },
      { user_id: 11, first_name: 'Jane', last_name: 'Smith', assignment_role: null }
    ],
    created_by_id: 1,
    created_at: '2026-09-01T08:00:00Z',
    updated_at: '2026-09-15T16:30:00Z'
  },
  {
    task_id: 201,
    project_id: 2,
    task_type_id: 1,
    task_type_name: 'Accounting',
    status_id: 1,
    status_name: 'New',
    priority_id: 3,
    priority_name: 'High',
    title: 'Chase the missing supplier invoices',
    description: null,
    start_date: null,
    due_date: '2026-10-10',
    estimated_hours: null,
    actual_hours: null,
    assignees: [{ user_id: 14, first_name: 'Tom', last_name: 'Becker', assignment_role: null }],
    created_by_id: 1,
    created_at: '2026-09-19T11:05:00Z',
    updated_at: '2026-09-19T11:05:00Z'
  }
];

// The signed-in user, until Ovanthi's shared auth piece lands. API 06 takes
// created_by from the token, so nothing sends this; it is only here so the
// 201 the mock hands back looks like the real one.
export const CURRENT_USER_ID = 1;
