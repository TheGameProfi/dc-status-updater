const { useEffect, useMemo, useState } = React

async function api(path, method = "GET", body = null) {
  const response = await fetch(path, {
    method,
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  })
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}))
    throw new Error(payload.detail || "Request failed")
  }
  return response.json()
}

function parseDurationToSeconds(value) {
  const normalized = value.trim().toLowerCase().replace(/\s+/g, "")
  if (!normalized) {
    throw new Error("Static duration is required (example: 30m, 1h30m, or 1d).")
  }

  if (/^\d+$/.test(normalized)) {
    const minutesOnly = Number(normalized)
    if (minutesOnly <= 0) {
      throw new Error("Duration must be greater than zero.")
    }
    return minutesOnly * 60
  }

  const match = normalized.match(/^(?:(\d+)d)?(?:(\d+)h)?(?:(\d+)m)?$/)
  if (!match) {
    throw new Error("Use duration like 30m, 1h, 1h30m, or 1d.")
  }

  const days = Number(match[1] || 0)
  const hours = Number(match[2] || 0)
  const minutes = Number(match[3] || 0)
  if (days === 0 && hours === 0 && minutes === 0) {
    throw new Error("Duration must be greater than zero.")
  }
  return ((days * 24 + hours) * 60 + minutes) * 60
}

function formatSecondsToDuration(value) {
  const totalSeconds = Number(value)
  if (!Number.isFinite(totalSeconds) || totalSeconds <= 0) {
    return "1h"
  }
  if (totalSeconds % 86400 === 0) {
    return `${totalSeconds / 86400}d`
  }
  if (totalSeconds % 3600 === 0) {
    return `${totalSeconds / 3600}h`
  }
  return `${Math.max(1, Math.round(totalSeconds / 60))}m`
}

