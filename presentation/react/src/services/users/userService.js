// ==============================|| USER SERVICE (API 02 / API 03) ||============================== //
//
// The only file in the users feature that knows where data comes from.
//
// TEMPORARY: returns mock data shaped exactly like the API 02 response
// (see application/django/users/serializers.py). Swap the body of getUsers()
// for a real call once the shared session/API client (owned by Ovanthi) is
// merged. Nothing above this layer needs to change.

const MOCK_USERS = [
  { user_id: 1, first_name: 'Ovanthi', last_name: 'Perera', email: 'ovanthi@jns.test', role_id: 1, role_name: 'Admin', availability: 'Full-time', status: 'Active' },
  { user_id: 2, first_name: 'Manat', last_name: 'Ka', email: 'manatka@jns.test', role_id: 2, role_name: 'Manager', availability: 'Full-time', status: 'Active' },
  { user_id: 3, first_name: 'Jane', last_name: 'Smith', email: 'jane@jns.test', role_id: 3, role_name: 'Employee', availability: 'Part-time', status: 'Active' },
  { user_id: 4, first_name: 'Sam', last_name: 'Lee', email: 'sam@jns.test', role_id: 5, role_name: 'Volunteer', availability: null, status: 'Inactive' }
];

// Simulates network latency so loading states are visible while developing.
const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

// API 02  GET /api/users
export async function getUsers() {
  await delay(400);
  return MOCK_USERS;
}

// Seeded values per users/management/commands/seed_lookups.py. ids are a guess
// until we can read them from the DB or a lookup endpoint (question f).
const MOCK_ROLES = [
  { role_id: 1, role_name: 'Admin' },
  { role_id: 2, role_name: 'Manager' },
  { role_id: 3, role_name: 'Employee' },
  { role_id: 4, role_name: 'Intern' },
  { role_id: 5, role_name: 'Volunteer' }
];

export async function getRoles() {
  await delay(200);
  return MOCK_ROLES;
}

// API 03  POST /api/users
//
// Mirrors the agreed contract: 201 with the created user, or 400 with
// { field: [message] } like DRF returns. The duplicate-email branch exists so
// the form's server-error handling can be developed before the backend is.
export async function createUser(payload) {
  await delay(400);

  if (MOCK_USERS.some((u) => u.email.toLowerCase() === payload.email.toLowerCase())) {
    const error = new Error('Validation failed');
    error.status = 400;
    error.fields = { email: ['A user with this email already exists in your organisation.'] };
    throw error;
  }

  const role = MOCK_ROLES.find((r) => r.role_id === Number(payload.role_id));
  const created = {
    user_id: MOCK_USERS.length + 1,
    first_name: payload.first_name,
    last_name: payload.last_name,
    email: payload.email,
    role_id: role.role_id,
    role_name: role.role_name,
    availability: payload.availability || null,
    status: 'Active'
  };

  MOCK_USERS.push(created);
  return created;
}