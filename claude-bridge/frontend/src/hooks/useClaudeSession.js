import { useCallback, useEffect, useRef, useState } from "react";
import { stopRun, streamChat } from "../lib/api.js";
import { loadState, saveState } from "../lib/storage.js";

// Owns the conversation: sends prompts to Claude Code through the backend and
// folds the streamed events into a list of messages.
//   user message:      { role: "user", text }
//   assistant message: { role: "assistant", segments: [{type:"text",text} | {type:"tool",...}], meta, error }
export function useClaudeSession() {
  const saved = useRef(loadState()).current;
  const [messages, setMessages] = useState(saved.messages || []);
  const [sessionId, setSessionId] = useState(saved.sessionId || null);
  const [model, setModel] = useState(saved.model || "");
  const [mockMode, setMockModeState] = useState(() => {
    try {
      const v = localStorage.getItem("adrosonic_mock_mode");
      return v === null ? true : v === "true";
    } catch {
      return true;
    }
  });
  const [busy, setBusy] = useState(null); // { runId, started, abort }
  const busyRef = useRef(null);
  busyRef.current = busy;

  const setMockMode = (val) => {
    setMockModeState(val);
    try {
      localStorage.setItem("adrosonic_mock_mode", String(val));
    } catch {}
  };

  useEffect(() => saveState({ messages, sessionId, model }), [messages, sessionId, model]);

  const updateLast = (fn) =>
    setMessages((ms) => {
      const copy = ms.slice();
      const last = copy[copy.length - 1];
      copy[copy.length - 1] = fn({ ...last, segments: last.segments.slice() });
      return copy;
    });

  const send = useCallback(async (prompt, { fresh = false } = {}) => {
    prompt = prompt.trim();
    if (!prompt || busyRef.current) return;
    const sid = fresh ? null : sessionId;
    const abort = new AbortController();
    setMessages((ms) => [...(fresh ? [] : ms), { role: "user", text: prompt }, { role: "assistant", segments: [] }]);
    if (fresh) setSessionId(null);
    setBusy({ runId: null, started: Date.now(), abort });

    const onEvent = (ev, d) => {
      switch (ev) {
        case "start":
          setBusy((b) => b && { ...b, runId: d.run_id });
          break;
        case "init":
          setSessionId(d.session_id);
          updateLast((m) => ({ ...m, meta: { ...m.meta, model: d.model } }));
          break;
        case "text_start":
          updateLast((m) => ({ ...m, segments: [...m.segments, { type: "text", text: "" }] }));
          break;
        case "text":
          updateLast((m) => {
            const last = m.segments[m.segments.length - 1];
            if (last?.type === "text") m.segments[m.segments.length - 1] = { ...last, text: last.text + d.text };
            else m.segments.push({ type: "text", text: d.text });
            return m;
          });
          break;
        case "tool":
          updateLast((m) => ({ ...m, segments: [...m.segments, { type: "tool", ...d, status: "running" }] }));
          break;
        case "tool_done":
          updateLast((m) => ({
            ...m,
            segments: m.segments.map((s) =>
              s.type === "tool" && s.id === d.id ? { ...s, status: d.is_error ? "error" : "ok", error: d.error } : s),
          }));
          break;
        case "done":
          setSessionId(d.session_id);
          updateLast((m) => ({
            ...m,
            segments: m.segments.some((s) => s.type === "text" && s.text.trim())
              ? m.segments
              : [...m.segments, { type: "text", text: d.result || "" }],
            error: d.is_error ? d.result : null,
            meta: { ...m.meta, duration_ms: d.duration_ms },
          }));
          break;
        case "error":
          updateLast((m) => ({ ...m, error: d.message }));
          break;
      }
    };

    try {
      await streamChat({ prompt, session_id: sid, model: model || null, demo_mode: mockMode }, onEvent, abort.signal);
    } catch (e) {
      updateLast((m) => ({ ...m, error: e.name === "AbortError" ? "Stopped." : String(e.message || e) }));
    } finally {
      setBusy(null);
    }
  }, [sessionId, model, mockMode]);

  const stop = useCallback(async () => {
    const b = busyRef.current;
    if (!b) return;
    if (b.runId) await stopRun(b.runId);
    b.abort.abort();
  }, []);

  const clear = useCallback(() => {
    if (busyRef.current) return;
    setMessages([]);
    setSessionId(null);
  }, []);

  return { messages, sessionId, model, setModel, busy, send, stop, clear, mockMode, setMockMode };
}

export const assistantText = (m) =>
  m.segments.filter((s) => s.type === "text").map((s) => s.text).join("\n\n");
