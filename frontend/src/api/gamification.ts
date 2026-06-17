/** Gamification API client */

import { api } from "./client";
import type {
  GamificationProfile,
  Quest,
  LeaderboardResponse,
  DailyClaimResult,
} from "../types/gamification";

export async function getGamificationProfile(): Promise<GamificationProfile> {
  return api<GamificationProfile>("/gamification/profile");
}

export async function getActiveQuests(): Promise<{ quests: Quest[] }> {
  return api<{ quests: Quest[] }>("/gamification/quests");
}

export async function getLeaderboard(): Promise<LeaderboardResponse> {
  return api<LeaderboardResponse>("/gamification/leaderboard");
}

export async function claimDailyBonus(): Promise<DailyClaimResult> {
  return api<DailyClaimResult>("/gamification/claim-daily", { method: "POST" });
}
