// ==============================|| MENU ITEMS - TASKS ||============================== //

// The link is /tasks rather than a project-scoped URL, because the sidebar is
// rendered before any project is known and hard-coding an id here would break
// for every user who is not a member of that project.

const tasks = {
  id: 'tasks',
  title: 'Work',
  type: 'group',
  children: [
    {
      id: 'tasks-collapse',
      title: 'Tasks',
      type: 'collapse',
      icon: 'ph ph-check-square',
      children: [
        {
          id: 'task-list',
          title: 'All tasks',
          type: 'item',
          url: '/tasks'
        }
      ]
    }
  ]
};

export default tasks;
