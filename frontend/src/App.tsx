import { useCallback, useEffect, useState } from "react";
import {
  apiBase,
  fetchEngines,
  fetchHealth,
  summarizeFile,
  summarizeText,
  summarizeUrl,
} from "./api";

type InputSource = "text" | "file" | "url";

export default function App() {
  const [engineOptions, setEngineOptions] = useState<string[]>(["tfidf", "textrank", "phobert-extractive"]);
  const [plannedEngines, setPlannedEngines] = useState<string[]>([]);
  const [engineWarning, setEngineWarning] = useState<string | null>(null);
  const [healthMsg, setHealthMsg] = useState<{ tone: "ok" | "err"; text: string } | null>(null);

  const [inputSource, setInputSource] = useState<InputSource>("text");
  const [inputText, setInputText] = useState("");
  const [urlInput, setUrlInput] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [maxSentences, setMaxSentences] = useState(3);
  const [engine, setEngine] = useState("tfidf");

  const [summary, setSummary] = useState<string | null>(null);
  const [metadata, setMetadata] = useState<Record<string, unknown> | null>(null);
  const [busy, setBusy] = useState(false);
  const [summarizeErr, setSummarizeErr] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    void (async () => {
      const { engines, planned, warning, defaultEngine } = await fetchEngines();
      if (cancelled) return;
      setEngineOptions(engines);
      setPlannedEngines(planned);
      setEngineWarning(warning);
      // Always align initial engine with backend default_engine (e.g. SUMMARY_ENGINE), not a hardcoded default.
      const resolved =
        defaultEngine && engines.includes(defaultEngine) ? defaultEngine : (engines[0] ?? "tfidf");
      setEngine(resolved);
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const onHealth = useCallback(async () => {
    setHealthMsg(null);
    const res = await fetchHealth();
    if (res.ok) {
      setHealthMsg({ tone: "ok", text: `API: ${res.status}` });
    } else {
      setHealthMsg({ tone: "err", text: res.message });
    }
  }, []);

  const onSummarize = useCallback(async () => {
    setSummarizeErr(null);
    setSummary(null);
    setMetadata(null);
    setBusy(true);
    try {
      let result;
      if (inputSource === "text") {
        if (!inputText.trim()) {
          setSummarizeErr("Please enter some text.");
          return;
        }
        result = await summarizeText({
          text: inputText,
          max_sentences: maxSentences,
          engine,
        });
      } else if (inputSource === "file") {
        if (!selectedFile) {
          setSummarizeErr("Please choose a file (.txt, .docx, .pdf).");
          return;
        }
        result = await summarizeFile(selectedFile, {
          max_sentences: maxSentences,
          engine,
        });
      } else {
        const url = urlInput.trim();
        if (!url) {
          setSummarizeErr("Please enter a URL.");
          return;
        }
        result = await summarizeUrl(url, {
          max_sentences: maxSentences,
          engine,
        });
      }

      if ("error" in result) {
        setSummarizeErr(result.error);
      } else {
        setSummary(result.summary);
        setMetadata(result.metadata ?? {});
      }
    } finally {
      setBusy(false);
    }
  }, [engine, inputSource, inputText, maxSentences, selectedFile, urlInput]);

  return (
    <div className="shell">
      <aside className="sidebar">
        <h2 className="sidebar-title">Backend Status</h2>
        <p className="muted small">
          API: <code className="inline-code">{apiBase()}</code>
        </p>
        {engineWarning ? <div className="banner warn">{engineWarning}</div> : null}
        <button type="button" className="btn secondary" onClick={() => void onHealth()}>
          Check Health
        </button>
        {healthMsg ? (
          <div className={healthMsg.tone === "ok" ? "banner ok" : "banner err"}>{healthMsg.text}</div>
        ) : null}
        {plannedEngines.length > 0 ? (
          <div className="planned">
            <div className="muted small sidebar-sub">Planned engines</div>
            <ul className="planned-list">
              {plannedEngines.map((e) => (
                <li key={e}>{e}</li>
              ))}
            </ul>
          </div>
        ) : null}
      </aside>

      <main className="main">
        <header className="hero">
          <h1>Vietnamese Text Summarization</h1>
          <p className="caption muted">Skeleton UI — Phase 1 (text, file, URL)</p>
        </header>

        <div className="field-label">Input source</div>
        <div className="source-tabs" role="tablist" aria-label="Input source">
          {(
            [
              ["text", "Plain text"],
              ["file", "File"],
              ["url", "URL"],
            ] as const
          ).map(([key, label]) => (
            <button
              key={key}
              type="button"
              role="tab"
              aria-selected={inputSource === key}
              className={`source-tab ${inputSource === key ? "active" : ""}`}
              onClick={() => {
                setInputSource(key);
                setSummarizeErr(null);
              }}
            >
              {label}
            </button>
          ))}
        </div>

        {inputSource === "text" ? (
          <>
            <label className="field-label" htmlFor="input-text">
              Input text
            </label>
            <textarea
              id="input-text"
              className="textarea"
              rows={10}
              placeholder="Paste Vietnamese text here..."
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
            />
          </>
        ) : null}

        {inputSource === "file" ? (
          <>
            <label className="field-label" htmlFor="file-input">
              Upload (.txt, .docx, .pdf)
            </label>
            <input
              id="file-input"
              type="file"
              className="file-input"
              accept=".txt,.docx,.pdf,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,text/plain"
              onChange={(e) => setSelectedFile(e.target.files?.[0] ?? null)}
            />
            {selectedFile ? (
              <p className="muted small file-hint">
                Selected: <strong>{selectedFile.name}</strong> ({Math.round(selectedFile.size / 1024)} KB)
              </p>
            ) : (
              <p className="muted small file-hint">No file selected.</p>
            )}
          </>
        ) : null}

        {inputSource === "url" ? (
          <>
            <label className="field-label" htmlFor="url-input">
              Page URL
            </label>
            <input
              id="url-input"
              type="url"
              className="text-input"
              placeholder="https://example.com/article"
              value={urlInput}
              onChange={(e) => setUrlInput(e.target.value)}
              autoComplete="off"
            />
            <p className="help muted small">Backend fetches the URL and extracts readable text (see API limits).</p>
          </>
        ) : null}

        <div className="row">
          <label className="field-label flex-grow" htmlFor="max-sent">
            Max summary sentences: <strong>{maxSentences}</strong>
          </label>
        </div>
        <input
          id="max-sent"
          type="range"
          min={1}
          max={10}
          value={maxSentences}
          onChange={(e) => setMaxSentences(Number(e.target.value))}
          className="slider"
        />

        <label className="field-label" htmlFor="engine">
          Engine
        </label>
        <select id="engine" className="select" value={engine} onChange={(e) => setEngine(e.target.value)}>
          {engineOptions.map((opt) => (
            <option key={opt} value={opt}>
              {opt}
            </option>
          ))}
        </select>
        <p className="help muted small">Engine list and default are discovered from the backend capability endpoint.</p>

        <button type="button" className="btn primary" disabled={busy} onClick={() => void onSummarize()}>
          {busy ? "Summarizing…" : "Summarize"}
        </button>

        {summarizeErr ? <div className="banner err">{summarizeErr}</div> : null}

        {summary !== null ? (
          <section className="results">
            <h2>Summary</h2>
            <div className="summary-box">{summary || <span className="muted">(empty)</span>}</div>
            <h2>Metadata</h2>
            <pre className="meta-json">{JSON.stringify(metadata ?? {}, null, 2)}</pre>
          </section>
        ) : null}
      </main>
    </div>
  );
}
