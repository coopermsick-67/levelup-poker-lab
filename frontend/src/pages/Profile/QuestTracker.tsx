import type { Quest } from "../../types/gamification";

interface QuestTrackerProps {
  quests: Quest[];
}

function QuestPeriodBadge({ period }: { period: "daily" | "weekly" }) {
  const color =
    period === "daily"
      ? "bg-blue-900 text-blue-300"
      : "bg-purple-900 text-purple-300";
  return (
    <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${color}`}>
      {period}
    </span>
  );
}

function QuestCard({ quest }: { quest: Quest }) {
  return (
    <div
      className={`bg-gray-900 rounded-lg p-3 border transition-colors ${
        quest.claimed
          ? "border-gray-700 opacity-60"
          : quest.completed
          ? "border-gold"
          : "border-gray-600"
      }`}
    >
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <QuestPeriodBadge period={quest.period} />
          <span className="text-sm font-semibold text-white">
            {quest.title}
          </span>
        </div>
        <span className="text-xs font-medium text-gold">
          +{quest.reward_xp} XP
        </span>
      </div>
      <p className="text-xs text-gray-400 mb-2">{quest.description}</p>
      <div className="relative w-full bg-gray-700 rounded-full h-2">
        <div
          className={`h-2 rounded-full transition-all ${
            quest.completed ? "bg-gold" : "bg-felt"
          }`}
          style={{ width: `${quest.progress_pct}%` }}
        />
      </div>
      <div className="flex justify-between mt-1">
        <span className="text-xs text-gray-500">
          {quest.progress} / {quest.target}
        </span>
        {quest.claimed ? (
          <span className="text-xs text-gray-500">Claimed</span>
        ) : quest.completed ? (
          <span className="text-xs text-gold font-medium">Ready!</span>
        ) : (
          <span className="text-xs text-gray-500">{quest.progress_pct}%</span>
        )}
      </div>
    </div>
  );
}

export default function QuestTracker({ quests }: QuestTrackerProps) {
  const dailyQuests = quests.filter((q) => q.period === "daily");
  const weeklyQuests = quests.filter((q) => q.period === "weekly");

  return (
    <div className="bg-gray-800 rounded-xl p-4 border border-gray-700">
      <h3 className="text-lg font-bold text-gold mb-3">Quests</h3>

      <div className="space-y-4">
        <div>
          <h4 className="text-sm font-semibold text-gray-300 mb-2">Daily</h4>
          <div className="grid gap-2">
            {dailyQuests.map((q) => (
              <QuestCard key={q.id} quest={q} />
            ))}
          </div>
        </div>

        <div>
          <h4 className="text-sm font-semibold text-gray-300 mb-2">Weekly</h4>
          <div className="grid gap-2">
            {weeklyQuests.map((q) => (
              <QuestCard key={q.id} quest={q} />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
