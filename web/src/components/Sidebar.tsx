import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  LayoutDashboard, Library, MessageSquare, BarChart3,
  Settings, ChevronLeft, ChevronRight,
} from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { api } from '../lib/api';
import { useAppStore } from '../lib/store';

const NAV_ITEMS = [
  { to: '/',          icon: LayoutDashboard, label: 'Dashboard', section: 'workspace' },
  { to: '/query',     icon: MessageSquare,   label: 'Query',     section: 'workspace' },
  { to: '/library',   icon: Library,         label: 'Library',   section: 'workspace' },
  { to: '/analytics', icon: BarChart3,       label: 'Analytics', section: 'workspace' },
  { to: '/settings',  icon: Settings,        label: 'Settings',  section: 'system'    },
];

function LogoMark() {
  return (
    <svg width={20} height={22} viewBox="0 0 20 22" fill="none" style={{ flexShrink: 0 }}>
      <rect x="4" y="3" width="14" height="17" rx="2" fill="rgba(255,255,255,0.08)" stroke="rgba(255,255,255,0.15)" strokeWidth="1"/>
      <rect x="1" y="1" width="14" height="17" rx="2" fill="var(--bg-raised)" stroke="var(--border-default)" strokeWidth="1"/>
      <path d="M10 1 L15 1 L15 6 Z" fill="var(--brand-500)" opacity="0.8"/>
      <line x1="3" y1="8"  x2="13" y2="8"  stroke="var(--border-default)" strokeWidth="1" strokeLinecap="round"/>
      <line x1="3" y1="11" x2="10" y2="11" stroke="var(--border-default)" strokeWidth="1" strokeLinecap="round"/>
      <line x1="3" y1="14" x2="8"  y2="14" stroke="var(--border-default)" strokeWidth="1" strokeLinecap="round"/>
      <circle cx="16" cy="2" r="3" fill="var(--accent-500)"/>
      <text x="13.5" y="4" fontSize="4" fill="white" fontWeight="bold">★</text>
    </svg>
  );
}

export default function Sidebar() {
  const { sidebarCollapsed, setSidebarCollapsed } = useAppStore();
  const location = useLocation();
  const collapsed = sidebarCollapsed;
  const W = collapsed ? 56 : 248;

  const { data: papers = [] } = useQuery({
    queryKey: ['papers'],
    queryFn: api.papers,
    staleTime: 30_000,
  });

  const { data: health, isError: healthError } = useQuery({
    queryKey: ['health'],
    queryFn: api.health,
    refetchInterval: 30_000,
    retry: false,
  });

  const { data: stats } = useQuery({
    queryKey: ['stats'],
    queryFn: api.stats,
    staleTime: 60_000,
  });

  const isOnline = !healthError && !!health;

  return (
    <motion.aside
      animate={{ width: W }}
      transition={{ duration: 0.2, ease: [0.25, 1, 0.5, 1] }}
      style={{
        height: '100vh',
        flexShrink: 0,
        display: 'flex',
        flexDirection: 'column',
        background: 'rgba(13,13,26,0.90)',
        backdropFilter: 'blur(20px)',
        WebkitBackdropFilter: 'blur(20px)',
        borderRight: '1px solid var(--border-faint)',
        overflow: 'hidden',
        zIndex: 40,
        position: 'relative',
      }}
    >
      {/* Logo */}
      <div style={{
        height: 64, display: 'flex', alignItems: 'center',
        padding: collapsed ? '0 18px' : '0 16px',
        borderBottom: '1px solid var(--border-faint)',
        gap: 10, flexShrink: 0,
      }}>
        <LogoMark />
        <AnimatePresence>
          {!collapsed && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.12 }}
              style={{ overflow: 'hidden', whiteSpace: 'nowrap' }}
            >
              <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)', lineHeight: 1.2 }}>
                ResearchRAG
              </div>
              <div style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 1 }}>v2.0 alpha</div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Nav */}
      <nav style={{ flex: 1, overflowY: 'auto', overflowX: 'hidden', padding: '12px 8px' }} className="scroll-area">
        <SectionLabel label="Workspace" collapsed={collapsed} />

        <div style={{ position: 'relative' }}>
          {NAV_ITEMS.filter(i => i.section === 'workspace').map((item) => {
            const isActive = location.pathname === item.to ||
              (item.to !== '/' && location.pathname.startsWith(item.to));
            if (!isActive) return null;
            return (
              <motion.div
                key="active-bg"
                layoutId="active-nav-bg"
                className="nav-active-bg"
                style={{
                  position: 'absolute', left: 0, right: 0,
                  top: `${NAV_ITEMS.filter(i => i.section === 'workspace').findIndex(i => i.to === item.to) * 38}px`,
                  height: 36, borderRadius: 8, pointerEvents: 'none',
                }}
                transition={{ duration: 0.2, ease: [0.25, 1, 0.5, 1] }}
              />
            );
          })}

          {NAV_ITEMS.filter(i => i.section === 'workspace').map((item) => (
            <NavItem
              key={item.to}
              item={item}
              collapsed={collapsed}
              paperCount={item.to === '/library' ? papers.length : undefined}
              isLive={item.to === '/query'}
              isOnline={isOnline}
            />
          ))}
        </div>

        <div style={{ marginTop: 16 }}>
          <SectionLabel label="System" collapsed={collapsed} />
          {NAV_ITEMS.filter(i => i.section === 'system').map((item) => (
            <NavItem key={item.to} item={item} collapsed={collapsed} isOnline={isOnline} />
          ))}
        </div>
      </nav>

      {/* Status card */}
      <div style={{ padding: 8, flexShrink: 0 }}>
        {!collapsed ? (
          <div style={{
            background: 'var(--bg-raised)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 10, padding: 12,
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 6 }}>
              <StatusDot online={isOnline} />
              <span style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)' }}>
                {isOnline ? 'API Online' : 'API Offline'}
              </span>
            </div>
            <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
              <Pill label={stats?.embedding_provider?.split('/').pop() ?? 'BGE-M3'} />
              <Pill label={stats?.llm_provider?.split('/').pop() ?? 'Mistral'} />
            </div>
          </div>
        ) : (
          <div style={{ display: 'flex', justifyContent: 'center', padding: '4px 0' }}>
            <StatusDot online={isOnline} />
          </div>
        )}

        <button
          onClick={() => setSidebarCollapsed(!collapsed)}
          style={{
            width: '100%', marginTop: 8,
            display: 'flex', alignItems: 'center',
            justifyContent: collapsed ? 'center' : 'flex-start',
            gap: 6, padding: '6px 8px',
            background: 'transparent', border: 'none',
            borderRadius: 8, cursor: 'pointer',
            color: 'var(--text-muted)', fontSize: 12,
            transition: 'color 120ms, background 120ms',
          }}
          onMouseEnter={e => {
            (e.currentTarget as HTMLButtonElement).style.color = 'var(--text-secondary)';
            (e.currentTarget as HTMLButtonElement).style.background = 'var(--bg-raised)';
          }}
          onMouseLeave={e => {
            (e.currentTarget as HTMLButtonElement).style.color = 'var(--text-muted)';
            (e.currentTarget as HTMLButtonElement).style.background = 'transparent';
          }}
          title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {collapsed
            ? <ChevronRight size={14} />
            : <><ChevronLeft size={14} /><span>Collapse</span></>
          }
        </button>
      </div>
    </motion.aside>
  );
}

