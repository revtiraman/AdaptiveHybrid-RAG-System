import React from 'react';
import { motion } from 'framer-motion';
import {
  Bell, FileCheck, AlertCircle, BarChart2, AlertTriangle, X, Check,
} from 'lucide-react';
import { useAppStore, type Notification } from '../lib/store';
import { formatDistanceToNow } from 'date-fns';

const TYPE_CONFIG = {
  success: { icon: FileCheck,     color: 'var(--success-text)',  bg: 'var(--success-bg)',  border: 'var(--success-border)' },
  error:   { icon: AlertCircle,   color: 'var(--danger-text)',   bg: 'var(--danger-bg)',   border: 'var(--danger-border)'  },
  info:    { icon: BarChart2,     color: 'var(--info-text)',     bg: 'var(--info-bg)',     border: 'var(--info-border)'    },
  warning: { icon: AlertTriangle, color: 'var(--warning-text)',  bg: 'var(--warning-bg)',  border: 'var(--warning-border)' },
};

interface Props { onClose: () => void; }

export default function NotificationCenter({ onClose }: Props) {
  const { notifications, markAllRead, dismissNotification, clearNotifications } = useAppStore();
  const unread = notifications.filter(n => !n.read).length;

  return (
    <motion.div
      initial={{ opacity: 0, y: -8, scale: 0.97 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: -8, scale: 0.97 }}
      transition={{ duration: 0.15, ease: [0.16, 1, 0.3, 1] }}
      style={{
        position: 'absolute', top: 'calc(100% + 8px)', right: 0,
        width: 340, zIndex: 300,
        background: 'var(--bg-raised)',
        border: '1px solid var(--border-subtle)',
        borderRadius: 16,
        boxShadow: '0 24px 80px rgba(0,0,0,0.7)',
        overflow: 'hidden',
      }}
      onClick={e => e.stopPropagation()}
    >
      {/* Header */}
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '14px 16px',
        borderBottom: '1px solid var(--border-faint)',
      }}>
        <span style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)' }}>
          Notifications
          {unread > 0 && (
            <span style={{
              marginLeft: 8, fontSize: 10, fontWeight: 600,
              background: 'var(--brand-500)', color: 'white',
              padding: '1px 6px', borderRadius: 999,
            }}>
              {unread}
            </span>
          )}
        </span>
        <div style={{ display: 'flex', gap: 8 }}>
          {unread > 0 && (
            <button
              onClick={markAllRead}
              style={{
                fontSize: 12, color: 'var(--text-brand)', background: 'none',
                border: 'none', cursor: 'pointer', padding: '2px 4px', borderRadius: 4,
              }}
            >
              Mark all read
            </button>
          )}
          <button
            onClick={onClose}
            style={{
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              width: 24, height: 24, background: 'none', border: 'none',
              cursor: 'pointer', color: 'var(--text-muted)', borderRadius: 4,
            }}
          >
            <X size={14} />
          </button>
        </div>
      </div>

      {/* List */}
      <div style={{ maxHeight: 360, overflowY: 'auto' }} className="scroll-area">
        {notifications.length === 0 ? (
          <div style={{
            display: 'flex', flexDirection: 'column', alignItems: 'center',
            padding: '32px 16px', gap: 8,
          }}>
            <Bell size={28} style={{ color: 'var(--text-muted)', opacity: 0.4 }} />
            <span style={{ fontSize: 13, color: 'var(--text-muted)' }}>All caught up</span>
          </div>
        ) : (
          notifications.map((n) => (
            <NotifItem
              key={n.id}
              notification={n}
              onDismiss={() => dismissNotification(n.id)}
            />
          ))
        )}
      </div>

      {/* Footer */}
      {notifications.length > 0 && (
        <div style={{
          padding: '10px 16px',
          borderTop: '1px solid var(--border-faint)',
          display: 'flex', justifyContent: 'flex-end',
        }}>
          <button
            onClick={clearNotifications}
            style={{
              fontSize: 12, color: 'var(--text-muted)',
              background: 'none', border: 'none', cursor: 'pointer',
            }}
          >
            Clear all
          </button>
        </div>
      )}
    </motion.div>
  );
}

function NotifItem({ notification: n, onDismiss }: { notification: Notification; onDismiss: () => void }) {
  const cfg = TYPE_CONFIG[n.type];
  const Icon = cfg.icon;
  const [hovered, setHovered] = React.useState(false);

  return (
    <motion.div
      initial={{ opacity: 0, x: 10 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -10 }}
      style={{
        display: 'flex', gap: 10,
        padding: '10px 12px',
        borderBottom: '1px solid var(--border-faint)',
        background: !n.read ? 'rgba(99,102,241,0.04)' : 'transparent',
        borderLeft: !n.read ? '3px solid var(--brand-500)' : '3px solid transparent',
        cursor: 'pointer',
        position: 'relative',
        transition: 'background 120ms',
      }}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      {/* Icon circle */}
      <div style={{
        width: 32, height: 32, borderRadius: '50%',
        background: cfg.bg, border: `1px solid ${cfg.border}`,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        flexShrink: 0,
      }}>
        <Icon size={14} style={{ color: cfg.color }} />
      </div>

      {/* Content */}
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)', lineHeight: 1.3 }}>
          {n.title}
        </div>
        <div style={{
          fontSize: 12, color: 'var(--text-secondary)',
          marginTop: 2, lineHeight: 1.4,
          overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
        }}>
          {n.description}
        </div>
        <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 3 }}>
          {formatDistanceToNow(new Date(n.timestamp), { addSuffix: true })}
        </div>
      </div>

      {/* Dismiss */}
      {hovered && (
        <button
          onClick={e => { e.stopPropagation(); onDismiss(); }}
          style={{
            position: 'absolute', top: 8, right: 8,
            width: 20, height: 20,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            background: 'var(--bg-overlay)', border: 'none',
            borderRadius: 4, cursor: 'pointer', color: 'var(--text-muted)',
          }}
        >
          <X size={11} />
        </button>
      )}
    </motion.div>
  );
}
