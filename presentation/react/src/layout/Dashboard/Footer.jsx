import Col from 'react-bootstrap/Col';
import Row from 'react-bootstrap/Row';

export default function Footer() {
  const year = new Date().getFullYear();

  return (
    <footer className="pc-footer">
      <div className="footer-wrapper container-fluid">
        <Row className="align-items-center justify-content-center text-center">
          <Col xs="auto" className="my-1">
            <p className="m-0 text-muted small">
              © {year} JNS Business Solutions
            </p>
          </Col>
        </Row>
      </div>
    </footer>
  );
}
