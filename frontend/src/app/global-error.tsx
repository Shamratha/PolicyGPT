'use client';

/** Last-resort error screen if the root layout itself fails. Uses plain inline styles on purpose. */
export default function GlobalError({ reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return (
    <html lang="en">
      <body style={{ fontFamily: 'system-ui, sans-serif', background: '#fff', color: '#141836', display: 'grid', placeItems: 'center', minHeight: '100vh', margin: 0 }}>
        <div style={{ textAlign: 'center', maxWidth: 480, padding: 24 }}>
          <h1 style={{ fontSize: 28, marginBottom: 12 }}>PolicyGPT hit an unexpected problem</h1>
          <p style={{ color: '#3f4562', marginBottom: 24 }}>Please reload the page. Your saved data is not affected.</p>
          <button
            type="button"
            onClick={reset}
            style={{ background: '#2338a8', color: '#fff', border: 0, borderRadius: 12, padding: '12px 22px', fontWeight: 700, cursor: 'pointer' }}
          >
            Reload
          </button>
        </div>
      </body>
    </html>
  );
}
