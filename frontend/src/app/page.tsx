"use client";

import { FormEvent, useState } from "react";
import { KanbanBoard } from "@/components/KanbanBoard";

const VALID_USERNAME = "user";
const VALID_PASSWORD = "password";

/**
 * Returns true when the submitted credentials match the MVP login pair.
 */
const isValidCredentials = (username: string, password: string) =>
  username === VALID_USERNAME && password === VALID_PASSWORD;

export default function Home() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (!isValidCredentials(username, password)) {
      setError("Use user / password.");
      setIsAuthenticated(false);
      return;
    }

    setError("");
    setIsAuthenticated(true);
  };

  const handleLogout = () => {
    setIsAuthenticated(false);
    setPassword("");
    setError("");
  };

  if (isAuthenticated) {
    return <KanbanBoard onLogout={handleLogout} />;
  }

  return (
    <main className="flex min-h-screen items-center justify-center px-6 py-10">
      <form
        onSubmit={handleSubmit}
        className="w-full max-w-md rounded-[32px] border border-[var(--stroke)] bg-white/90 p-8 shadow-[var(--shadow)] backdrop-blur"
      >
        <p className="text-xs font-semibold uppercase tracking-[0.35em] text-(--gray-text)">
          Sign In
        </p>
        <h1 className="mt-3 font-display text-4xl font-semibold text-foreground">
          Kanban Studio
        </h1>
        <p className="mt-3 text-sm leading-6 text-(--gray-text)">
          Use the MVP credentials to access your board.
        </p>
        <label className="mt-8 block text-sm font-semibold text-foreground">
          Username
          <input
            value={username}
            onChange={(event) => setUsername(event.target.value)}
            className="mt-2 w-full rounded-2xl border border-[var(--stroke)] px-4 py-3 outline-none transition focus:border-[var(--primary-blue)]"
          />
        </label>
        <label className="mt-4 block text-sm font-semibold text-[var(--navy-dark)]">
          Password
          <input
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            className="mt-2 w-full rounded-2xl border border-[var(--stroke)] px-4 py-3 outline-none transition focus:border-[var(--primary-blue)]"
          />
        </label>
        {error ? (
          <p className="mt-4 text-sm text-[var(--purple-secondary)]">{error}</p>
        ) : null}
        <button
          type="submit"
          className="mt-6 w-full rounded-2xl bg-(--purple-secondary) px-4 py-3 text-sm font-semibold text-black transition hover:opacity-90"
        >
          Sign in
        </button>
      </form>
    </main>
  );
}
