// react-bootstrap
import Alert from 'react-bootstrap/Alert';
import Badge from 'react-bootstrap/Badge';
import Spinner from 'react-bootstrap/Spinner';
import Table from 'react-bootstrap/Table';

// project-imports
import MainCard from 'components/MainCard';
import useUsers from 'logic/users/useUsers';

// ==============================|| USERS - LIST (API 02) ||============================== //
//
// Card copied from sections/tables/bootstrap-table/basic-table/BasicTable.jsx
// (the reference Ovanthi pointed to), with the three states the Trello card
// asks for: loading, empty list, error.

export default function UserList() {
  const { users, isLoading, error } = useUsers();

  let body;

  if (isLoading) {
    body = (
      <div className="text-center py-4">
        <Spinner animation="border" role="status" size="sm" className="me-2" />
        Loading users...
      </div>
    );
  } else if (error) {
    body = (
      <Alert variant="danger" className="mb-0">
        Could not load users. Please try again.
      </Alert>
    );
  } else if (users.length === 0) {
    body = <p className="text-muted mb-0 py-3 text-center">No users found in your organisation.</p>;
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
    <MainCard className="table-card" title="Users" subheader={<p className="mb-0">All users in your organisation</p>}>
      {body}
    </MainCard>
  );
}