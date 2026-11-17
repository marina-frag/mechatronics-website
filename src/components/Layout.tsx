import { Link, NavLink } from 'react-router';
import { site } from '../content/site';

export function Header() {
  return (
    <header className="site-header">
      <div className="site-header__inner">
        <Link to="/" className="brand" aria-label="Αρχική">
          <span className="brand__mark" aria-hidden="true" />
          <span className="brand__text">Μηχατρονικά συστήματα</span>
        </Link>
        <nav aria-label="Κύρια πλοήγηση">
          <ul className="nav">
            <li>
              <Link to="/#projects">Projects</Link>
            </li>
            <li>
              <NavLink to="/material">Υλικό μαθήματος</NavLink>
            </li>
          </ul>
        </nav>
      </div>
    </header>
  );
}

export function Footer() {
  return (
    <footer className="site-footer">
      <div className="site-footer__inner">
        <p>
          <strong>{site.course}</strong>
          <br />
          {site.school}, {site.university}
        </p>
        <p className="muted">Τα 3D μοντέλα προέρχονται από τα αρχεία CAD των ομάδων.</p>
      </div>
    </footer>
  );
}
