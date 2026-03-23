import { AnimatePresence, motion } from 'framer-motion';
import type { ReactNode } from 'react';
import { Suspense, lazy } from 'react';
import { Navigate, Route, Routes, useLocation } from 'react-router-dom';
import { AppShell } from './components/layout/AppShell';

const ChatInterface = lazy(() => import('./components/chat/ChatInterface').then((m) => ({ default: m.ChatInterface })));
const DocumentStructureViewer = lazy(() =>
  import('./components/structure/DocumentStructureViewer').then((m) => ({ default: m.DocumentStructureViewer })),
);
const ClaimsPanel = lazy(() => import('./components/claims/ClaimsPanel').then((m) => ({ default: m.ClaimsPanel })));
const KnowledgeGraphViewer = lazy(() =>
  import('./components/graph/KnowledgeGraphViewer').then((m) => ({ default: m.KnowledgeGraphViewer })),
);
const EvaluationDashboard = lazy(() =>
  import('./components/eval/EvaluationDashboard').then((m) => ({ default: m.EvaluationDashboard })),
);
const LiteratureReviewPanel = lazy(() =>
  import('./components/review/LiteratureReviewPanel').then((m) => ({ default: m.LiteratureReviewPanel })),
);
const AnnotationPanel = lazy(() =>
  import('./components/annotations/AnnotationPanel').then((m) => ({ default: m.AnnotationPanel })),
);
const ArXivMonitor = lazy(() => import('./components/monitor/ArXivMonitor').then((m) => ({ default: m.ArXivMonitor })));
const SettingsPanel = lazy(() => import('./components/settings/SettingsPanel').then((m) => ({ default: m.SettingsPanel })));
const ShortcutsModal = lazy(() => import('./components/help/ShortcutsModal').then((m) => ({ default: m.ShortcutsModal })));

function RouteFallback() {
  return <div className="h-full p-4"><div className="skeleton h-24 w-full" /></div>;
}

function AnimatedPage({ children }: { children: ReactNode }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -6 }}
      transition={{ duration: 0.2 }}
      className="h-full"
    >
      {children}
    </motion.div>
  );
}

function ContentRoutes() {
  return (
    <Suspense fallback={<RouteFallback />}>
      <Routes>
        <Route path="/" element={<Navigate to="/chat" replace />} />
        <Route path="/chat" element={<AnimatedPage><ChatInterface /></AnimatedPage>} />
        <Route path="/chat/:sessionId" element={<AnimatedPage><ChatInterface /></AnimatedPage>} />
        <Route path="/structure" element={<AnimatedPage><DocumentStructureViewer /></AnimatedPage>} />
        <Route path="/structure/:paperId" element={<AnimatedPage><DocumentStructureViewer /></AnimatedPage>} />
        <Route path="/claims" element={<AnimatedPage><ClaimsPanel /></AnimatedPage>} />
        <Route path="/graph" element={<AnimatedPage><KnowledgeGraphViewer /></AnimatedPage>} />
        <Route path="/eval" element={<AnimatedPage><EvaluationDashboard /></AnimatedPage>} />
        <Route path="/review" element={<AnimatedPage><LiteratureReviewPanel /></AnimatedPage>} />
        <Route path="/annotate" element={<AnimatedPage><AnnotationPanel /></AnimatedPage>} />
        <Route path="/monitor" element={<AnimatedPage><ArXivMonitor /></AnimatedPage>} />
        <Route path="/settings" element={<AnimatedPage><SettingsPanel /></AnimatedPage>} />
        <Route path="/help" element={<AnimatedPage><ShortcutsModal /></AnimatedPage>} />
        <Route path="*" element={<Navigate to="/chat" replace />} />
      </Routes>
    </Suspense>
  );
}

export function AppRouter() {
  const location = useLocation();
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route
          path="*"
          element={
            <AnimatePresence mode="wait" initial={false}>
              <div key={location.pathname} className="h-full">
                <ContentRoutes />
              </div>
            </AnimatePresence>
          }
        />
      </Route>
    </Routes>
  );
}
