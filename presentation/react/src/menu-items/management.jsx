const management = {
  id: 'worklink-management',
  title: 'Management',
  type: 'group',
  children: [
    {
      id: 'projects',
      title: 'Projects',
      type: 'item',
      icon: 'ph ph-folder-open',
      url: '/projects'
    },
    {
      id: 'users',
      title: 'Users',
      type: 'item',
      icon: 'ph ph-users',
      url: '/users',
      permissions: ['manage_users']
    },
    {
      id: 'roles-permissions',
      title: 'Roles & permissions',
      type: 'item',
      icon: 'ph ph-shield-check',
      url: '/roles',
      permissions: ['manage_roles']
    },
    {
      id: 'history',
      title: 'History',
      type: 'item',
      icon: 'ph ph-clock-counter-clockwise',
      url: '/history',
      permissions: ['view_history']
    },
    {
      id: 'workload',
      title: 'Workload',
      type: 'item',
      icon: 'ph ph-chart-bar',
      url: '/workload',
      permissions: ['view_workload']
    }
  ]
};

export default management;
