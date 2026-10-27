import { FormEvent, useEffect, useMemo, useState } from "react";

import {
  request,
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
      setNotice(error instanceof Error ? error.message : "No se pudieron cargar los objetos.");
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
      return;
    }
    request<Observation[]>(`/v1/objects/${selected.id}/history`, token)
      .then(setHistory)
      .catch((error: Error) => setNotice(error.message));
  }, [selected, token]);

  function submit(event: FormEvent) {
    event.preventDefault();
    void load();
  }

  return (
    <section className="panel catalog">
      <p className="eyebrow">CATÁLOGO / EVIDENCIA REGISTRADA</p>
      <h1>Objetos observados</h1>
      <form className="catalog-controls" onSubmit={submit}>
        <input
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Nombre o alias"
          aria-label="Buscar objetos"
        />
        <select value={category} onChange={(event) => setCategory(event.target.value)}>
          <option value="">Todas las categorías</option>
          {categories.map((value) => <option value={value} key={value}>{value}</option>)}
        </select>
        <select value={zoneId} onChange={(event) => setZoneId(event.target.value)}>
          <option value="">Todas las ubicaciones</option>
          {zones.map((zone) => <option value={zone.id} key={zone.id}>{zone.name}</option>)}
        </select>
        <button className="primary">Filtrar</button>
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
              <span>{item.category ?? "sin categoría"}</span>
              <strong>{item.canonical_name}</strong>
              <small>Ver observaciones verificadas</small>
            </button>
          )) : <p className="empty">No hay objetos que coincidan. Registra una evidencia o cambia el filtro.</p>}
        </div>
        <aside className="history-card">
          {selected ? <>
            <p className="eyebrow">HISTORIAL / {selected.canonical_name}</p>
            <h2>Observaciones</h2>
            {history.length ? <ol>{history.map((item) => <li key={item.id}>
              <time>{new Date(item.seen_at).toLocaleString("es-CO")}</time>
              <strong>{item.verification_status === "verified" ? "Verificada" : item.verification_status}</strong>
              <span>{item.spatial_description ?? "Sin detalle espacial"}</span>
            </li>)}</ol> : <p className="empty">Aún no hay observaciones para este objeto.</p>}
          </> : <>
            <p className="eyebrow">HISTORIAL</p>
            <h2>Selecciona un objeto</h2>
            <p className="empty">Aquí aparece el historial de evidencia; no se inicia ninguna captura.</p>
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
      <p className="eyebrow">MAPA DE UBICACIONES / JERARQUÍA DECLARADA</p>
      <h1>Espacios, no coordenadas</h1>
      <p className="lead">Esta vista representa zonas, estanterías y niveles registrados. No afirma una posición métrica 3D.</p>
      {notice && <p className="error">{notice}</p>}
      {zones.length ? <div className="location-tree"><LocationBranch parentId="root" byParent={byParent} /></div> : <p className="empty">Aún no hay ubicaciones. Crea una zona al registrar evidencia.</p>}
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
