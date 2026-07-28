import { Brain, Sparkle } from "@phosphor-icons/react";
import { ButtonLink, EmptyState } from "../components/ui";

export function ComingSoonPage({ type }: { type: "learn" | "quiz" }) {
  const isLearn = type === "learn";
  return (
    <div className="page page--centered">
      <EmptyState
        icon={
          isLearn ? (
            <Brain aria-hidden size={38} weight="duotone" />
          ) : (
            <Sparkle aria-hidden size={38} weight="duotone" />
          )
        }
        title={isLearn ? "Learning is the next loop" : "Quizzes are coming next"}
        description={
          isLearn
            ? "The vocabulary library is ready. Spaced repetition and study sessions will arrive in the learning phase."
            : "Quiz modes will be connected once learning state and review history are available."
        }
        action={<ButtonLink to="/decks">Keep building vocabulary</ButtonLink>}
      />
    </div>
  );
}
