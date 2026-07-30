import { Link } from 'react-router-dom';
import SkeletonHero from '../components/SkeletonHero';
import '../components/SkeletonHero.css';
import './Home.css';

const MODULES = [
  {
    eyebrow: 'Vision',
    title: 'Real-time form tracking',
    body:
      'Pose detection measures the actual angle at your elbow, knee, or hip every frame, and counts a rep only when the movement completes - not a guess, a measurement.',
    to: '/train',
    cta: 'Open the trainer',
  },
  {
    eyebrow: 'Nutrition',
    title: 'A diet plan for your actual situation',
    body:
      'Set your budget and cooking access - hostel mess, no kitchen, tight budget - and the plan changes accordingly. Ask the coach anything, it accounts for the same constraints.',
    to: '/diet',
    cta: 'Build a plan',
  },
  {
    eyebrow: 'Consistency',
    title: 'A record of what you actually did',
    body:
      'Every session is logged. Your streak, your weekly consistency, and whether you are trending off track - based on real history, not a guess on day one.',
    to: '/dashboard',
    cta: 'View dashboard',
  },
];

export default function Home() {
  return (
    <>
      <section className="hero">
        <div className="container hero__grid">
          <div className="hero__copy">
            <p className="eyebrow">Redline Training Systems</p>
            <h1 className="hero__title">
              Measure the
              <br />
              movement.
              <br />
              <span className="hero__title-accent">Not the vibe.</span>
            </h1>
            <p className="hero__sub">
              Computer vision tracks joint angles in real time to count reps
              and correct form, a nutrition engine that works whether you
              have a kitchen or a mess hall, and a habit tracker built on
              your real session history.
            </p>
            <div className="hero__actions">
              <Link to="/train" className="btn btn-primary">
                Start training
              </Link>
              <Link to="/diet" className="btn btn-ghost">
                Plan a diet
              </Link>
            </div>
          </div>
          <div className="hero__visual">
            <SkeletonHero />
          </div>
        </div>
      </section>

      <section className="modules">
        <div className="container">
          <div className="modules__grid">
            {MODULES.map((mod) => (
              <div className="module-card" key={mod.title}>
                <p className="eyebrow">{mod.eyebrow}</p>
                <h3 className="module-card__title">{mod.title}</h3>
                <p className="module-card__body">{mod.body}</p>
                <Link to={mod.to} className="module-card__link">
                  {mod.cta} &#8594;
                </Link>
              </div>
            ))}
          </div>
        </div>
      </section>

      <footer className="site-footer">
        <div className="container site-footer__inner">
          <span>Built with pose estimation, not assumptions.</span>
        </div>
      </footer>
    </>
  );
}