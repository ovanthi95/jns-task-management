import { useState } from 'react';
import { mutate } from 'swr';

// project-imports
import { createUser } from 'services/users/userService';

// ==============================|| USE CREATE USER (API 03) ||============================== //
//
// Owns the submit lifecycle: submitting flag, field errors from the server,
// a general error, and the created user on success. After a success the
// 'users' list cache is invalidated so UserList refetches.

export default function useCreateUser() {
  const [isSubmitting, setSubmitting] = useState(false);
  const [serverErrors, setServerErrors] = useState({});
  const [generalError, setGeneralError] = useState(null);
  const [created, setCreated] = useState(null);

  const submit = async (values) => {
    setSubmitting(true);
    setServerErrors({});
    setGeneralError(null);

    try {
      const user = await createUser(values);
      setCreated(user);
      mutate('users');
      return user;
    } catch (err) {
      if (err.status === 400 && err.fields) {
        setServerErrors(err.fields);
      } else {
        setGeneralError('Could not create the user. Please try again.');
      }
      return null;
    } finally {
      setSubmitting(false);
    }
  };

  return { submit, isSubmitting, serverErrors, generalError, created };
}