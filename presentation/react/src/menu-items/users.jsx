// ==============================|| MENU ITEMS - JNS USERS ||============================== //

const users = {
  id: 'jns-users',
  title: 'JNS',
  type: 'group',
  children: [
    {
      id: 'users',
      title: 'Users',
      type: 'item',
      icon: 'ph ph-users',
      url: '/users'
    },
    {
      id: 'users-new',
      title: 'Create user',
      type: 'item',
      icon: 'ph ph-user-plus',
      url: '/users/new'
    },
    {
      id: 'kanban',
      title: 'Kanban',
      type: 'item',
      icon: 'ph ph-kanban',
      url: '/kanban'
    }
  ]
};

export default users;