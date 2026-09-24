// API 10 UI logic
// Owner: Manatka
//
// Client-side pre-checks mirror the backend rules (10 MB, allowed types) so
// the user gets instant feedback; the backend remains the authority.

import { useState } from 'react';

import { uploadFile } from 'services/tasks/fileService';

export const MAX_FILE_SIZE = 10 * 1024 * 1024;
export const ALLOWED_EXTENSIONS = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.csv', '.txt', '.png', '.jpg', '.jpeg'];

function preCheck(file) {
  if (!file) return 'Choose a file first.';

  const ext = file.name.includes('.') ? `.${file.name.split('.').pop().toLowerCase()}` : '';

  if (!ALLOWED_EXTENSIONS.includes(ext)) return 'File type not allowed. Allowed: PDF, DOC/DOCX, XLS/XLSX, CSV, TXT, PNG, JPG/JPEG.';
  if (file.size === 0) return 'File is empty.';
  if (file.size > MAX_FILE_SIZE) return 'File is larger than 10 MB.';

  return null;
}

export function useTaskFiles(taskId) {
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);
  const [uploaded, setUploaded] = useState([]);

  const upload = async (file) => {
    setError(null);

    const problem = preCheck(file);

    if (problem) {
      setError(problem);
      return null;
    }

    setUploading(true);

    try {
      const attachment = await uploadFile(taskId, file);
      setUploaded((list) => [attachment, ...list]);
      return attachment;
    } catch (err) {
      if (err.status === 400) setError(err.fields?.file?.[0] ?? err.message);
      else if (err.status === 404) setError('Task not found, or you are not a member of its project.');
      else if (err.status === 401) setError('Your session has expired. Please log in again.');
      else setError('Upload failed. Please try again.');
      return null;
    } finally {
      setUploading(false);
    }
  };

  return { upload, uploading, error, uploaded };
}