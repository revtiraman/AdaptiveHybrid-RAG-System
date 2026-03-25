import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface Notification {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  description: string;
  timestamp: string;
  read: boolean;
  href?: string;
}

interface AppState {
  sidebarCollapsed: boolean;
  setSidebarCollapsed: (v: boolean) => void;

  notifications: Notification[];
  addNotification: (n: Omit<Notification, 'id' | 'timestamp' | 'read'>) => void;
  markAllRead: () => void;
  dismissNotification: (id: string) => void;
  clearNotifications: () => void;

  commandOpen: boolean;
  setCommandOpen: (v: boolean) => void;

  queryDrawerOpen: boolean;
  queryDrawerEntryId: string | null;
  openQueryDrawer: (id: string) => void;
  closeQueryDrawer: () => void;
}

export const useAppStore = create<AppState>()(
  persist(
    (set) => ({
      sidebarCollapsed: false,
      setSidebarCollapsed: (v) => set({ sidebarCollapsed: v }),

      notifications: [],
      addNotification: (n) =>
        set((s) => ({
          notifications: [
            {
              ...n,
              id: crypto.randomUUID(),
              timestamp: new Date().toISOString(),
              read: false,
            },
            ...s.notifications,
          ].slice(0, 50),
        })),
      markAllRead: () =>
        set((s) => ({
          notifications: s.notifications.map((n) => ({ ...n, read: true })),
        })),
      dismissNotification: (id) =>
        set((s) => ({
          notifications: s.notifications.filter((n) => n.id !== id),
        })),
      clearNotifications: () => set({ notifications: [] }),

      commandOpen: false,
      setCommandOpen: (v) => set({ commandOpen: v }),

      queryDrawerOpen: false,
      queryDrawerEntryId: null,
      openQueryDrawer: (id) => set({ queryDrawerOpen: true, queryDrawerEntryId: id }),
      closeQueryDrawer: () => set({ queryDrawerOpen: false, queryDrawerEntryId: null }),
    }),
    {
      name: 'rag-app-store',
      partialize: (s) => ({
        sidebarCollapsed: s.sidebarCollapsed,
        notifications: s.notifications,
      }),
    },
  ),
);
