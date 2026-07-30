import { Link, useLocation } from 'react-router-dom';
import './Nav.css';

const LINKS = [
  { to: '/', label: 'Home' },
  { to: '/train', label: 'Train' },
  { to: '/diet', label: 'Diet' },
  { to: '/dashboard', label: 'Dashboard' },
];

export default function Nav() {
  const location = useLocation();

  return (
    <header className="nav">
      <div className="container nav__inner">
        <Link to="/" className="nav__mark">
          RED<span className="nav__mark-accent">/</span>LINE
        </Link>
        <nav className="nav__links">
          {LINKS.map((link) => (
            <Link
              key={link.to}
              to={link.to}
              className={
                location.pathname === link.to
                  ? 'nav__link nav__link--active'
                  : 'nav__link'
              }
            >
              {link.label}
            </Link>
          ))}
        </nav>
      </div>
    </header>
  );
}