import { useEffect, useState } from 'react';
import Button from 'react-bootstrap/Button';
import Form from 'react-bootstrap/Form';
import Table from 'react-bootstrap/Table';

import MainCard from 'components/MainCard';
import { getHistory } from 'services/audit/historyService';

const tabs = ['Project', 'Task', 'User'];

function showValue(value) {
  if (value === null || value === undefined || value === '') return '—';
  return typeof value === 'object' ? JSON.stringify(value) : String(value);
}

export default function History() {
  const [entityType, setEntityType] = useState('Project');
  const [search, setSearch] = useState('');
  const [changedBy, setChangedBy] = useState('');
  const [fromDate, setFromDate] = useState('');
  const [toDate, setToDate] = useState('');
  const [data, setData] = useState({
    items: [],
    current_items: [],
    changed_by_options: []
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError('');

    getHistory({
      entityType,
      search,
      changedBy,
      from: fromDate,
      to: toDate
    })
      .then((result) => {
        if (active) setData(result);
      })
      .catch((err) => {
        if (active) setError(err.message);
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, [entityType, search, changedBy, fromDate, toDate]);

  const switchTab = (tab) => {
    setEntityType(tab);
    setSearch('');
    setChangedBy('');
    setFromDate('');
    setToDate('');
  };

  return (
    <MainCard title="History">
      <div className="d-flex flex-wrap gap-2 mb-3">
        {tabs.map((tab) => (
          <Button
            key={tab}
            variant={entityType === tab ? 'primary' : 'outline-primary'}
            onClick={() => switchTab(tab)}
          >
            {tab} History
          </Button>
        ))}
      </div>

      <div className="border rounded p-3 mb-4">
        <div className="row g-2">
          <div className="col-lg-4">
            <Form.Label>Search</Form.Label>
            <Form.Control
              type="search"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder={`Search ${entityType.toLowerCase()} history`}
            />
          </div>

          <div className="col-md-4 col-lg-3">
            <Form.Label>Changed by</Form.Label>
            <Form.Select
              value={changedBy}
              onChange={(event) => setChangedBy(event.target.value)}
            >
              <option value="">All users</option>
              {(data.changed_by_options || []).map((user) => (
                <option key={user.user_id} value={user.user_id}>
                  {user.name}
                </option>
              ))}
            </Form.Select>
          </div>

          <div className="col-md-4 col-lg-2">
            <Form.Label>From</Form.Label>
            <Form.Control
              type="date"
              value={fromDate}
              onChange={(event) => setFromDate(event.target.value)}
            />
          </div>

          <div className="col-md-4 col-lg-2">
            <Form.Label>To</Form.Label>
            <Form.Control
              type="date"
              value={toDate}
              onChange={(event) => setToDate(event.target.value)}
            />
          </div>

          <div className="col-lg-1 d-flex align-items-end">
            <Button
              variant="outline-secondary"
              onClick={() => {
                setSearch('');
                setChangedBy('');
                setFromDate('');
                setToDate('');
              }}
            >
              Clear
            </Button>
          </div>
        </div>
      </div>

      {error && <div className="alert alert-danger">{error}</div>}
      {loading && <p>Loading history...</p>}

      {!loading && !error && (entityType === 'Project' || entityType === 'Task') && (
        <>
          <h5>Current ongoing {entityType.toLowerCase()}s</h5>
          {(data.current_items || []).length === 0 ? (
            <p className="text-muted">No ongoing items match the search.</p>
          ) : (
            <Table responsive hover>
              <thead>
                <tr>
                  <th>{entityType}</th>
                  {entityType === 'Task' && <th>Project</th>}
                  <th>Status</th>
                  <th>{entityType === 'Project' ? 'Progress' : 'Due date'}</th>
                </tr>
              </thead>
              <tbody>
                {data.current_items.map((item) => (
                  <tr key={item.entity_id}>
                    <td>{item.entity_name}</td>
                    {entityType === 'Task' && <td>{item.project_name}</td>}
                    <td>{item.status}</td>
                    <td>
                      {entityType === 'Project'
                        ? `${item.completed_tasks} / ${item.total_tasks} completed`
                        : item.due_date || '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </Table>
          )}
        </>
      )}

      {!loading && !error && (
        <>
          <h5 className="mt-4">{entityType} history records</h5>
          {(data.items || []).length === 0 ? (
            <p className="text-muted">No matching history found.</p>
          ) : (
            <Table responsive hover>
              <thead>
                <tr>
                  <th>Date / time</th>
                  <th>{entityType}</th>
                  <th>Changed by</th>
                  <th>Field</th>
                  <th>From</th>
                  <th>To</th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((item) => (
                  <tr key={item.history_id}>
                    <td>{new Date(item.created_at).toLocaleString()}</td>
                    <td>{item.entity_name || `${entityType} #${item.entity_id}`}</td>
                    <td>{item.changed_by_name}</td>
                    <td>{item.field_name || item.action || 'Created'}</td>
                    <td>{showValue(item.old_value)}</td>
                    <td>{showValue(item.new_value)}</td>
                  </tr>
                ))}
              </tbody>
            </Table>
          )}
        </>
      )}
    </MainCard>
  );
}
