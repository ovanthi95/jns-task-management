import MainCard from 'components/MainCard';

export default function DefaultPage() {
  return (
    <MainCard>
      <div className="py-4">
        <h3 className="mb-2">Welcome to Worklink</h3>
        <p className="text-muted mb-0">
          Manage projects, tasks, users and team workload from one place.
        </p>
      </div>
    </MainCard>
  );
}
