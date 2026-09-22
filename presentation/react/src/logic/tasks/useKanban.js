import { useMemo } from 'react';

// ==============================|| USE KANBAN (API 07 consumer) ||============================== //
//
// Pure grouping logic. Takes the task array exactly as API 07 returns it
// (see application/django/tasks/serializers.py TaskSerializer) and buckets it
// into the four stages the Trello card asks for. status_name values are the
// seeded ones in users/management/commands/seed_lookups.py.
//
// This hook does NOT fetch. The page passes in tasks from Edward's
// useProjectTasks hook (once merged) or from mock data meanwhile, so nothing
// about fetching or filtering is duplicated here.

export const KANBAN_COLUMNS = [
  { key: 'todo', title: 'To Do', statuses: ['New', 'Assigned'] },
  { key: 'in_progress', title: 'In Progress', statuses: ['In Progress'] },
  { key: 'review', title: 'Review / Blocked', statuses: ['Waiting for Information', 'Under Review'] },
  { key: 'done', title: 'Done', statuses: ['Completed'] }
];

export default function useKanban(tasks) {
  return useMemo(() => {
    const byStatus = new Map(KANBAN_COLUMNS.map((c) => [c.key, []]));
    const unmapped = [];

    for (const task of tasks ?? []) {
      const column = KANBAN_COLUMNS.find((c) => c.statuses.includes(task.status_name));
      if (column) byStatus.get(column.key).push(task);
      else unmapped.push(task); // a status added to the DB later shows up here instead of vanishing
    }

    return {
      columns: KANBAN_COLUMNS.map((c) => ({ ...c, tasks: byStatus.get(c.key) })),
      unmapped
    };
  }, [tasks]);
}