function App() {
  const [lists, setLists] = useState([])
  const [activeList, setActiveList] = useState("")
  const [quotes, setQuotes] = useState([])
  const [runtime, setRuntime] = useState(null)
  const [newListName, setNewListName] = useState("")
  const [newQuote, setNewQuote] = useState("")
  const [staticText, setStaticText] = useState("")
  const [staticDuration, setStaticDuration] = useState("1h")
  const [status, setStatus] = useState("")
  const [intervalInput, setIntervalInput] = useState("1h")

  async function refreshLists() {
    const payload = await api("/api/lists")
    setLists(payload.lists)
  }

  async function refreshRuntime() {
    const payload = await api("/api/runtime")
    setRuntime(payload)
    setActiveList(payload.active_list)
    setIntervalInput(formatSecondsToDuration(payload.interval_seconds))
  }

  async function refreshQuotes(listName) {
    const payload = await api(`/api/lists/${encodeURIComponent(listName)}/quotes`)
    setQuotes(payload.quotes)
  }

  async function initialize() {
    await refreshLists()
    await refreshRuntime()
  }

  useEffect(() => {
    initialize().catch((error) => setStatus(error.message))
  }, [])

  useEffect(() => {
    if (activeList) {
      refreshQuotes(activeList).catch((error) => setStatus(error.message))
    }
  }, [activeList])

  const listNames = useMemo(() => lists.map((entry) => entry.name), [lists])

  async function withStatus(fn) {
    try {
      await fn()
      setStatus("Saved")
      await refreshLists()
      await refreshRuntime()
      if (activeList) {
        await refreshQuotes(activeList)
      }
    } catch (error) {
      setStatus(error.message)
    }
  }

  return (
    <div className="container">
      <h1>Discord Status Updater</h1>
      <p className="status">{status || "Ready"}</p>
      <div className="grid">
        <div className="card">
          <h2>Runtime</h2>
          <div>Current mode: <b>{runtime?.mode || "-"}</b></div>
          <div>Last text: <b>{runtime?.last_applied_text || "-"}</b></div>
          <div className="row">
            <button onClick={() => withStatus(() => api("/api/runtime/auto", "POST"))}>Activate Auto</button>
            <button onClick={() => withStatus(() => api("/api/runtime/pause", "POST"))}>Pause</button>
          </div>
          <label>Interval (30m, 1h, 1d)</label>
          <input
            type="text"
            value={intervalInput}
            onChange={(event) => setIntervalInput(event.target.value)}
            placeholder="1h"
          />
          <button
            onClick={() =>
              withStatus(() =>
                {
                  const intervalSeconds = parseDurationToSeconds(intervalInput)
                  return api("/api/runtime", "PUT", {
                    interval_seconds: intervalSeconds,
                    active_list: activeList,
                  })
                }
              )
            }
          >
            Save Runtime Settings
          </button>
          <label>Static custom text</label>
          <input value={staticText} onChange={(event) => setStaticText(event.target.value)} placeholder="Type status text" />
          <label>Static duration (30m, 1h, 1h30m, 1d)</label>
          <input
            type="text"
            value={staticDuration}
            onChange={(event) => setStaticDuration(event.target.value)}
            placeholder="1h30m"
          />
          <button
            onClick={() =>
              withStatus(() =>
                {
                  const durationSeconds = parseDurationToSeconds(staticDuration)
                  return api("/api/runtime/static/custom", "POST", {
                    text: staticText,
                    duration_seconds: durationSeconds,
                  })
                }
              )
            }
          >
            Set Static Custom
          </button>
          <button
            onClick={() =>
              withStatus(() =>
                {
                  const durationSeconds = parseDurationToSeconds(staticDuration)
                  return api("/api/runtime/static/list", "POST", {
                    list_name: activeList,
                    duration_seconds: durationSeconds,
                  })
                }
              )
            }
          >
            Set Static From Active List
          </button>
        </div>

        <div className="card">
          <h2>Lists</h2>
          <label>Active list</label>
          <select
            value={activeList}
            onChange={(event) => setActiveList(event.target.value)}
          >
            {listNames.map((name) => (
              <option key={name} value={name}>{name}</option>
            ))}
          </select>
          <div className="row">
            <input
              value={newListName}
              onChange={(event) => setNewListName(event.target.value)}
              placeholder="new list name"
            />
            <button
              onClick={() =>
                withStatus(async () => {
                  await api("/api/lists", "POST", { name: newListName })
                  setNewListName("")
                })
              }
            >
              Add List
            </button>
          </div>
          <button
            onClick={() =>
              withStatus(() => api(`/api/lists/${encodeURIComponent(activeList)}`, "DELETE"))
            }
          >
            Delete Active List
          </button>
        </div>
      </div>

      <div className="card" style={{ marginTop: "16px" }}>
        <h2>Quotes ({activeList || "-"})</h2>
        <div className="row">
          <input
            value={newQuote}
            onChange={(event) => setNewQuote(event.target.value)}
            placeholder="new quote text"
          />
          <button
            onClick={() =>
              withStatus(async () => {
                await api(`/api/lists/${encodeURIComponent(activeList)}/quotes`, "POST", { text: newQuote })
                setNewQuote("")
              })
            }
          >
            Add Quote
          </button>
        </div>
        <div className="quotes">
          {quotes.map((quote) => (
            <div className="quote-row" key={quote.index}>
              <div className="quote-text">{quote.text}</div>
              <div className="quote-actions">
                <button
                  className="small-button"
                  onClick={() =>
                    withStatus(() => api(`/api/lists/${encodeURIComponent(activeList)}/quotes/${quote.index}`, "DELETE"))
                  }
                >
                  Remove
                </button>
                <button
                  className="small-button"
                  onClick={() =>
                    withStatus(() =>
                      {
                        const durationSeconds = parseDurationToSeconds(staticDuration)
                        return api("/api/runtime/static/list", "POST", {
                          list_name: activeList,
                          quote_index: quote.index,
                          duration_seconds: durationSeconds,
                        })
                      }
                    )
                  }
                >
                  Use Static
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

ReactDOM.createRoot(document.getElementById("root")).render(<App />)
