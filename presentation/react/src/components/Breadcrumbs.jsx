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

function findBreadcrumbMenuItem(items, pathname) {
  for (const item of items || []) {
    if (item.type === 'group' && item.children) {
      const child = item.children.find(
        (candidate) =>
          candidate.type === 'item' &&
          (pathname === candidate.url || pathname.startsWith(`${candidate.url}/`))
      );
      if (child) return { group: item, child };
    }
  }
  return null;
}

export default function Breadcrumbs() {
  const location = useLocation();
  const [crumb, setCrumb] = useState(null);

  const resolve = useCallback(() => {
    const found = findBreadcrumbMenuItem(navigation.items, location.pathname);
    if (!found) {
      setCrumb(null);
      return;
    }

    setCrumb({
      groupTitle: typeof found.group.title === 'string' ? found.group.title : '',
      groupUrl: found.group.children?.find((item) => item.type === 'item')?.url || APP_DEFAULT_PATH,
      title: projectBreadcrumbTitle(location.pathname) || found.child.title || '',
      breadcrumbs: found.child.breadcrumbs !== false
    });
  }, [location.pathname]);

  useEffect(() => {
    resolve();
  }, [resolve]);

  if (!crumb || !crumb.breadcrumbs) return null;

  return (
    <div className="page-header">
      <div className="page-block">
        <Row className="align-items-center">
          <Col md={12} className="page-header-title text-capitalize">
            <h5>{crumb.title}</h5>
          </Col>
          <Col md={12}>
            <Breadcrumb listProps={{ style: { marginBottom: 0 } }}>
              <Breadcrumb.Item linkAs={Link} linkProps={{ to: APP_DEFAULT_PATH }}>
                Home
              </Breadcrumb.Item>
              <Breadcrumb.Item linkAs={Link} linkProps={{ to: crumb.groupUrl }}>
                {crumb.groupTitle}
              </Breadcrumb.Item>
              <Breadcrumb.Item active>{crumb.title}</Breadcrumb.Item>
            </Breadcrumb>
          </Col>
        </Row>
      </div>
    </div>
  );
}
