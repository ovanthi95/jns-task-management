// Shared role options introduced with APIs 02/03
// Owner: Manatka

// Shared role options for the prototype (playbook section 5 / 9.2).
// Ids match seed_lookups.py on a freshly seeded database.
// The backend still validates role_id; this is display only.

export const ROLES = [
  { role_id: 1, role_name: 'Admin' },
  { role_id: 2, role_name: 'Manager' },
  { role_id: 3, role_name: 'Employee' },
  { role_id: 4, role_name: 'Intern' },
  { role_id: 5, role_name: 'Volunteer' }
];