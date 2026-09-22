import { useNavigate } from 'react-router-dom';

// react-bootstrap
import Alert from 'react-bootstrap/Alert';
import Button from 'react-bootstrap/Button';
import Col from 'react-bootstrap/Col';
import Form from 'react-bootstrap/Form';
import Row from 'react-bootstrap/Row';

// third-party
import useSWR from 'swr';
import { useForm } from 'react-hook-form';

// project-imports
import MainCard from 'components/MainCard';
import useCreateUser from 'logic/users/useCreateUser';
import { getRoles } from 'services/users/userService';
import { emailSchema, firstNameSchema, lastNameSchema, passwordSchema } from 'utils/validationSchema';

// ==============================|| USERS - CREATE (API 03) ||============================== //
//
// Same pattern as sections/auth/AuthLogin.jsx: react-hook-form + the shared
// rules in utils/validationSchema. Client-side rules catch the obvious cases;
// server field errors (duplicate email, invalid role) are shown on the same
// inputs so the user sees one consistent style of feedback.

export default function UserCreate() {
  const navigate = useNavigate();
  const { data: roles = [], isLoading: rolesLoading } = useSWR('roles', getRoles);
  const { submit, isSubmitting, serverErrors, generalError } = useCreateUser();

  const {
    register,
    handleSubmit,
    formState: { errors }
  } = useForm();

  // First client-side error, then server error, for each field.
  const fieldError = (name) => errors[name]?.message ?? serverErrors[name]?.[0];

  const onSubmit = async (values) => {
    const user = await submit(values);
    if (user) navigate('/users');
  };

  return (
    <MainCard title="Create user" subheader={<p className="mb-0">The new user is added to your organisation</p>}>
      {generalError && <Alert variant="danger">{generalError}</Alert>}

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
            <Form.Select
              {...register('role_id', { required: 'Role is required' })}
              isInvalid={!!fieldError('role_id')}
              disabled={rolesLoading}
            >
              <option value="">{rolesLoading ? 'Loading roles...' : 'Select a role'}</option>
              {roles.map((r) => (
                <option key={r.role_id} value={r.role_id}>
                  {r.role_name}
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
          <Button type="submit" disabled={isSubmitting}>
            {isSubmitting ? 'Creating...' : 'Create user'}
          </Button>
          <Button variant="light" onClick={() => navigate('/users')} disabled={isSubmitting}>
            Cancel
          </Button>
        </div>
      </Form>
    </MainCard>
  );
}