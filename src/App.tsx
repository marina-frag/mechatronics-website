import { Suspense, useEffect } from 'react';
import { Outlet, ScrollRestoration, useLocation } from 'react-router';
import { Footer, Header } from './components/Layout';

export function App() {
  const { hash, pathname } = useLocation();

  // Σύνδεσμοι τύπου /#projects: κύλιση στο σωστό σημείο μετά την πλοήγηση.
  useEffect(() => {
    if (!hash) return;
    const id = decodeURIComponent(hash.slice(1));
    requestAnimationFrame(() => document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' }));
  }, [hash, pathname]);

  return (
    <>
      <a className="skip-link" href="#main">
        Μετάβαση στο περιεχόμενο
      </a>
      <Header />
      <main id="main">
        <Suspense fallback={<p className="page-loading">Φόρτωση…</p>}>
          <Outlet />
        </Suspense>
      </main>
      <Footer />
      <ScrollRestoration />
    </>
  );
}
