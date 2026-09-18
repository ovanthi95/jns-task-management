import PropTypes from 'prop-types';
import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';

// react-bootstrap
import Alert from 'react-bootstrap/Alert';
import Button from 'react-bootstrap/Button';
import Col from 'react-bootstrap/Col';
import Form from 'react-bootstrap/Form';
import Image from 'react-bootstrap/Image';
import InputGroup from 'react-bootstrap/InputGroup';
import Row from 'react-bootstrap/Row';
import Spinner from 'react-bootstrap/Spinner';
import Stack from 'react-bootstrap/Stack';

// third-party
import { useForm } from 'react-hook-form';

// project-imports
import MainCard from 'components/MainCard';
import { useAuth } from 'contexts/AuthContext';
import { confirmPasswordSchema, emailSchema, firstNameSchema, lastNameSchema, passwordSchema } from 'utils/validationSchema';

// assets
import DarkLogo from 'assets/images/logo-dark.svg';

// ==============================|| AUTH REGISTER FORM ||============================== //

// POST /api/v1/auth/register (service 01). This is self-service *tenant* sign-up,
// not "add a user": it creates an organisations row and its first users row, as
// Admin, in one transaction. That is why the form asks for an organisation name
// that the template's stub did not collect — without it the request is a 400.
//
// Adding a colleague to an existing organisation is a different endpoint
// (POST /users, Admin-only), because only /auth/register may write
// organisation_id; every other endpoint derives it from the JWT.

// ChoiceField(choices=["SME", "NFP", "OTHER"], default="OTHER") on the server.
// Kept as a literal list rather than a lookup fetch because it is a serializer
// choice, not a database table, so there is no endpoint that could return it.
const ORGANISATION_TYPES = [
  { value: 'SME', label: 'Small or medium enterprise' },
  { value: 'NFP', label: 'Not-for-profit' },
  { value: 'OTHER', label: 'Other' }
];

const organisationNameSchema = {
  required: 'Organisation name is required',
  maxLength: { value: 150, message: 'Organisation name must be 150 characters or fewer' }
};

