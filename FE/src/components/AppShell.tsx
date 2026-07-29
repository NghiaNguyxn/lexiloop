import {
  Books,
  Brain,
  CaretLeft,
  CaretRight,
  House,
  SignOut,
  Sparkle,
  UserCircle,
} from "@phosphor-icons/react";
import { useEffect, useRef, useState } from "react";
import {
  NavLink,
  Outlet,
  useLocation,
  useNavigate,
  useNavigationType,
} from "react-router-dom";
import { useAuth } from "../features/auth/AuthProvider";

const navigation = [
  { to: "/", label: "Home", icon: House, end: true },
  { to: "/decks", label: "Decks", icon: Books },
  { to: "/learn", label: "Learn", icon: Brain },
  { to: "/quiz", label: "Quiz", icon: Sparkle },
  { to: "/profile", label: "Profile", icon: UserCircle },
];

export function AppShell() {
  const [collapsed, setCollapsed] = useState(false);
  const { user, signOut } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const navigationType = useNavigationType();
  const mainContentRef = useRef<HTMLElement>(null);

  useEffect(() => {
    const frame = window.requestAnimationFrame(() => {
      mainContentRef.current?.focus({ preventScroll: true });

      if (navigationType !== "POP") {
        window.scrollTo({ top: 0, left: 0, behavior: "auto" });
      }
    });

    return () => window.cancelAnimationFrame(frame);
  }, [location.pathname, navigationType]);

  const handleSignOut = async () => {
    await signOut();
    navigate("/login", { replace: true });
  };

  return (
    <div className={`app-shell ${collapsed ? "app-shell--collapsed" : ""}`}>
      <a className="skip-link" href="#main-content">
        Skip to content
      </a>
      <aside className="sidebar" aria-label="Primary navigation">
        <NavLink to="/" className="brand" aria-label="LexiLoop home">
          <img src="/lexiloop-mark.svg" alt="" />
          <span>LexiLoop</span>
        </NavLink>
        <nav className="sidebar__nav">
          {navigation.map(({ to, label, icon: Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                `nav-item ${isActive ? "nav-item--active" : ""}`
              }
            >
              <Icon aria-hidden size={22} weight="duotone" />
              <span>{label}</span>
            </NavLink>
          ))}
        </nav>
        <div className="sidebar__footer">
          <div className="sidebar__profile">
            <span className="avatar" aria-hidden>
              {(user?.full_name || user?.username || "U")[0]?.toUpperCase()}
            </span>
            <span>
              <strong>{user?.full_name || user?.username}</strong>
              <small>{user?.email}</small>
            </span>
          </div>
          <button type="button" className="nav-item" onClick={handleSignOut}>
            <SignOut aria-hidden size={22} />
            <span>Sign out</span>
          </button>
        </div>
        <button
          type="button"
          className="sidebar__toggle"
          onClick={() => setCollapsed((value) => !value)}
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {collapsed ? (
            <CaretRight aria-hidden />
          ) : (
            <CaretLeft aria-hidden />
          )}
        </button>
      </aside>

      <main
        ref={mainContentRef}
        id="main-content"
        className="main-content"
        tabIndex={-1}
      >
        <Outlet />
      </main>

      <nav className="mobile-nav" aria-label="Mobile navigation">
        {navigation.map(({ to, label, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            aria-current={
              location.pathname === to ||
              (!end && location.pathname.startsWith(to))
                ? "page"
                : undefined
            }
          >
            <Icon aria-hidden size={22} weight="duotone" />
            <span>{label}</span>
          </NavLink>
        ))}
      </nav>
    </div>
  );
}
