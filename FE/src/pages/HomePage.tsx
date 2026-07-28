import {
  ArrowRight,
  Books,
  Brain,
  Lightning,
  Plus,
  Sparkle,
} from "@phosphor-icons/react";
import { useQuery } from "@tanstack/react-query";
import { ButtonLink, PageLoader } from "../components/ui";
import { useAuth } from "../features/auth/AuthProvider";
import { deckApi } from "../lib/api";

export function HomePage() {
  const { user } = useAuth();
  const { data: decks, isLoading } = useQuery({
    queryKey: ["decks", "owned"],
    queryFn: deckApi.owned,
  });
  const firstName = (user?.full_name || user?.username || "there").split(" ")[0];

  if (isLoading) return <PageLoader label="Preparing your library" />;

  return (
    <div className="page">
      <section className="home-hero">
        <div>
          <p className="eyebrow eyebrow--light">Your vocabulary space</p>
          <h1>Welcome back, {firstName}.</h1>
          <p>
            Keep collecting useful words and the context that makes them stick.
          </p>
          <div className="home-hero__actions">
            <ButtonLink to="/decks">
              Open my decks <ArrowRight aria-hidden />
            </ButtonLink>
            <ButtonLink to="/decks/new" variant="secondary">
              <Plus aria-hidden /> Create a deck
            </ButtonLink>
          </div>
        </div>
        <div className="home-hero__orbit" aria-hidden>
          <img src="/lexiloop-mark.svg" alt="" />
        </div>
      </section>

      <section className="metric-grid" aria-label="Library overview">
        <article className="metric-card metric-card--indigo">
          <Books aria-hidden size={25} weight="duotone" />
          <div>
            <strong>{decks?.length ?? 0}</strong>
            <span>Personal decks</span>
          </div>
        </article>
        <article className="metric-card metric-card--mint">
          <Brain aria-hidden size={25} weight="duotone" />
          <div>
            <strong>Build first</strong>
            <span>Learning arrives next</span>
          </div>
        </article>
        <article className="metric-card metric-card--amber">
          <Lightning aria-hidden size={25} weight="duotone" />
          <div>
            <strong>Context-rich</strong>
            <span>Meanings and examples</span>
          </div>
        </article>
      </section>

      <section className="section">
        <div className="section__heading">
          <div>
            <p className="eyebrow">Continue building</p>
            <h2>Recent decks</h2>
          </div>
          <ButtonLink to="/decks" variant="ghost">
            View all <ArrowRight aria-hidden />
          </ButtonLink>
        </div>
        {decks?.length ? (
          <div className="deck-grid">
            {decks.slice(0, 3).map((deck, index) => (
              <article className={`deck-card deck-card--tone-${index + 1}`} key={deck.id}>
                <div className="deck-card__icon">
                  <Books aria-hidden weight="duotone" />
                </div>
                <span className="badge">{deck.is_public ? "Public" : "Private"}</span>
                <h3>{deck.name}</h3>
                <p>{deck.description || "A growing collection of useful vocabulary."}</p>
                <ButtonLink to={`/decks/${deck.id}`} variant="ghost">
                  Open deck <ArrowRight aria-hidden />
                </ButtonLink>
              </article>
            ))}
          </div>
        ) : (
          <div className="home-empty">
            <Sparkle aria-hidden size={32} weight="duotone" />
            <div>
              <h3>Your first word starts with a deck.</h3>
              <p>Create a focused collection for a topic or learning goal.</p>
            </div>
            <ButtonLink to="/decks/new">Create your first deck</ButtonLink>
          </div>
        )}
      </section>
    </div>
  );
}
