import { useEffect, useState, useCallback } from "react";
import {
  getGamificationProfile,
  getActiveQuests,
  getLeaderboard,
  claimDailyBonus,
} from "../../api/gamification";
import type {
  GamificationProfile as ProfileType,
  Quest,
  LeaderboardEntry,
} from "../../types/gamification";
import QuestTracker from "./QuestTracker";
import BadgeCollection from "./BadgeCollection";
import Leaderboard from "./Leaderboard";

type Tab = "overview" | "quests" | "leaderboard";

function XPBar({ profile }: { profile: ProfileType }) {
  const isMax = profile.progress.is_max_level;
  return (
    <div className="w-full">
      <div className="flex justify-between items-baseline mb-1">
        <span className="text-sm font-medium text-gray-300">
          Level {profile.level}
        </span>
        <span className="text-xs text-gray-500">
          {isMax
            ? "Max Level!"
            : `${profile.progress.xp_in_level} / ${profile.progress.xp_needed_for_next} XP`}
        </span>
      </div>
      <div className="relative w-full bg-gray-700 rounded-full h-3 overflow-hidden">
        <div
          className="h-full rounded-full bg-gradient-to-r from-felt to-gold transition-all duration-500"
          style={{ width: `${profile.progress.progress_pct}%` }}
        />
        {profile.progress.progress_pct > 0 && (
          <div className="absolute inset-0 bg-gold/10 rounded-full" />
        )}
      </div>
      {!isMax && (
        <p className="text-xs text-gray-500 mt-1">
          {profile.progress.xp_needed_for_next - profile.progress.xp_in_level} XP to Level{" "}
          {profile.level + 1}
        </p>
      )}
    </div>
  );
}

function StatCard({
  label,
  value,
  icon,
}: {
  label: string;
  value: string | number;
  icon: string;
}) {
  return (
    <div className="bg-gray-900 rounded-lg p-3 border border-gray-700 text-center">
      <div className="text-lg mb-1">{icon}</div>
      <div className="text-xl font-bold text-white">{value}</div>
      <div className="text-xs text-gray-500">{label}</div>
    </div>
  );
}

