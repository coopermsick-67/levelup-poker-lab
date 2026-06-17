import type { LeaderboardEntry } from "../../types/gamification";

interface LeaderboardProps {
  entries: LeaderboardEntry[];
  userRank: number | null;
  currentUserId: number;
}

function RankBadge({ rank }: { rank: number }) {
  if (rank === 1) return <span className="text-lg">🥇</span>;
  if (rank === 2) return <span className="text-lg">🥈</span>;
  if (rank === 3) return <span className="text-lg">🥉</span>;
  return (
    <span className="text-sm font-mono text-gray-400 w-6 text-center">
      {rank}
    </span>
  );
}

export default function Leaderboard({
  entries,
  userRank,
  currentUserId,
}: LeaderboardProps) {
  return (
    <div className="bg-gray-800 rounded-xl p-4 border border-gray-700">
      <h3 className="text-lg font-bold text-gold mb-3">Leaderboard</h3>

      {entries.length === 0 ? (
        <p className="text-gray-500 text-sm">
          No players yet. Be the first to climb the ranks!
        </p>
      ) : (
        <div className="space-y-1">
          {/* Header */}
          <div className="grid grid-cols-[2rem_1fr_4rem_4rem_4rem] gap-2 px-2 py-1 text-xs text-gray-500 font-medium border-b border-gray-700">
            <span></span>
            <span>Player</span>
            <span className="text-right">Level</span>
            <span className="text-right">Rating</span>
            <span className="text-right">Streak</span>
          </div>

          {entries.map((entry) => {
            const isCurrentUser = entry.user_id === currentUserId;
            return (
              <div
                key={entry.rank}
                className={`grid grid-cols-[2rem_1fr_4rem_4rem_4rem] gap-2 px-2 py-2 rounded-lg items-center ${
                  isCurrentUser
                    ? "bg-felt/30 border border-gold/40"
                    : "hover:bg-gray-700/50"
                }`}
              >
                <RankBadge rank={entry.rank} />
                <div className="min-w-0">
                  <div
                    className={`text-sm font-medium truncate ${
                      isCurrentUser ? "text-gold" : "text-white"
                    }`}
                  >
                    {entry.display_name}
                  </div>
                  <div className="text-xs text-gray-500 truncate">
                    @{entry.username}
                  </div>
                </div>
                <span className="text-sm text-gray-300 text-right">
                  {entry.level}
                </span>
                <span className="text-sm text-gray-300 text-right">
                  {entry.skill_rating}
                </span>
                <span className="text-sm text-gray-300 text-right">
                  {entry.streak > 0 ? `🔥 ${entry.streak}` : "-"}
                </span>
              </div>
            );
          })}
        </div>
      )}

      {userRank && userRank > 20 && (
        <div className="mt-3 pt-3 border-t border-gray-700 text-center">
          <span className="text-sm text-gray-400">
            Your rank: <span className="text-gold font-medium">#{userRank}</span>
          </span>
        </div>
      )}
    </div>
  );
}
