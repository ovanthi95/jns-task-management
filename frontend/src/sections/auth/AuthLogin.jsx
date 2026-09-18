import PropTypes from 'prop-types';
import { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';

// react-bootstrap
import Alert from 'react-bootstrap/Alert';
import Button from 'react-bootstrap/Button';
import Form from 'react-bootstrap/Form';
import Image from 'react-bootstrap/Image';
import InputGroup from 'react-bootstrap/InputGroup';
import Spinner from 'react-bootstrap/Spinner';
import Stack from 'react-bootstrap/Stack';

// third-party
import { useForm } from 'react-hook-form';

// project-imports
import MainCard from 'components/MainCard';
import { useAuth } from 'contexts/AuthContext';
import { emailSchema, passwordSchema } from 'utils/validationSchema';

// assets
import DarkLogo from 'assets/images/logo-dark.svg';

// ==============================|| AUTH LOGIN FORM ||============================== //

// POST /api/v1/auth/login (service 02). Returns {user, tokens:{access, refresh}};
// AuthContext stores the pair and every later request carries the access token
// as `Authorization: Bearer <token>`.

export default function AuthLoginForm({ className, link }) {
  const [showPassword, setShowPassword] = useState(false);
  const [formError, setFormError] = useState('');
  // Email is UNIQUE (organisation_id, email), not globally, so the same address
  // can legitimately exist in two tenants. The API says so rather than guessing;
  // this extra field appears only when it does.
  const [needsOrganisation, setNeedsOrganisation] = useState(false);

  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting }
  } = useForm();

  const togglePasswordVisibility = () => {
    setShowPassword((prevState) => !prevState);
  };

  const onSubmit = async (data) => {
    setFormError('');

    try {
      await login({
        email: data.email,
        password: data.password,
        organisationId: data.organisationId
      });

      // Back to wherever RequireAuth interrupted them, or the dashboard.
      navigate(location.state?.from?.pathname || '/dashboard/default', { replace: true });
    } catch (error) {
      // The API returns the same message for an unknown email and a wrong
      // password on purpose, so this endpoint cannot be used to test whether an
      // address is registered. Do not try to be more helpful than that here.
      setFormError(error?.message || 'Could not sign in.');
      setNeedsOrganisation(Boolean(error?.message?.includes('more than one organisation')));
    }
  };

  return (
    <MainCard className="mb-0">
      <div className="text-center">
        <a>
          <Image src={DarkLogo} alt="img" />
        </a>
      </div>
      <Form onSubmit={handleSubmit(onSubmit)}>
        <h4 className={`text-center f-w-500 mt-4 mb-3 ${className}`}>Login</h4>
        {formError && (
          <Alert variant="danger" className="py-2">
            {formError}
          </Alert>
        )}
        <Form.Group className="mb-3" controlId="formEmail">
          <Form.Control
            type="email"
            placeholder="Email Address"
            {...register('email', emailSchema)}
            isInvalid={!!errors.email}
            className={className && 'bg-transparent border-white text-white border-opacity-25 '}
          />
          <Form.Control.Feedback type="invalid">{errors.email?.message}</Form.Control.Feedback>
        </Form.Group>
        <Form.Group className="mb-3" controlId="formPassword">
          <InputGroup>
            <Form.Control
              type={showPassword ? 'text' : 'password'}
              placeholder="Password"
              {...register('password', passwordSchema)}
              isInvalid={!!errors.password}
              className={className && 'bg-transparent border-white text-white border-opacity-25 '}
            />
            <Button onClick={togglePasswordVisibility}>
              {showPassword ? <i className="ti ti-eye" /> : <i className="ti ti-eye-off" />}
            </Button>
            <Form.Control.Feedback type="invalid">{errors.password?.message}</Form.Control.Feedback>
          </InputGroup>
        </Form.Group>
        {needsOrganisation && (
          <Form.Group className="mb-3" controlId="formOrganisation">
            <Form.Control
              type="number"
              placeholder="Organisation ID"
              {...register('organisationId')}
              className={className && 'bg-transparent border-white text-white border-opacity-25 '}
            />
            <Form.Text className="text-muted">This email is registered with more than one organisation.</Form.Text>
          </Form.Group>
        )}

        <Stack direction="horizontal" className="mt-1 justify-content-between align-items-center">
          <Form.Group controlId="customCheckc1">
            <Form.Check
              type="checkbox"
              label="Remember me?"
              defaultChecked
              className={`input-primary ${className ? className : 'text-muted'} `}
            />
          </Form.Group>
          <Link to="#!" className={`text-secondary f-w-400 mb-0  ${className}`}>
            Forgot Password?
          </Link>
        </Stack>
        <div className="text-center mt-4">
          <Button type="submit" className="shadow px-sm-4" disabled={isSubmitting}>
            {isSubmitting && <Spinner animation="border" size="sm" className="me-2" role="status" />}
            {isSubmitting ? 'Signing in…' : 'Login'}
          </Button>
        </div>
        <Stack direction="horizontal" className="justify-content-between align-items-end mt-4">
          <h6 className={`f-w-500 mb-0 ${className}`}>Don&apos;t have an Account?</h6>
          <Link to={link} className="link-primary">
            Create Account
          </Link>
        </Stack>
      </Form>
    </MainCard>
  );
}

AuthLoginForm.propTypes = { className: PropTypes.string, link: PropTypes.string };
