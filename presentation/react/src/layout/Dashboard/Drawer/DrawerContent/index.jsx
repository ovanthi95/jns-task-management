import PropTypes from 'prop-types';
import { useEffect, useMemo, useState } from 'react';

// react-bootstrap
import ListGroup from 'react-bootstrap/ListGroup';

// project imports
import NavItem from './NavItem';
import NavGroup from './NavGroup';
import menuItems from 'menu-items';
import { getSessionUser } from 'services/auth/sessionService';

function canSee(item, granted) {
  const required = item?.permissions || [];
  if (!required.length) return true;
  return required.every((permission) => granted.has(permission));
}

function filterMenuItem(item, granted) {
  if (!canSee(item, granted)) return null;

  if (!item.children?.length) return item;

  const children = item.children
    .map((child) => filterMenuItem(child, granted))
    .filter(Boolean);

  if (!children.length) return null;

  return { ...item, children };
}

// ==============================|| DRAWER CONTENT ||============================== //

export default function Navigation({ selectedItems, setSelectedItems, setSelectTab }) {
  const [selectedID, setSelectedID] = useState('');
  const [selectedLevel, setSelectedLevel] = useState(0);
  const [permissions, setPermissions] = useState(new Set());

  useEffect(() => {
    let active = true;

    getSessionUser()
      .then((user) => {
        if (!active) return;
        setPermissions(new Set(user?.permissions || []));
      })
      .catch(() => {
        if (active) setPermissions(new Set());
      });

    return () => {
      active = false;
    };
  }, []);

  const visibleMenuItems = useMemo(
    () =>
      menuItems.items
        .map((item) => filterMenuItem(item, permissions))
        .filter(Boolean),
    [permissions]
  );

  const lastItem = null;
  let lastItemIndex = visibleMenuItems.length - 1;
  let remItems = [];
  let lastItemId;

  if (lastItem && lastItem < visibleMenuItems.length) {
    lastItemId = visibleMenuItems[lastItem - 1].id;
    lastItemIndex = lastItem - 1;
    remItems = visibleMenuItems.slice(lastItem - 1, visibleMenuItems.length).map((item) => ({
      id: item.id,
      type: item.type,
      title: item.title,
      elements: item.children,
      icon: item.icon,
      ...(item.url && {
        url: item.url
      })
    }));
  }

  const navGroups = visibleMenuItems.slice(0, lastItemIndex + 1).map((item) => {
    switch (item.type) {
      case 'group':
        if (item.url && item.id !== lastItemId) {
          return (
            <ListGroup.Item key={item.id}>
              <NavItem item={item} level={1} isParents />
            </ListGroup.Item>
          );
        }

        return (
          <NavGroup
            key={item.id}
            setSelectedID={setSelectedID}
            setSelectedItems={setSelectedItems}
            setSelectedLevel={setSelectedLevel}
            selectedLevel={selectedLevel}
            selectedID={selectedID}
            selectedItems={selectedItems}
            lastItem={lastItem}
            remItems={remItems}
            lastItemId={lastItemId}
            item={item}
            setSelectTab={setSelectTab ?? (() => {})}
          />
        );
      default:
        return (
          <h6 key={item.id} className="text-danger align-items-center">
            Fix - Navigation Group
          </h6>
        );
    }
  });

  return <ul className="pc-navbar">{navGroups}</ul>;
}

Navigation.propTypes = {
  selectedItems: PropTypes.any,
  setSelectedItems: PropTypes.oneOfType([PropTypes.func, PropTypes.any]),
  setSelectTab: PropTypes.oneOfType([PropTypes.func, PropTypes.any])
};
