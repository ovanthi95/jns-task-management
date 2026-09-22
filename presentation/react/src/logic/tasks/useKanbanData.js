import useSWR from 'swr';

// ==============================|| USE KANBAN DATA (temporary mock) ||============================== //
//
// The ONLY file the Kanban page fetches through. Once Edward's
// feature/edward-tasks-ui is on main, replace the body of this hook with his
// useProjectTasks(projectId) and delete MOCK_TASKS. Nothing else changes.
//
// Task shape mirrors TaskSerializer; status/priority names mirror seed_lookups.

const person = (user_id, first_name, last_name) => ({ user_id, first_name, last_name, assignment_role: null });

const MOCK_TASKS = [
  { task_id: 1, status_name: 'New', priority_name: 'High', title: 'Collect bank statements', due_date: '2026-10-03', assignees: [person(3, 'Jane', 'Smith')] },
  { task_id: 2, status_name: 'Assigned', priority_name: 'Medium', title: 'Reconcile Q3 ledger', due_date: '2026-10-10', assignees: [person(2, 'Manat', 'Ka')] },
  { task_id: 3, status_name: 'In Progress', priority_name: 'Urgent', title: 'Prepare GST return', due_date: '2026-09-28', assignees: [person(3, 'Jane', 'Smith')] },
  { task_id: 4, status_name: 'Waiting for Information', priority_name: 'Low', title: 'Confirm supplier invoices', due_date: '2026-10-15', assignees: [] },
  { task_id: 5, status_name: 'Under Review', priority_name: 'High', title: 'Review depreciation schedule', due_date: '2026-10-01', assignees: [person(2, 'Manat', 'Ka')] },
  { task_id: 6, status_name: 'Completed', priority_name: 'Medium', title: 'Set up chart of accounts', due_date: '2026-09-15', assignees: [person(1, 'Ovanthi', 'Perera')] }
];

const fetchMock = () => new Promise((resolve) => setTimeout(() => resolve(MOCK_TASKS), 400));

export default function useKanbanData() {
  const { data, error, isLoading } = useSWR('kanban-mock', fetchMock);

  return {
    tasks: data ?? [],
    loading: isLoading,
    error,
    projectName: 'Annual Accounts 2026'
  };
}