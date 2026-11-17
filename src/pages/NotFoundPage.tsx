import { Link } from 'react-router';

export function NotFoundPage() {
  return (
    <section className="section section--first">
      <div className="container">
        <h1>Η σελίδα δεν βρέθηκε</h1>
        <p className="lead">Ίσως ο σύνδεσμος να έχει αλλάξει.</p>
        <Link className="btn btn--primary" to="/">
          Αρχική
        </Link>
      </div>
    </section>
  );
}
