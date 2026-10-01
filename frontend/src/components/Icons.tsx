type P = { className?: string };
const base = {
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 1.5,
  strokeLinecap: "round" as const,
  strokeLinejoin: "round" as const,
};

/** Brand mark: a tile with a fracture running through it. */
export function Mark({ className }: P) {
  return (
    <svg viewBox="0 0 20 20" className={className} aria-hidden>
      <rect x="1.5" y="1.5" width="17" height="17" rx="5" fill="var(--accent)" fillOpacity="0.16" stroke="var(--accent)" strokeOpacity="0.5" />
      <path d="M6 3.5 9 8.5 7.2 11 11.5 16.5" {...base} stroke="var(--accent)" strokeWidth={1.6} />
    </svg>
  );
}

export function Search({ className }: P) {
  return (
    <svg viewBox="0 0 16 16" className={className} aria-hidden {...base}>
      <circle cx="7" cy="7" r="4.25" />
      <path d="m10.25 10.25 3 3" />
    </svg>
  );
}

export function Close({ className }: P) {
  return (
    <svg viewBox="0 0 16 16" className={className} aria-hidden {...base}>
      <path d="m4.5 4.5 7 7m0-7-7 7" />
    </svg>
  );
}

export function Enter({ className }: P) {
  return (
    <svg viewBox="0 0 16 16" className={className} aria-hidden {...base}>
      <path d="M12.5 3.5v4.25a1.75 1.75 0 0 1-1.75 1.75H4m0 0 2.75-2.75M4 9.5l2.75 2.75" />
    </svg>
  );
}
