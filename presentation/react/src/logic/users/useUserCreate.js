// API 03 UI logic
// Owner: Manatka
//
// Submit lifecycle only: submitting flag, per-field server errors, general
// error. Navigation after success is the page's decision.

import { useState } from 'react';

import { createUser } from 'services/users/userCreateService';

export function useUserCreate() {
  const [submitting, setSubmitting] = useState(false);
  const [serverErrors, setServerErrors] = useState({});
  const [generalError, setGeneralError] = useState(null);

  const submit = async (values) => {
    setSubmitting(true);
    setServerErrors({});
    setGeneralError(null);

    try {
      return await createUser(values);
    } catch (err) {
      if (err.status === 400) {
        setServerErrors(err.fields || {});
      } else if (err.status === 403) {
        setGeneralError('Your role is not permitted to create users.');
      } else {
        setGeneralError('Could not create the user. Please try again.');
      }
      return null;
    } finally {
      setSubmitting(false);
    }
  };

  return { submit, submitting, serverErrors, generalError };
}