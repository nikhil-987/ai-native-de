import { useCallback, useEffect, useState } from "react";

const KEY = "aide.theme";

function initialTheme() {
  try {
    const saved = localStorage.getItem(KEY);
    if (saved === "light" || saved === "dark") return saved;
  } catch { /* storage unavailable */ }
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

// Light / dark mode: sets data-theme on <html>, which switches the CSS colour tokens.
export function useTheme() {
  const [theme, setTheme] = useState(initialTheme);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    try { localStorage.setItem(KEY, theme); } catch { /* storage unavailable */ }
  }, [theme]);

  const toggleTheme = useCallback(() => setTheme((t) => (t === "dark" ? "light" : "dark")), []);
  return { theme, toggleTheme };
}
