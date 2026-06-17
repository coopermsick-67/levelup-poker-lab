import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { register, login } from "../api/auth";

type Mode = "welcome" | "register" | "login";

export default function Onboarding() {
  const [mode, setMode] = useState<Mode>("welcome");
  const [displayName, setDisplayName] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleRegister = async () => {
    if (!displayName.trim() || !username.trim() || !password.trim()) {
      setError("Please fill in all fields");
      return;
    }
    if (password.length < 4) {
      setError("Password must be at least 4 characters");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const result = await register(displayName.trim(), username.trim(), password);
      localStorage.setItem("access_token", result.access_token);
      localStorage.setItem("user", JSON.stringify(result.user));
      navigate("/play");
    } catch (err: any) {
      setError(err.message || "Registration failed. Try a different username.");
    } finally {
      setLoading(false);
    }
  };

  const handleLogin = async () => {
    if (!username.trim() || !password.trim()) {
      setError("Please enter username and password");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const result = await login(username.trim(), password);
      localStorage.setItem("access_token", result.access_token);
      localStorage.setItem("user", JSON.stringify(result.user));
      navigate("/play");
    } catch (err: any) {
      setError(err.message || "Login failed. Check your credentials.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen gap-6 p-4">
      <h1 className="text-4xl font-bold text-gold">🃏 LevelUp Poker Lab</h1>
      <p className="text-gray-400 text-center max-w-md">
        Practice poker, train with drills, and get AI-style coaching. No real
        money — just skill building.
      </p>

      {mode === "welcome" && (
        <div className="flex flex-col gap-3 w-64">
          <button
            onClick={() => setMode("register")}
            className="bg-gold text-gray-900 font-bold px-8 py-3 rounded-lg hover:bg-gold-dark transition-colors text-lg"
          >
            Create Account
          </button>
          <button
            onClick={() => setMode("login")}
            className="bg-felt text-white font-medium px-8 py-3 rounded-lg hover:bg-felt-dark transition-colors"
          >
            Sign In
          </button>
        </div>
      )}

      {mode === "register" && (
        <div className="flex flex-col gap-3 w-72">
          <h2 className="text-xl font-bold text-white text-center">
            Create Account
          </h2>
          <input
            className="bg-gray-800 border border-gray-600 rounded-lg px-4 py-2 text-white text-center placeholder-gray-500"
            placeholder="Display name"
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
            maxLength={50}
          />
          <input
            className="bg-gray-800 border border-gray-600 rounded-lg px-4 py-2 text-white text-center placeholder-gray-500"
            placeholder="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value.toLowerCase().replace(/[^a-z0-9_]/g, ""))}
            maxLength={50}
            autoComplete="username"
          />
          <input
            className="bg-gray-800 border border-gray-600 rounded-lg px-4 py-2 text-white text-center placeholder-gray-500"
            placeholder="Password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleRegister()}
            autoComplete="new-password"
          />
          <button
            onClick={handleRegister}
            disabled={loading}
            className="bg-gold text-gray-900 font-bold px-8 py-2 rounded-lg hover:bg-gold-dark disabled:opacity-50 transition-colors"
          >
            {loading ? "Creating..." : "Create Account"}
          </button>
          <button
            onClick={() => {
              setMode("welcome");
              setError(null);
            }}
            className="text-sm text-gray-500 hover:text-gray-300"
          >
            Back
          </button>
        </div>
      )}

      {mode === "login" && (
        <div className="flex flex-col gap-3 w-72">
          <h2 className="text-xl font-bold text-white text-center">Sign In</h2>
          <input
            className="bg-gray-800 border border-gray-600 rounded-lg px-4 py-2 text-white text-center placeholder-gray-500"
            placeholder="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleLogin()}
            autoComplete="username"
          />
          <input
            className="bg-gray-800 border border-gray-600 rounded-lg px-4 py-2 text-white text-center placeholder-gray-500"
            placeholder="Password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleLogin()}
            autoComplete="current-password"
          />
          <button
            onClick={handleLogin}
            disabled={loading}
            className="bg-gold text-gray-900 font-bold px-8 py-2 rounded-lg hover:bg-gold-dark disabled:opacity-50 transition-colors"
          >
            {loading ? "Signing in..." : "Sign In"}
          </button>
          <button
            onClick={() => {
              setMode("welcome");
              setError(null);
            }}
            className="text-sm text-gray-500 hover:text-gray-300"
          >
            Back
          </button>
        </div>
      )}

      {error && (
        <div className="bg-red-900/30 border border-red-700 rounded-lg px-4 py-2 text-sm text-red-300 max-w-xs text-center">
          {error}
        </div>
      )}
    </div>
  );
}
