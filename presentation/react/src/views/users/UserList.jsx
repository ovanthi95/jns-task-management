// API 02 UI - User list
// Owner: Manatka

// react-bootstrap
import Alert from 'react-bootstrap/Alert';
import Badge from 'react-bootstrap/Badge';
import Button from 'react-bootstrap/Button';
import Spinner from 'react-bootstrap/Spinner';
import Table from 'react-bootstrap/Table';
import { Link } from 'react-router-dom';

// project-imports
import MainCard from 'components/MainCard';
import { useUserList } from 'logic/users/useUserList';

// ==============================|| USERS - LIST (API 02) ||============================== //

export default function UserList() {
  const { users, loading, error } = useUserList();

  let body;

  if (loading) {
    body = (
      <div className="text-center py-4">
        <Spinner animation="border" size="sm" className="me-2" />
        Loading users...
      </div>
    );
  } else if (error) {
    body = (
      <Alert variant={error.status === 403 ? 'warning' : 'danger'} className="mb-0">
        {error.status === 403 ? 'Your role is not permitted to view the user list.' : 'Could not load users. Please try again.'}
      </Alert>
    );
  } else if (users.length === 0) {
    body = <p className="text-muted text-center py-3 mb-0">No users found in your organisation.</p>;
  } else {
    body = (
      <Table responsive hover className="mb-0">
        <thead>
          <tr>
            <th>#</th>
            <th>Name</th>
            <th>Email</th>
            <th>Role</th>
            <th>Availability</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {users.map((u) => (
            <tr key={u.user_id}>
              <td>{u.user_id}</td>
              <td>
                {u.first_name} {u.last_name}
              </td>
              <td>{u.email}</td>
              <td>{u.role_name}</td>
              <td>{u.availability ?? '-'}</td>
              <td>
                <Badge bg={u.status === 'Active' ? 'success' : 'secondary'}>{u.status}</Badge>
              </td>
            </tr>
          ))}
        </tbody>
      </Table>
    );
  }

  return (
    <MainCard
      className="table-card"
      title="Users"
      subheader={<p className="mb-0">All users in your organisation</p>}
      secondary={
        <Button as={Link} to="/users/new" size="sm">
          <i className="ph ph-user-plus me-1" />
          Create user
        </Button>
      }
    >
      {body}
    </MainCard>
  );
}