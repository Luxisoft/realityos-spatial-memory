import { FormEvent, useEffect, useMemo, useState } from "react";

import {
  request,
  type ObjectFact,
  type Observation,
  type TrackedObject,
  type Zone,
} from "./api";
import "./explorer.css";

export function Objects({ workspaceId, token }: { workspaceId: string; token: string }) {
  const [items, setItems] = useState<TrackedObject[]>([]);
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState("");
  const [zoneId, setZoneId] = useState("");
  const [zones, setZones] = useState<Zone[]>([]);
  const [selected, setSelected] = useState<TrackedObject | null>(null);
  const [history, setHistory] = useState<Observation[]>([]);
  const [facts, setFacts] = useState<ObjectFact[]>([]);
  const [notice, setNotice] = useState("");
  const categories = useMemo(
    () => [...new Set(items.map((item) => item.category).filter(Boolean))] as string[],
    [items]
  );

  async function load() {
    if (!workspaceId) return;
    const params = new URLSearchParams({ workspace_id: workspaceId });
    if (query.trim()) params.set("q", query.trim());
    if (category) params.set("category", category);
    if (zoneId) params.set("zone_id", zoneId);
    try {
      setItems(await request<TrackedObject[]>(`/v1/objects?${params}`, token));
      setNotice("");
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "Objects could not be loaded.");
    }
  }

  useEffect(() => {
    void load();
  }, [workspaceId, token]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!workspaceId) return;
    request<Zone[]>(`/v1/workspaces/${workspaceId}/zones`, token)
      .then(setZones)
      .catch((error: Error) => setNotice(error.message));
  }, [workspaceId, token]);

  useEffect(() => {
    if (!selected) {
      setHistory([]);
      setFacts([]);
      return;
    }
    request<Observation[]>(`/v1/objects/${selected.id}/history`, token)
      .then(setHistory)
      .catch((error: Error) => setNotice(error.message));
    request<ObjectFact[]>(`/v1/objects/${selected.id}/facts`, token)
      .then(setFacts)
      .catch(() => setFacts([]));
  }, [selected, token]);

  function submit(event: FormEvent) {
    event.preventDefault();
    void load();
  }

  return (
    <section className="panel catalog">
      <p className="eyebrow">CATALOG / RECORDED EVIDENCE</p>
      <h1>Observed objects</h1>
      <form className="catalog-controls" onSubmit={submit}>
        <input
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Name or alias"
          aria-label="Search objects"
        />
        <select value={category} onChange={(event) => setCategory(event.target.value)}>
          <option value="">All categories</option>
          {categories.map((value) => <option value={value} key={value}>{value}</option>)}
        </select>
        <select value={zoneId} onChange={(event) => setZoneId(event.target.value)}>
          <option value="">All locations</option>
          {zones.map((zone) => <option value={zone.id} key={zone.id}>{zone.name}</option>)}
        </select>
        <button className="primary">Filter</button>
      </form>
      {notice && <p className="error">{notice}</p>}
      <div className="catalog-grid">
        <div className="object-list">
          {items.length ? items.map((item) => (
            <button
              className={selected?.id === item.id ? "object-card active" : "object-card"}
              key={item.id}
              onClick={() => setSelected(item)}
              type="button"
            >
              <span>{item.category ?? "uncategorized"}</span>
              <strong>{item.canonical_name}</strong>
              <small>View verified observations</small>
            </button>
          )) : <p className="empty">No objects match. Register evidence or change the filter.</p>}
        </div>
        <aside className="history-card">
          {selected ? <>
            <p className="eyebrow">HISTORY / {selected.canonical_name}</p>
            <h2>Observations</h2>
            {facts.length > 0 && <dl className="fact-list">{facts.slice(0, 6).map((fact) => <div key={fact.id}><dt>{fact.fact_type.replaceAll("_", " ")}</dt><dd>{fact.value_text ?? fact.normalized_value ?? `${fact.numeric_value ?? "?"} ${fact.unit ?? ""}`} <small>{fact.verification_status} · {Math.round(fact.confidence * 100)}%</small></dd></div>)}</dl>}
            {history.length ? <ol>{history.map((item) => <li key={item.id}>
              <time>{new Date(item.seen_at).toLocaleString("en-US")}</time>
              <strong>{item.verification_status === "verified" ? "Verified" : item.verification_status}</strong>
              <span>{item.spatial_description ?? "No spatial detail"}</span>
            </li>)}</ol> : <p className="empty">There are no observations for this object yet.</p>}
          </> : <>
            <p className="eyebrow">HISTORY</p>
            <h2>Select an object</h2>
            <p className="empty">Evidence history appears here; it never starts capture.</p>
          </>}
        </aside>
      </div>
    </section>
  );
}

export function LocationMap({ workspaceId, token }: { workspaceId: string; token: string }) {
  const [zones, setZones] = useState<Zone[]>([]);
  const [notice, setNotice] = useState("");
  useEffect(() => {
    if (!workspaceId) return;
    request<Zone[]>(`/v1/workspaces/${workspaceId}/zones`, token)
      .then(setZones)
      .catch((error: Error) => setNotice(error.message));
  }, [workspaceId, token]);
  const byParent = useMemo(() => {
    const grouped = new Map<string, Zone[]>();
    zones.forEach((zone) => {
      const key = zone.parent_id ?? "root";
      grouped.set(key, [...(grouped.get(key) ?? []), zone]);
    });
    return grouped;
  }, [zones]);
  return (
    <section className="panel map-panel">
      <p className="eyebrow">LOCATION MAP / DECLARED HIERARCHY</p>
      <h1>Spaces, not coordinates</h1>
      <p className="lead">This view represents recorded zones, shelves and levels. It does not claim a metric 3D position.</p>
      {notice && <p className="error">{notice}</p>}
      {zones.length ? <div className="location-tree"><LocationBranch parentId="root" byParent={byParent} /></div> : <p className="empty">There are no locations yet. Create a zone when registering evidence.</p>}
    </section>
  );
}

function LocationBranch({ parentId, byParent }: { parentId: string; byParent: Map<string, Zone[]> }) {
  const children = byParent.get(parentId) ?? [];
  if (!children.length) return null;
  return <ul>{children.map((zone) => <li key={zone.id}>
    <div className="location-node"><span>{zone.kind}</span><strong>{zone.name}</strong></div>
    <LocationBranch parentId={zone.id} byParent={byParent} />
  </li>)}</ul>;
}
