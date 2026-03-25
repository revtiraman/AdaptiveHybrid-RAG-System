import React, { useEffect, useRef } from 'react';
import { useLocation } from 'react-router-dom';

const routeOrbs: Record<string, [string, string, string, string, string, string]> = {
  '/':          ['15%', '20%', '85%', '60%', '50%', '90%'],
  '/library':   ['20%', '10%', '80%', '50%', '40%', '85%'],
  '/query':     ['10%', '30%', '90%', '40%', '55%', '80%'],
  '/analytics': ['25%', '15%', '75%', '65%', '50%', '95%'],
  '/settings':  ['30%', '25%', '70%', '70%', '45%', '88%'],
};

export default function AmbientBackground() {
  const location = useLocation();
  const orb1Ref = useRef<HTMLDivElement>(null);
  const orb2Ref = useRef<HTMLDivElement>(null);
  const orb3Ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const key = Object.keys(routeOrbs).find(k => location.pathname.startsWith(k) && k !== '/')
      ?? '/';
    const [l1, t1, l2, t2, l3, t3] = routeOrbs[key] ?? routeOrbs['/'];
    if (orb1Ref.current) { orb1Ref.current.style.left = l1; orb1Ref.current.style.top = t1; }
    if (orb2Ref.current) { orb2Ref.current.style.left = l2; orb2Ref.current.style.top = t2; }
    if (orb3Ref.current) { orb3Ref.current.style.left = l3; orb3Ref.current.style.top = t3; }
  }, [location.pathname]);

  return (
    <div
      aria-hidden
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: -1,
        background: 'var(--bg-canvas)',
        overflow: 'hidden',
        pointerEvents: 'none',
      }}
    >
      {/* Noise texture */}
      <div style={{
        position: 'absolute', inset: 0, opacity: 0.03,
        backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='200' height='200'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' stitchTiles='stitch'/%3E%3CfeColorMatrix type='saturate' values='0'/%3E%3C/filter%3E%3Crect width='200' height='200' filter='url(%23n)'/%3E%3C/svg%3E")`,
        backgroundRepeat: 'repeat',
      }} />

      {/* Grid overlay */}
      <div style={{
        position: 'absolute', inset: 0,
        backgroundImage: `
          linear-gradient(rgba(255,255,255,0.015) 1px, transparent 1px),
          linear-gradient(90deg, rgba(255,255,255,0.015) 1px, transparent 1px)
        `,
        backgroundSize: '80px 80px',
      }} />

      {/* Orb 1 — indigo */}
      <div ref={orb1Ref} style={{
        position: 'absolute',
        width: 800, height: 800,
        borderRadius: '50%',
        background: 'radial-gradient(circle, rgba(99,102,241,0.08) 0%, transparent 70%)',
        transform: 'translate(-50%, -50%)',
        left: '15%', top: '20%',
        transition: 'left 2s ease, top 2s ease',
      }} />

      {/* Orb 2 — violet */}
      <div ref={orb2Ref} style={{
        position: 'absolute',
        width: 600, height: 600,
        borderRadius: '50%',
        background: 'radial-gradient(circle, rgba(139,92,246,0.06) 0%, transparent 70%)',
        transform: 'translate(-50%, -50%)',
        left: '85%', top: '60%',
        transition: 'left 2s ease, top 2s ease',
      }} />

      {/* Orb 3 — cyan */}
      <div ref={orb3Ref} style={{
        position: 'absolute',
        width: 500, height: 500,
        borderRadius: '50%',
        background: 'radial-gradient(circle, rgba(6,182,212,0.05) 0%, transparent 70%)',
        transform: 'translate(-50%, -50%)',
        left: '50%', top: '90%',
        transition: 'left 2s ease, top 2s ease',
      }} />
    </div>
  );
}
