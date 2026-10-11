import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';

import Button from 'react-bootstrap/Button';
import Dropdown from 'react-bootstrap/Dropdown';
import Image from 'react-bootstrap/Image';
import Nav from 'react-bootstrap/Nav';
import Stack from 'react-bootstrap/Stack';

import { handlerDrawerOpen, useGetMenuMaster } from 'api/menu';
import { logout } from 'services/auth/logoutService';
import { getSessionUser } from 'services/auth/sessionService';
import Img2 from 'assets/images/user/avatar-2.png';

export default function Header() {
  const navigate = useNavigate();
  const { menuMaster } = useGetMenuMaster();
  const drawerOpen = menuMaster?.isDashboardDrawerOpened;
  const [user, setUser] = useState(null);

  useEffect(() => {
    let active = true;

    getSessionUser()
      .then((sessionUser) => {
        if (active) setUser(sessionUser);
      })
      .catch(() => {
        if (active) setUser(null);
      });

    return () => {
      active = false;
    };
  }, []);

  const handleLogout = async () => {
    try {
      await logout();
      navigate('/login', { replace: true });
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  const displayName = user
    ? [user.first_name, user.last_name].filter(Boolean).join(' ')
    : 'Worklink User';

  return (
    <header className="pc-header">
      <div className="header-wrapper">
        <div className="me-auto pc-mob-drp">
          <Nav className="list-unstyled">
            <Nav.Item className="pc-h-item pc-sidebar-collapse">
              <Nav.Link
                as={Link}
                to="#"
                className="pc-head-link ms-0"
                id="sidebar-hide"
                onClick={() => handlerDrawerOpen(!drawerOpen)}
              >
                <i className="ph ph-list" />
              </Nav.Link>
            </Nav.Item>

            <Nav.Item className="pc-h-item pc-sidebar-popup">
              <Nav.Link
                as={Link}
                to="#"
                className="pc-head-link ms-0"
                id="mobile-collapse"
                onClick={() => handlerDrawerOpen(!drawerOpen)}
              >
                <i className="ph ph-list" />
              </Nav.Link>
            </Nav.Item>
          </Nav>
        </div>

        <div className="ms-auto">
          <Nav className="list-unstyled">
            <Dropdown className="pc-h-item" align="end">
              <Dropdown.Toggle
                className="pc-head-link arrow-none me-0"
                variant="link"
                id="user-profile-dropdown"
                aria-haspopup="true"
                aria-expanded="false"
              >
                <i className="ph ph-user-circle" />
              </Dropdown.Toggle>

              <Dropdown.Menu className="dropdown-user-profile pc-h-dropdown p-0 overflow-hidden">
                <Dropdown.Header className="bg-primary">
                  <Stack direction="horizontal" gap={3} className="my-2">
                    <div className="flex-shrink-0">
                      <Image
                        src={Img2}
                        alt="user-avatar"
                        className="user-avatar wid-35"
                        roundedCircle
                      />
                    </div>
                    <Stack gap={1}>
                      <h6 className="text-white mb-0">{displayName}</h6>
                      <span className="text-white text-opacity-75">
                        {user?.email || ''}
                      </span>
                    </Stack>
                  </Stack>
                </Dropdown.Header>

                <div className="dropdown-body">
                  <div className="profile-notification-scroll position-relative">
                    <Dropdown.Item as={Link} to="/change-password" className="justify-content-start">
                      <i className="ph ph-lock-key me-2" />
                      Change password
                    </Dropdown.Item>

                    <div className="d-grid my-2">
                      <Button onClick={handleLogout}>
                        <i className="ph ph-sign-out align-middle me-2" />
                        Logout
                      </Button>
                    </div>
                  </div>
                </div>
              </Dropdown.Menu>
            </Dropdown>
          </Nav>
        </div>
      </div>
    </header>
  );
}
