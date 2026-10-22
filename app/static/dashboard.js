// Loads each dashboard widget from its own API endpoint and exposes
// data-state = loading | loaded | error on the widget element.

const API = "/api/v1/dashboard";

function setState(widget, state, message = "") {
  widget.dataset.state = state;
  const error = widget.querySelector('[data-testid="widget-error"]');
  error.hidden = state !== "error";
  error.textContent = message;
}

async function loadWidget(widget, url, render) {
  setState(widget, "loading");
  try {
    const response = await fetch(url, { credentials: "same-origin" });
    if (response.status === 401) {
      window.location.assign("/login?reason=expired");
      return;
    }
    const body = await response.json();
    if (!response.ok) {
      setState(widget, "error", body.error ? body.error.message : `HTTP ${response.status}`);
      return;
    }
    render(widget, body);
    setState(widget, "loaded");
  } catch (err) {
    setState(widget, "error", "Could not load this widget.");
  }
}

function cell(text, testId) {
  const td = document.createElement("td");
  td.textContent = text;
  if (testId) td.dataset.testid = testId;
  return td;
}

const renderers = {
  "total-test-cases": (widget, body) => {
    widget.querySelector('[data-testid="widget-value"]').textContent = String(body.value);
  },
  "pass-rate": (widget, body) => {
    widget.querySelector('[data-testid="widget-value"]').textContent = `${body.value.toFixed(1)}%`;
    widget.querySelector('[data-testid="widget-caption"]').textContent = body.run_name;
  },
  "recent-runs": (widget, body) => {
    const tbody = widget.querySelector("tbody");
    tbody.replaceChildren(
      ...body.items.map((run) => {
        const tr = document.createElement("tr");
        tr.dataset.testid = "run-row";
        tr.dataset.runId = String(run.id);
        tr.append(
          cell(run.name, "run-name"),
          cell(run.run_date, "run-date"),
          cell(String(run.passed), "run-passed"),
          cell(String(run.failed), "run-failed"),
          cell(`${run.pass_rate.toFixed(1)}%`, "run-pass-rate"),
          cell(run.status, "run-status"),
        );
        return tr;
      }),
    );
    widget.querySelector('[data-testid="runs-empty"]').hidden = body.items.length > 0;
  },
  "flaky-tests": (widget, body) => {
    widget.querySelector("tbody").replaceChildren(
      ...body.items.map((t) => {
        const tr = document.createElement("tr");
        tr.dataset.testid = "flaky-row";
        tr.append(cell(t.test_name, "flaky-name"), cell(String(t.flips), "flaky-flips"),
                  cell(t.last_seen, "flaky-last-seen"));
        return tr;
      }),
    );
  },
  "team-activity": (widget, body) => {
    widget.querySelector("ul").replaceChildren(
      ...body.items.map((a) => {
        const li = document.createElement("li");
        li.dataset.testid = "activity-item";
        li.textContent = `${a.user_email}: ${a.action}`;
        return li;
      }),
    );
  },
};

// --- Recent runs filters, kept in sync with the URL query string ---

const FILTERS = ["status", "date_from", "date_to", "sort", "order"];

function filterControls(widget) {
  return Object.fromEntries(FILTERS.map((name) => [name, widget.querySelector(`[name="${name}"]`)]));
}

function runsUrl(params) {
  const query = new URLSearchParams();
  for (const name of FILTERS) {
    if (params.get(name)) query.set(name, params.get(name));
  }
  const qs = query.toString();
  return qs ? `${API}/recent-runs?${qs}` : `${API}/recent-runs`;
}

function setupRecentRuns(widget) {
  const controls = filterControls(widget);
  const fromUrl = new URLSearchParams(window.location.search);
  for (const name of FILTERS) {
    if (fromUrl.get(name)) controls[name].value = fromUrl.get(name);
  }

  const reload = () => {
    const params = new URLSearchParams(window.location.search);
    for (const name of FILTERS) {
      const value = controls[name].value;
      // "desc" is the default order, so leave it out of the URL unless a sort is chosen.
      if (value && !(name === "order" && value === "desc" && !controls.sort.value)) {
        params.set(name, value);
      } else {
        params.delete(name);
      }
    }
    const qs = params.toString();
    history.replaceState(null, "", qs ? `?${qs}` : window.location.pathname);
    loadWidget(widget, runsUrl(params), renderers["recent-runs"]);
  };
  Object.values(controls).forEach((el) => el.addEventListener("change", reload));
  loadWidget(widget, runsUrl(fromUrl), renderers["recent-runs"]);
}

// --- Mobile menu ---

function setupMenu() {
  const toggle = document.querySelector('[data-testid="menu-toggle"]');
  const sidebar = document.getElementById("sidebar");
  toggle.addEventListener("click", () => {
    const open = sidebar.classList.toggle("open");
    toggle.setAttribute("aria-expanded", String(open));
  });
}

document.addEventListener("DOMContentLoaded", () => {
  setupMenu();
  for (const widget of document.querySelectorAll("[data-widget]")) {
    const name = widget.dataset.widget;
    if (name === "recent-runs") {
      setupRecentRuns(widget);
    } else {
      loadWidget(widget, `${API}/${name}`, renderers[name]);
    }
  }
});
