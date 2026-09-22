// #login implemented by Ovanthi- 25298714

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { login } from 'services/auth/loginService';

export function useLogin() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  
  const navigate = useNavigate();
  const togglePassword = () => {
    setShowPassword((current) => !current);
  };

  const handleSubmit = async (event) => {
    event.preventDefault();

    setError('');
    setSuccess('');
    setLoading(true);

    try {
      const data = await login(email, password);

      setSuccess(data.message || 'Login successful.');
      navigate('/dashboard');
    } catch (error) {
      setError(error.message || 'Unable to sign in. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return {
    email,
    password,
    showPassword,
    loading,
    error,
    success,
    setEmail,
    setPassword,
    togglePassword,
    handleSubmit
  };
}