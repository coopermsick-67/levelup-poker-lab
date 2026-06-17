/** TypeScript interfaces for the Gamification system */

export interface LevelProgress {
  current_level: number;
  xp_in_level: number;
  xp_needed_for_next: number;
  progress_pct: number;
  is_max_level: boolean;
}

export interface GamificationProfile {
  user_id: number;
  display_name: string;
  username: string;
  level: number;
  xp: number;
  next_level_xp: number | null;
  progress: LevelProgress;
  streak: number;
  longest_streak: number;
  skill_rating: number;
  badges: Badge[];
  total_hands: number;
}

export interface Badge {
  id: string;
  name: string;
  icon: string;
  description: string;
}

export interface Quest {
  id: string;
  title: string;
  description: string;
  target: number;
  progress: number;
  reward_xp: number;
  completed: boolean;
  claimed: boolean;
  period: "daily" | "weekly";
  progress_pct: number;
}

export interface LeaderboardEntry {
  rank: number;
  user_id: number;
  display_name: string;
  username: string;
  level: number;
  xp: number;
  skill_rating: number;
  streak: number;
}

export interface LeaderboardResponse {
  leaderboard: LeaderboardEntry[];
  user_rank: number | null;
}

export interface DailyClaimResult {
  xp_earned: number;
  new_total_xp: number;
  leveled_up: boolean;
  new_level: number;
  streak: number;
  streak_message: string;
}
