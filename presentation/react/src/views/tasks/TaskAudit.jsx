// API 11 UI - Task audit
// Owner: Ovanthi

import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';

import Alert from 'react-bootstrap/Alert';
import Spinner from 'react-bootstrap/Spinner';
import Table from 'react-bootstrap/Table';

import MainCard from 'components/MainCard';
import { getTaskAudit } from 'services/audit/taskAuditService';

function valueText(value) {
  if (value === null || value === undefined) return '—';
  if (typeof value === 'object') return JSON.stringify(value);
  return String(value);
}

export default function TaskAudit() {
  const { projectId, taskId } = useParams();
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;

    getTaskAudit(taskId)
      .then((data) => {
        if (active) setRows(data);
      })
      .catch((requestError) => {
        if (active) setError(requestError.message);
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, [taskId]);

  return (
    <MainCard
      title={`Task #${taskId} — Audit history`}
      subheader={
        projectId ? (
          <Link to={`/projects/${projectId}/tasks`}>
            Back to tasks
          </Link>
        ) : null
      }
    >
      {error && <Alert variant="danger">{error}</Alert>}

      {loading ? (
        <div className="py-4 text-center">
          <Spinner animation="border" size="sm" /> Loading audit history...
        </div>
      ) : !error && rows.length === 0 ? (
        <p className="text-muted mb-0">
          No recorded changes for this task.
        </p>
      ) : !error ? (
        <Table responsive hover align="middle">
          <thead>
            <tr>
              <th>Changed at</th>
              <th>Changed by</th>
              <th>Field</th>
              <th>Old value</th>
              <th>New value</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.history_id}>
                <td>{new Date(row.changed_at).toLocaleString()}</td>
                <td>{row.first_name} {row.last_name}</td>
                <td>{row.field_name}</td>
                <td>{valueText(row.old_value)}</td>
                <td>{valueText(row.new_value)}</td>
              </tr>
            ))}
          </tbody>
        </Table>
      ) : null}
    </MainCard>
  );
}
