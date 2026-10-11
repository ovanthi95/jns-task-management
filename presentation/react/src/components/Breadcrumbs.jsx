import { useEffect, useCallback, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';

import Breadcrumb from 'react-bootstrap/Breadcrumb';
import Col from 'react-bootstrap/Col';
import Row from 'react-bootstrap/Row';

import { APP_DEFAULT_PATH } from 'config';
import navigation from 'menu-items';

function projectBreadcrumbTitle(pathname) {
  if (pathname === '/projects') return 'Projects';
  if (pathname === '/projects/new') return 'New project';
  if (/^\/projects\/[^/]+\/edit$/.test(pathname)) return 'Edit project';
  if (/^\/projects\/[^/]+\/tasks$/.test(pathname)) return 'Tasks';
  if (/^\/projects\/[^/]+\/tasks\/new$/.test(pathname)) return 'New task';
  if (/^\/projects\/[^/]+\/tasks\/[^/]+$/.test(pathname)) return 'Task';
  if (/^\/projects\/[^/]+\/tasks\/[^/]+\/edit$/.test(pathname)) return 'Edit task';
  if (/^\/projects\/[^/]+\/tasks\/[^/]+\/comments$/.test(pathname)) return 'Comments';
  if (/^\/projects\/[^/]+\/tasks\/[^/]+\/audit$/.test(pathname)) return 'Task audit';
  if (/^\/projects\/[^/]+\/kanban$/.test(pathname)) return 'Kanban';
  return null;
}

export default function Breadcrumbs() {
  const location = useLocation();
  const [main, setMain] = useState({});
  const [item, setItem] = useState({});

  const getCollapse = useCallback(
    (menuItem) => {
      if (!menuItem.children) return;

      const exactChild = menuItem.children.find(
        (child) =>
          child.type === 'item'
          && (
            location.pathname === child.url
            || location.pathname.startsWith(`${child.url}/`)
          )
      );

      if (!exactChild) return;

      setMain({
        type: 'collapse',
        title: typeof menuItem.title === 'string' ? menuItem.title : undefined,
        url: menuItem.children.find((child) => child.type === 'item')?.url || APP_DEFAULT_PATH
      });

      setItem({
        type: 'item',
        title: projectBreadcrumbTitle(location.pathname) || (
          typeof exactChild.title === 'string' ? exactChild.title : ''
        ),
        breadcrumbs: exactChild.breadcrumbs !== false
      });
    },
    [location.pathname]
  );

  useEffect(() => {
    setMain({});
    setItem({});

    if (location.pathname.startsWith('/projects')) {
      const projectsGroup = navigation.items.find(
        (navItem) => navItem.type === 'group' && navItem.id === 'worklink-management'
      );

      if (projectsGroup) {
        getCollapse(projectsGroup);
      }
      return;
    }

    navigation.items.forEach((navItem) => {
      if (navItem.type === 'group') getCollapse(navItem);
    });
  }, [location.pathname, getCollapse]);

  if (item.type !== 'item' || item.breadcrumbs === false) {
    return null;
  }

  const title = item.title || '';

  return (
    <div className="page-header">
      <div className="page-block">
        <Row className="align-items-center">
          <Col md={12} className="page-header-title text-capitalize">
            <h5>{title}</h5>
          </Col>
          <Col md={12}>
            <Breadcrumb listProps={{ style: { marginBottom: 0 } }}>
              <Breadcrumb.Item linkAs={Link} linkProps={{ to: APP_DEFAULT_PATH }}>
                Home
              </Breadcrumb.Item>
              {main.type === 'collapse' && (
                <Breadcrumb.Item
                  linkAs={Link}
                  linkProps={{ to: main.url }}
                >
                  {main.title}
                </Breadcrumb.Item>
              )}
              <Breadcrumb.Item active>{title}</Breadcrumb.Item>
            </Breadcrumb>
          </Col>
        </Row>
      </div>
    </div>
  );
}