export default function Profile() {
  const [profile, setProfile] = useState<ProfileType | null>(null);
  const [quests, setQuests] = useState<Quest[]>([]);
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([]);
  const [userRank, setUserRank] = useState<number | null>(null);
  const [activeTab, setActiveTab] = useState<Tab>("overview");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [claimMessage, setClaimMessage] = useState<string | null>(null);
  const [claiming, setClaiming] = useState(false);

  const loadData = useCallback(async () => {
    try {
      const [profileData, questsData, lbData] = await Promise.all([
        getGamificationProfile(),
        getActiveQuests(),
        getLeaderboard(),
      ]);
      setProfile(profileData);
      setQuests(questsData.quests);
      setLeaderboard(lbData.leaderboard);
      setUserRank(lbData.user_rank);
      setError(null);
    } catch (err) {
      setError("Failed to load profile data. Please try again.");
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleClaimDaily = async () => {
    if (claiming) return;
    setClaiming(true);
    try {
      const result = await claimDailyBonus();
      setClaimMessage(
        `+${result.xp_earned} XP earned! ${result.streak_message}`
      );
      await loadData();
      setTimeout(() => setClaimMessage(null), 5000);
    } catch (err: any) {
      if (err.message?.includes("400")) {
        setClaimMessage("Daily bonus already claimed today!");
      } else {
        setClaimMessage("Could not claim daily bonus. Try again later.");
      }
      setTimeout(() => setClaimMessage(null), 3000);
    } finally {
      setClaiming(false);
    }
  };

  if (typeof window !== 'undefined' && !localStorage.getItem('access_token')) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] gap-4 p-4">
        <div className="text-4xl">🃏</div>
        <h2 className="text-2xl font-bold text-gold">Profile</h2>
        <p className="text-gray-400 text-center">
          Please sign in or create an account to view your profile.
        </p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-gray-400 animate-pulse">Loading profile...</div>
      </div>
    );
  }

  if (error || !profile) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] gap-4">
        <p className="text-red-400">{error || "Something went wrong"}</p>
        <button
          onClick={loadData}
          className="bg-gold text-gray-900 font-medium px-4 py-2 rounded-lg text-sm hover:bg-gold-dark"
        >
          Retry
        </button>
      </div>
    );
  }

  const tabs: { key: Tab; label: string }[] = [
    { key: "overview", label: "Overview" },
    { key: "quests", label: "Quests" },
    { key: "leaderboard", label: "Leaderboard" },
  ];

  return (
    <div className="max-w-2xl mx-auto space-y-4 p-4">
      {/* Header Card */}
      <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
        <div className="flex items-center gap-4 mb-4">
          <div className="w-16 h-16 rounded-full bg-felt-dark border-2 border-gold flex items-center justify-center text-2xl">
            {profile.display_name.charAt(0).toUpperCase()}
          </div>
          <div>
            <h1 className="text-xl font-bold text-white">
              {profile.display_name}
            </h1>
            <p className="text-sm text-gray-400">@{profile.username}</p>
          </div>
        </div>

        <XPBar profile={profile} />

        <div className="grid grid-cols-4 gap-2 mt-4">
          <StatCard icon="🔥" label="Streak" value={profile.streak} />
          <StatCard
            icon="🏆"
            label="Longest"
            value={profile.longest_streak}
          />
          <StatCard
            icon="📊"
            label="Rating"
            value={profile.skill_rating}
          />
          <StatCard icon="🎴" label="Total XP" value={profile.xp} />
        </div>
      </div>

      {/* Daily Claim Button */}
      <button
        onClick={handleClaimDaily}
        disabled={claiming}
        className="w-full bg-felt hover:bg-felt-dark disabled:opacity-50 text-white font-medium py-3 rounded-lg transition-colors flex items-center justify-center gap-2 border border-felt"
      >
        <span className="text-lg">☀️</span>
        {claiming ? "Claiming..." : "Claim Daily Login Bonus"}
      </button>

      {claimMessage && (
        <div className="bg-felt/20 border border-felt rounded-lg p-3 text-center text-sm text-green-300">
          {claimMessage}
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-1 bg-gray-800 rounded-lg p-1 border border-gray-700">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`flex-1 py-2 text-sm font-medium rounded-md transition-colors ${
              activeTab === tab.key
                ? "bg-gold text-gray-900"
                : "text-gray-400 hover:text-white"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      {activeTab === "overview" && (
        <div className="space-y-4">
          <BadgeCollection badges={profile.badges} />
          {/* Show first 3 quests as a preview */}
          {quests.length > 0 && (
            <div className="bg-gray-800 rounded-xl p-4 border border-gray-700">
              <div className="flex justify-between items-center mb-3">
                <h3 className="text-lg font-bold text-gold">Active Quests</h3>
                <button
                  onClick={() => setActiveTab("quests")}
                  className="text-sm text-gold hover:underline"
                >
                  View all
                </button>
              </div>
              <div className="space-y-2">
                {quests.slice(0, 3).map((q) => (
                  <div
                    key={q.id}
                    className="flex items-center justify-between bg-gray-900 rounded-lg px-3 py-2 border border-gray-700"
                  >
                    <div>
                      <span className="text-xs text-gray-500 capitalize">
                        {q.period}
                      </span>
                      <span className="text-sm text-white ml-2">
                        {q.title}
                      </span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-gray-500">
                        {q.progress}/{q.target}
                      </span>
                      {q.completed && (
                        <span className="text-xs text-green-400">Done</span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {activeTab === "quests" && <QuestTracker quests={quests} />}

      {activeTab === "leaderboard" && (
        <Leaderboard
          entries={leaderboard}
          userRank={userRank}
          currentUserId={profile.user_id}
        />
      )}
    </div>
  );
}