export default function AuthRegisterForm({ className, link }) {
  const [showPassword, setShowPassword] = useState(false);
  const [formError, setFormError] = useState('');

  const { register: signUp } = useAuth();
  const navigate = useNavigate();

  // `register` is taken by the auth context above, so react-hook-form's own
  // register is aliased. Two different registrations, one obvious name.
  const {
    register: field,
    handleSubmit,
    formState: { errors, isSubmitting },
    setError,
    clearErrors
  } = useForm({ defaultValues: { organisationType: 'OTHER' } });

  const togglePasswordVisibility = () => {
    setShowPassword((prevState) => !prevState);
  };

  const onSubmit = async (data) => {
    setFormError('');

    if (data.password !== data.confirmPassword) {
      setError('confirmPassword', { type: 'manual', message: 'Both Password must be match!' });
      return;
    }

    clearErrors('confirmPassword');

    try {
      await signUp({
        organisationName: data.organisationName,
        organisationType: data.organisationType,
        firstName: data.firstName,
        lastName: data.lastName,
        email: data.email,
        password: data.password
      });

      // register returns the same {user, tokens} payload as login, and
      // AuthContext has already stored both, so the new Admin lands signed in.
      navigate('/dashboard/default', { replace: true });
    } catch (error) {
      // Django's AUTH_PASSWORD_VALIDATORS reject common and numeric-only
      // passwords, and a duplicate address inside the same organisation comes
      // back on `email`. Both arrive as 400 field errors, so put them on the
      // field they belong to rather than in a banner nobody connects to a box.
      const fieldErrors = error?.fieldErrors ?? {};
      const known = {
        organisation_name: 'organisationName',
        organisation_type: 'organisationType',
        first_name: 'firstName',
        last_name: 'lastName',
        email: 'email',
        password: 'password'
      };

      let placed = false;
      Object.entries(fieldErrors).forEach(([apiField, message]) => {
        const target = known[apiField];
        if (target) {
          setError(target, { type: 'server', message });
          placed = true;
        }
      });

      if (!placed) {
        setFormError(error?.message || 'Could not create the account.');
      }
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
        <h4 className={`text-center f-w-500 mt-4 mb-3 ${className}`}>Sign up</h4>
        {formError && (
          <Alert variant="danger" className="py-2">
            {formError}
          </Alert>
        )}
        <Row>
          <Col sm={6}>
            <Form.Group className="mb-3" controlId="formFirstName">
              <Form.Control
                type="text"
                placeholder="First Name"
                {...field('firstName', firstNameSchema)}
                isInvalid={!!errors.firstName}
                className={className && 'bg-transparent border-white text-white border-opacity-25 '}
              />
              <Form.Control.Feedback type="invalid">{errors.firstName?.message}</Form.Control.Feedback>
            </Form.Group>
          </Col>
          <Col sm={6}>
            <Form.Group className="mb-3" controlId="formLastName">
              <Form.Control
                type="text"
                placeholder="Last Name"
                {...field('lastName', lastNameSchema)}
                isInvalid={!!errors.lastName}
                className={className && 'bg-transparent border-white text-white border-opacity-25 '}
              />
              <Form.Control.Feedback type="invalid">{errors.lastName?.message}</Form.Control.Feedback>
            </Form.Group>
          </Col>
        </Row>
        <Row>
          <Col sm={7}>
            <Form.Group className="mb-3" controlId="formOrganisationName">
              <Form.Control
                type="text"
                placeholder="Organisation Name"
                {...field('organisationName', organisationNameSchema)}
                isInvalid={!!errors.organisationName}
                className={className && 'bg-transparent border-white text-white border-opacity-25 '}
              />
              <Form.Control.Feedback type="invalid">{errors.organisationName?.message}</Form.Control.Feedback>
            </Form.Group>
          </Col>
          <Col sm={5}>
            <Form.Group className="mb-3" controlId="formOrganisationType">
              <Form.Select
                {...field('organisationType')}
                isInvalid={!!errors.organisationType}
                className={className && 'bg-transparent border-white text-white border-opacity-25 '}
              >
                {ORGANISATION_TYPES.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </Form.Select>
              <Form.Control.Feedback type="invalid">{errors.organisationType?.message}</Form.Control.Feedback>
            </Form.Group>
          </Col>
        </Row>
        <Form.Group className="mb-3" controlId="formEmail">
          <Form.Control
            type="email"
            placeholder="Email Address"
            {...field('email', emailSchema)}
            isInvalid={!!errors.email}
            className={className && 'bg-transparent border-white text-white border-opacity-25 '}
          />
          <Form.Control.Feedback type="invalid">{errors.email?.message}</Form.Control.Feedback>
        </Form.Group>
        <Form.Group className="mb-3" controlId="formPassword">
          <InputGroup hasValidation>
            <Form.Control
              type={showPassword ? 'text' : 'password'}
              placeholder="Password"
              {...field('password', passwordSchema)}
              isInvalid={!!errors.password}
              className={className && 'bg-transparent border-white text-white border-opacity-25 '}
            />
            <Button onClick={togglePasswordVisibility} type="button">
              {showPassword ? <i className="ti ti-eye" /> : <i className="ti ti-eye-off" />}
            </Button>
            <Form.Control.Feedback type="invalid">{errors.password?.message}</Form.Control.Feedback>
          </InputGroup>
        </Form.Group>
        <Form.Group className="mb-3" controlId="formConfirmPassword">
          <Form.Control
            type="password"
            placeholder="Confirm Password"
            {...field('confirmPassword', confirmPasswordSchema)}
            isInvalid={!!errors.confirmPassword}
            className={className && 'bg-transparent border-white text-white border-opacity-25 '}
          />
          <Form.Control.Feedback type="invalid">{errors.confirmPassword?.message}</Form.Control.Feedback>
        </Form.Group>
        <Stack direction="horizontal" className="mt-1 justify-content-between">
          <Form.Group controlId="customCheckc1">
            <Form.Check
              type="checkbox"
              label="I agree to all the Terms & Condition"
              defaultChecked
              className={`input-primary ${className ? className : 'text-muted'} `}
            />
          </Form.Group>
        </Stack>
        <div className="text-center mt-4">
          <Button type="submit" className="shadow px-sm-4" disabled={isSubmitting}>
            {isSubmitting && <Spinner animation="border" size="sm" className="me-2" role="status" />}
            {isSubmitting ? 'Creating account…' : 'Sign up'}
          </Button>
        </div>
        <Stack direction="horizontal" className="justify-content-between align-items-end mt-4">
          <h6 className={`f-w-500 mb-0 ${className}`}>Already have an Account?</h6>
          <Link to={link} className="link-primary">
            Login
          </Link>
        </Stack>
      </Form>
    </MainCard>
  );
}

AuthRegisterForm.propTypes = { className: PropTypes.string, link: PropTypes.string };
