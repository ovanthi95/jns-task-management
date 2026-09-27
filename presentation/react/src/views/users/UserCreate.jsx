// API 03 UI - Create user
// Owner: Manatka

import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

// react-bootstrap
import Alert from 'react-bootstrap/Alert';
import Button from 'react-bootstrap/Button';
import Col from 'react-bootstrap/Col';
import Form from 'react-bootstrap/Form';
import Row from 'react-bootstrap/Row';

// third-party
import { useForm } from 'react-hook-form';

// project-imports
import MainCard from 'components/MainCard';
import { useUserCreate } from 'logic/users/useUserCreate';
import { getRoles } from 'services/users/roleService';
import { emailSchema, firstNameSchema, lastNameSchema, passwordSchema } from 'utils/validationSchema';

// ==============================|| USERS - CREATE (API 03) ||============================== //
//
// Same form pattern as views/auth/login: react-hook-form + shared validation
// rules. Client-side rules catch the obvious cases; server field errors
// (duplicate email, unknown role) show on the same inputs.

export default function UserCreate() {
  const navigate = useNavigate();
  const { submit, submitting, serverErrors, generalError } = useUserCreate();
  const [roles, setRoles] = useState([]);
  const [roleError, setRoleError] = useState('');

  useEffect(() => {
    getRoles()
      .then((data) => setRoles((data.roles || []).filter((role) => role.is_active)))
      .catch((error) => setRoleError(error.message));
  }, []);

  const {
    register,
    handleSubmit,
    formState: { errors }
  } = useForm();

  const fieldError = (name) => errors[name]?.message ?? serverErrors[name]?.[0];

  const onSubmit = async (values) => {
    const user = await submit({ ...values, role_id: Number(values.role_id) });
    if (user) navigate('/users');
  };

  return (
    <MainCard title="Create user" subheader={<p className="mb-0">The new user is added to your organisation</p>}>
      {generalError && <Alert variant="danger">{generalError}</Alert>}
      {roleError && <Alert variant="danger">{roleError}</Alert>}

      <Form noValidate onSubmit={handleSubmit(onSubmit)}>
        <Row>
          <Form.Group as={Col} md="6" className="mb-3" controlId="firstName">
            <Form.Label>First name</Form.Label>
            <Form.Control type="text" {...register('first_name', firstNameSchema)} isInvalid={!!fieldError('first_name')} />
            <Form.Control.Feedback type="invalid">{fieldError('first_name')}</Form.Control.Feedback>
          </Form.Group>
          <Form.Group as={Col} md="6" className="mb-3" controlId="lastName">
            <Form.Label>Last name</Form.Label>
            <Form.Control type="text" {...register('last_name', lastNameSchema)} isInvalid={!!fieldError('last_name')} />
            <Form.Control.Feedback type="invalid">{fieldError('last_name')}</Form.Control.Feedback>
          </Form.Group>
        </Row>

        <Row>
          <Form.Group as={Col} md="6" className="mb-3" controlId="email">
            <Form.Label>Email</Form.Label>
            <Form.Control type="email" {...register('email', emailSchema)} isInvalid={!!fieldError('email')} />
            <Form.Control.Feedback type="invalid">{fieldError('email')}</Form.Control.Feedback>
          </Form.Group>
          <Form.Group as={Col} md="6" className="mb-3" controlId="password">
            <Form.Label>Password</Form.Label>
            <Form.Control type="password" {...register('password', passwordSchema)} isInvalid={!!fieldError('password')} />
            <Form.Control.Feedback type="invalid">{fieldError('password')}</Form.Control.Feedback>
          </Form.Group>
        </Row>

        <Row>
          <Form.Group as={Col} md="6" className="mb-3" controlId="roleId">
            <Form.Label>Role</Form.Label>
            <Form.Select {...register('role_id', { required: 'Role is required' })} isInvalid={!!fieldError('role_id')}>
              <option value="">Select a role</option>
              {roles.map((role) => (
                <option key={role.role_id} value={role.role_id}>
                  {role.role_name}
                </option>
              ))}
            </Form.Select>
            <Form.Control.Feedback type="invalid">{fieldError('role_id')}</Form.Control.Feedback>
          </Form.Group>
          <Form.Group as={Col} md="6" className="mb-3" controlId="availability">
            <Form.Label>Availability (optional)</Form.Label>
            <Form.Control type="text" placeholder="e.g. Full-time, Part-time" {...register('availability')} />
          </Form.Group>
        </Row>

        <div className="d-flex gap-2">
          <Button type="submit" disabled={submitting}>
            {submitting ? 'Creating...' : 'Create user'}
          </Button>
          <Button variant="light" onClick={() => navigate('/users')} disabled={submitting}>
            Cancel
          </Button>
        </div>
      </Form>
    </MainCard>
  );
}