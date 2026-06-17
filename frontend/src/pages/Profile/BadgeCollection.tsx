import type { Badge } from "../../types/gamification";

const ICON_MAP: Record<string, string> = {
  star: "⭐",
  crown: "👑",
  fire: "🔥",
  cards: "🎴",
  brain: "🧠",
};

interface BadgeCollectionProps {
  badges: Badge[];
}

export default function BadgeCollection({ badges }: BadgeCollectionProps) {
  return (
    <div className="bg-gray-800 rounded-xl p-4 border border-gray-700">
      <h3 className="text-lg font-bold text-gold mb-3">Badges</h3>
      {badges.length === 0 ? (
        <p className="text-gray-500 text-sm">
          Keep training to earn your first badge!
        </p>
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
          {badges.map((badge) => (
            <div
              key={badge.id}
              className="bg-gray-900 rounded-lg p-3 text-center border border-gray-600 hover:border-gold transition-colors"
              title={badge.description}
            >
              <div className="text-2xl mb-1">
                {ICON_MAP[badge.icon] || "🏆"}
              </div>
              <div className="text-xs font-semibold text-white">
                {badge.name}
              </div>
              <div className="text-xs text-gray-500 mt-0.5">
                {badge.description}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