function SectionLabel({ label, collapsed }: { label: string; collapsed: boolean }) {
  return (
    <AnimatePresence>
      {!collapsed && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.1 }}
          style={{
            fontSize: 10, fontWeight: 600,
            color: 'var(--text-muted)',
            letterSpacing: '0.12em',
            textTransform: 'uppercase',
            padding: '4px 8px 8px',
          }}
        >
          {label}
        </motion.div>
      )}
    </AnimatePresence>
  );
}

function StatusDot({ online }: { online: boolean }) {
  return (
    <span
      className={online ? 'status-pulse' : ''}
      style={{
        display: 'inline-block', width: 7, height: 7,
        borderRadius: '50%',
        background: online ? 'var(--emerald-500)' : 'var(--rose-500)',
        flexShrink: 0,
      }}
    />
  );
}

function Pill({ label }: { label: string }) {
  return (
    <span style={{
      fontSize: 10, padding: '2px 6px',
      background: 'var(--bg-overlay)',
      color: 'var(--text-secondary)',
      borderRadius: 6,
    }}>
      {label}
    </span>
  );
}

interface NavItemProps {
  item: (typeof NAV_ITEMS)[number];
  collapsed: boolean;
  paperCount?: number;
  isLive?: boolean;
  isOnline?: boolean;
}

function NavItem({ item, collapsed, paperCount, isLive, isOnline }: NavItemProps) {
  const location = useLocation();
  const isActive = location.pathname === item.to ||
    (item.to !== '/' && location.pathname.startsWith(item.to));
  const Icon = item.icon;

  return (
    <NavLink
      to={item.to}
      end={item.to === '/'}
      style={{
        display: 'flex', alignItems: 'center',
        gap: 8,
        padding: collapsed ? '9px 0' : '9px 8px',
        justifyContent: collapsed ? 'center' : 'flex-start',
        borderRadius: 8,
        textDecoration: 'none',
        color: isActive ? 'var(--text-primary)' : 'var(--text-muted)',
        position: 'relative',
        marginBottom: 2,
        borderLeft: isActive ? '2px solid var(--brand-500)' : '2px solid transparent',
        transition: 'color 120ms',
        minHeight: 36,
      }}
    >
      {isActive && (
        <span style={{
          position: 'absolute', left: -1, top: '50%', transform: 'translateY(-50%)',
          width: 4, height: 4, borderRadius: '50%',
          background: 'var(--brand-500)',
          boxShadow: '0 0 6px var(--brand-500)',
        }} />
      )}

      <Icon
        size={18}
        style={{ color: isActive ? 'var(--brand-400)' : 'inherit', flexShrink: 0 }}
      />

      <AnimatePresence>
        {!collapsed && (
          <motion.span
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.1 }}
            style={{
              fontSize: 13,
              fontWeight: isActive ? 500 : 400,
              overflow: 'hidden',
              whiteSpace: 'nowrap',
              flex: 1,
            }}
          >
            {item.label}
          </motion.span>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {!collapsed && paperCount !== undefined && paperCount > 0 && (
          <motion.span
            initial={{ scale: 0.5, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.5, opacity: 0 }}
            transition={{ type: 'spring', stiffness: 400, damping: 15 }}
            style={{
              fontSize: 10, fontWeight: 600,
              background: 'rgba(99,102,241,0.2)',
              color: 'var(--brand-300)',
              padding: '1px 6px',
              borderRadius: 999,
            }}
          >
            {paperCount}
          </motion.span>
        )}
      </AnimatePresence>

      {!collapsed && isLive && (
        <span
          className={isOnline ? 'status-pulse' : ''}
          style={{
            width: 6, height: 6, borderRadius: '50%',
            background: isOnline ? 'var(--emerald-500)' : 'var(--rose-500)',
            flexShrink: 0,
          }}
        />
      )}
    </NavLink>
  );
}
