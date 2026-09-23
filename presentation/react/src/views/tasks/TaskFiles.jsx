// API 10 UI - Task files
// Owner: Manatka

import { useRef, useState } from 'react';
import { useParams } from 'react-router-dom';

// react-bootstrap
import Alert from 'react-bootstrap/Alert';
import Button from 'react-bootstrap/Button';
import Form from 'react-bootstrap/Form';
import Table from 'react-bootstrap/Table';

// project-imports
import MainCard from 'components/MainCard';
import { ALLOWED_EXTENSIONS, useTaskFiles } from 'logic/tasks/useTaskFiles';

// ==============================|| TASKS - FILES (API 10) ||============================== //
//
// Own page for uploading an attachment to one task (route /tasks/:taskId/files).
// There is no list-files API on the agreed contract, so the table below shows
// the attachments uploaded in this session only.

const formatSize = (bytes) => (bytes >= 1024 * 1024 ? `${(bytes / 1024 / 1024).toFixed(1)} MB` : `${Math.ceil(bytes / 1024)} KB`);

export default function TaskFiles() {
  const { taskId } = useParams();
  const { upload, uploading, error, uploaded } = useTaskFiles(taskId);
  const [file, setFile] = useState(null);
  const inputRef = useRef(null);

  const onSubmit = async (event) => {
    event.preventDefault();
    const result = await upload(file);
    if (result) {
      setFile(null);
      if (inputRef.current) inputRef.current.value = '';
    }
  };

  return (
    <MainCard title={`Task #${taskId} files`} subheader={<p className="mb-0">Upload an attachment to this task</p>}>
      <Form onSubmit={onSubmit} className="mb-4">
        <Form.Group controlId="taskFile" className="mb-2">
          <Form.Label>File</Form.Label>
          <Form.Control
            ref={inputRef}
            type="file"
            accept={ALLOWED_EXTENSIONS.join(',')}
            onChange={(event) => setFile(event.target.files?.[0] ?? null)}
            isInvalid={!!error}
            disabled={uploading}
          />
          <Form.Control.Feedback type="invalid">{error}</Form.Control.Feedback>
          <Form.Text muted>Max 10 MB. PDF, DOC/DOCX, XLS/XLSX, CSV, TXT, PNG, JPG/JPEG.</Form.Text>
        </Form.Group>
        <Button type="submit" disabled={uploading || !file}>
          {uploading ? 'Uploading...' : 'Upload'}
        </Button>
      </Form>

      {uploaded.length === 0 ? (
        <p className="text-muted mb-0">No files uploaded in this session yet.</p>
      ) : (
        <>
          <Alert variant="success" className="py-2">File uploaded.</Alert>
          <Table responsive hover className="mb-0">
            <thead>
              <tr>
                <th>#</th>
                <th>File</th>
                <th>Type</th>
                <th>Size</th>
                <th>Uploaded at</th>
              </tr>
            </thead>
            <tbody>
              {uploaded.map((a) => (
                <tr key={a.attachment_id}>
                  <td>{a.attachment_id}</td>
                  <td>{a.file_name}</td>
                  <td>{a.file_type}</td>
                  <td>{formatSize(a.file_size)}</td>
                  <td>{a.uploaded_at}</td>
                </tr>
              ))}
            </tbody>
          </Table>
        </>
      )}
    </MainCard>
  );
}