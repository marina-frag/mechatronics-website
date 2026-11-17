import { Link, isRouteErrorResponse, useRouteError } from 'react-router';

/** Φιλική σελίδα σφάλματος, αντί για την προεπιλεγμένη του React Router. */
export function ErrorPage() {
  const error = useRouteError();
  const notFound = isRouteErrorResponse(error) && error.status === 404;
  const detail = isRouteErrorResponse(error)
    ? `${error.status} ${error.statusText}`
    : error instanceof Error
      ? error.message
      : String(error);

  return (
    <section className="section section--first">
      <div className="container">
        <h1>{notFound ? 'Η σελίδα δεν βρέθηκε' : 'Κάτι πήγε στραβά'}</h1>
        <p className="lead">
          {notFound
            ? 'Ίσως ο σύνδεσμος να έχει αλλάξει.'
            : 'Η σελίδα δεν φόρτωσε σωστά. Δοκίμασε ανανέωση· αν επιμένει, γύρνα στην αρχική.'}
        </p>
        <div className="actions">
          {!notFound && (
            <button type="button" className="btn btn--primary" onClick={() => window.location.reload()}>
              Ανανέωση
            </button>
          )}
          <Link className="btn" to="/">
            Αρχική
          </Link>
        </div>
        {!notFound && (
          <details className="error-detail">
            <summary>Τεχνικές λεπτομέρειες</summary>
            <pre>{detail}</pre>
          </details>
        )}
      </div>
    </section>
  );
}
