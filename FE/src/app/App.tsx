import { lazy, Suspense } from "react";
import { Navigate, Route, Routes, useLocation } from "react-router-dom";
import { AppShell } from "../components/AppShell";
import { PageLoader } from "../components/ui";
import { LoginPage, RegisterPage } from "../features/auth/AuthPages";
import { useAuth } from "../features/auth/AuthProvider";
import { ComingSoonPage } from "../pages/ComingSoonPage";
import { HomePage } from "../pages/HomePage";

const DecksPage = lazy(() =>
  import("../features/decks/DeckPages").then((module) => ({
    default: module.DecksPage,
  })),
);
const DeckFormPage = lazy(() =>
  import("../features/decks/DeckPages").then((module) => ({
    default: module.DeckFormPage,
  })),
);
const DeckDetailPage = lazy(() =>
  import("../features/decks/DeckPages").then((module) => ({
    default: module.DeckDetailPage,
  })),
);
const VocabularyCreatePage = lazy(() =>
  import("../features/vocabulary/VocabularyPages").then((module) => ({
    default: module.VocabularyCreatePage,
  })),
);
const VocabularyDetailPage = lazy(() =>
  import("../features/vocabulary/VocabularyPages").then((module) => ({
    default: module.VocabularyDetailPage,
  })),
);
const ProfilePage = lazy(() =>
  import("../features/profile/ProfilePage").then((module) => ({
    default: module.ProfilePage,
  })),
);

function ProtectedLayout() {
  const { user, isBootstrapping } = useAuth();
  const location = useLocation();

  if (isBootstrapping) return <PageLoader label="Restoring your session" />;
  if (!user) {
    return (
      <Navigate
        to="/login"
        replace
        state={{ from: `${location.pathname}${location.search}` }}
      />
    );
  }
  return <AppShell />;
}

function NotFoundPage() {
  return (
    <div className="not-found">
      <img src="/lexiloop-mark.svg" alt="" />
      <p className="eyebrow">404</p>
      <h1>This page left the loop.</h1>
      <p>The address may be wrong or the resource may no longer be available.</p>
      <a className="button button--primary" href="/">
        Return home
      </a>
    </div>
  );
}

export function App() {
  return (
    <Suspense fallback={<PageLoader />}>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route element={<ProtectedLayout />}>
          <Route index element={<HomePage />} />
          <Route path="decks" element={<DecksPage />} />
          <Route path="decks/new" element={<DeckFormPage />} />
          <Route path="decks/:deckId" element={<DeckDetailPage />} />
          <Route path="decks/:deckId/edit" element={<DeckFormPage />} />
          <Route
            path="decks/:deckId/words/new"
            element={<VocabularyCreatePage />}
          />
          <Route
            path="vocabularies/:vocabularyId"
            element={<VocabularyDetailPage />}
          />
          <Route path="learn" element={<ComingSoonPage type="learn" />} />
          <Route path="quiz" element={<ComingSoonPage type="quiz" />} />
          <Route path="profile" element={<ProfilePage />} />
        </Route>
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </Suspense>
  );
}
