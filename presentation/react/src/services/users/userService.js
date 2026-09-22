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