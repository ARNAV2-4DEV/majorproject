export default function SkeletonHero() {
  return (
    <svg
      viewBox="0 0 420 460"
      className="skeleton-hero"
      role="img"
      aria-label="Diagram of a figure mid-exercise with joint angles measured at the elbow and knee"
    >
      {/* Torso + limbs */}
      <g stroke="var(--chalk)" strokeWidth="3" strokeLinecap="round" fill="none">
        {/* head */}
        <circle cx="210" cy="60" r="24" />
        {/* spine */}
        <line x1="210" y1="84" x2="205" y2="220" />
        {/* left arm: shoulder -> elbow -> wrist (bent, mid-curl) */}
        <line x1="205" y1="120" x2="150" y2="165" />
        <line x1="150" y1="165" x2="175" y2="105" />
        {/* right arm: relaxed at side */}
        <line x1="205" y1="120" x2="255" y2="175" />
        <line x1="255" y1="175" x2="250" y2="230" />
        {/* left leg: hip -> knee -> ankle (mid-squat) */}
        <line x1="205" y1="220" x2="160" y2="300" />
        <line x1="160" y1="300" x2="180" y2="390" />
        {/* right leg: standing */}
        <line x1="205" y1="220" x2="235" y2="305" />
        <line x1="235" y1="305" x2="230" y2="395" />
      </g>

      {/* Joint points */}
      <g fill="var(--ember)">
        <circle cx="150" cy="165" r="5" />
        <circle cx="160" cy="300" r="5" />
      </g>

      {/* Angle arc: elbow */}
      <g className="angle-arc angle-arc--1">
        <path
          d="M 165 145 A 26 26 0 0 1 148 190"
          stroke="var(--ember)"
          strokeWidth="2"
          fill="none"
        />
        <text x="108" y="150" className="angle-label">
          52&#176;
        </text>
      </g>

      {/* Angle arc: knee */}
      <g className="angle-arc angle-arc--2">
        <path
          d="M 172 282 A 30 30 0 0 1 178 330"
          stroke="var(--sage)"
          strokeWidth="2"
          fill="none"
        />
        <text x="182" y="345" className="angle-label angle-label--sage">
          94&#176;
        </text>
      </g>

      {/* ground line */}
      <line x1="90" y1="410" x2="330" y2="410" stroke="var(--line)" strokeWidth="1" />
    </svg>
  );
}