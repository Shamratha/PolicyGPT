/** Decorative 24-spoke wheel inspired by the Ashoka Chakra. Purely visual. */
export default function ChakraWheel({ className = '' }: { className?: string }) {
  const spokes = Array.from({ length: 24 }, (_, i) => i * 15);
  return (
    <svg viewBox="0 0 200 200" className={className} aria-hidden="true" focusable="false">
      <g fill="none" stroke="currentColor">
        <circle cx="100" cy="100" r="96" strokeWidth="5" />
        <circle cx="100" cy="100" r="84" strokeWidth="1.5" />
        <circle cx="100" cy="100" r="12" strokeWidth="5" />
        {spokes.map((deg) => (
          <g key={deg} transform={`rotate(${deg} 100 100)`}>
            <path d="M100 88 L97 30 L100 12 L103 30 Z" fill="currentColor" stroke="none" />
            <circle cx="100" cy="9" r="2.6" fill="currentColor" stroke="none" transform={`rotate(7.5 100 100)`} />
          </g>
        ))}
      </g>
    </svg>
  );
}
