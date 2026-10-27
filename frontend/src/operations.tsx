import { FormEvent, useEffect, useState } from "react";

import {
  request,
  type Device,
  type DeviceAssignment,
  type DeviceEnrollment,
  type InventoryAnalytics,
} from "./api";
import "./operations.css";

type Context = { workspaceId: string; token: string };

function Tally({ label, rows }: { label: string; rows: { value: string; count: number }[] }) {
  return <section className="tally"><p>{label}</p>{rows.length ? <ol>{rows.map((row) => <li key={row.value}><span>{row.value}</span><strong>{row.count}</strong></li>)}</ol> : <em>No verified evidence yet.</em>}</section>;
}

export function InventoryIntelligence({ workspaceId, token }: Context) {
  const [report, setReport] = useState<InventoryAnalytics | null>(null);
  const [notice, setNotice] = useState("");
  useEffect(() => {
    if (!workspaceId) return;
    request<InventoryAnalytics>(`/v1/admin/analytics/inventory?workspace_id=${workspaceId}`, token)
      .then((value) => { setReport(value); setNotice(""); })
      .catch((error: Error) => setNotice(error.message));
  }, [workspaceId, token]);
  return <section className="panel intelligence">
    <p className="eyebrow">ADMIN / INVENTORY INTELLIGENCE</p>
    <h1>What the workspace holds</h1>
    <p className="lead">Counts separate confirmed inventory facts from provisional visual findings. A count of visible items is not an inventory promise.</p>
    {notice && <p className="error">{notice}</p>}
    {report && <>
      <div className="ledger-strip"><div><strong>{report.verified_object_count}</strong><span>objects with verified facts</span></div><div><strong>{report.provisional_fact_count}</strong><span>findings awaiting review</span></div><div><strong>{report.devices.length}</strong><span>registered devices</span></div></div>
      <div className="tally-grid"><Tally label="Verified brands" rows={report.brands} /><Tally label="Object categories" rows={report.categories} /><Tally label="Observed condition" rows={report.conditions} /><Tally label="Observed use" rows={report.usage_states} /></div>
      <section className="device-activity"><p className="eyebrow">CAPTURE ORIGIN</p><h2>Device activity</h2>{report.devices.length ? <table><thead><tr><th>Device</th><th>ID</th><th>Sessions</th></tr></thead><tbody>{report.devices.map((device) => <tr key={device.device_id}><td>{device.label}</td><td><code>{device.device_id}</code></td><td>{device.capture_sessions}</td></tr>)}</tbody></table> : <p className="empty">Enroll a device to attribute incoming evidence.</p>}</section>
    </>}
  </section>;
}

export function DeviceRegistry({ workspaceId, token }: Context) {
  const [devices, setDevices] = useState<Device[]>([]);
  const [deviceIdentifier, setDeviceIdentifier] = useState("");
  const [label, setLabel] = useState("");
  const [keyOnce, setKeyOnce] = useState<DeviceEnrollment | null>(null);
  const [selected, setSelected] = useState<Device | null>(null);
  const [assignments, setAssignments] = useState<DeviceAssignment[]>([]);
  const [operator, setOperator] = useState("");
  const [notice, setNotice] = useState("");

  async function load() {
    if (!workspaceId) return;
    try { setDevices(await request<Device[]>(`/v1/admin/devices?workspace_id=${workspaceId}`, token)); setNotice(""); }
    catch (error) { setNotice(error instanceof Error ? error.message : "Devices could not be loaded."); }
  }
  useEffect(() => { void load(); }, [workspaceId, token]); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => {
    if (!selected) { setAssignments([]); return; }
    request<DeviceAssignment[]>(`/v1/admin/devices/${selected.id}/assignments`, token).then(setAssignments).catch((error: Error) => setNotice(error.message));
  }, [selected, token]);

  async function enroll(event: FormEvent) {
    event.preventDefault(); if (!workspaceId) return;
    try {
      const result = await request<DeviceEnrollment>("/v1/admin/devices", token, { method: "POST", body: JSON.stringify({ workspace_id: workspaceId, device_identifier: deviceIdentifier, label }) });
      setKeyOnce(result); setDeviceIdentifier(""); setLabel(""); await load();
    } catch (error) { setNotice(error instanceof Error ? error.message : "Device could not be enrolled."); }
  }
  async function rotate(device: Device) {
    try { setKeyOnce(await request<DeviceEnrollment>(`/v1/admin/devices/${device.id}/rotate`, token, { method: "POST" })); await load(); }
    catch (error) { setNotice(error instanceof Error ? error.message : "Credential could not be rotated."); }
  }
  async function revoke(device: Device) {
    try { await request<Device>(`/v1/admin/devices/${device.id}/revoke`, token, { method: "POST" }); if (selected?.id === device.id) setSelected(null); await load(); }
    catch (error) { setNotice(error instanceof Error ? error.message : "Device could not be revoked."); }
  }
  async function assign(event: FormEvent) {
    event.preventDefault(); if (!selected || !operator.trim()) return;
    try {
      const entry = await request<DeviceAssignment>(`/v1/admin/devices/${selected.id}/assignments`, token, { method: "POST", body: JSON.stringify({ operator_label: operator, notice_version: "admin-notice-v1" }) });
      setAssignments((current) => [entry, ...current]); setOperator("");
    } catch (error) { setNotice(error instanceof Error ? error.message : "Assignment could not be saved."); }
  }
  return <section className="panel devices"><p className="eyebrow">ADMIN / DEVICE REGISTRY</p><h1>Trusted capture origins</h1><p className="lead">A device ID labels evidence. Its private key authorizes uploads and appears exactly once on enrollment or rotation.</p>
    <form className="device-enroll" onSubmit={enroll}><label>Device ID<input required value={deviceIdentifier} onChange={(event) => setDeviceIdentifier(event.target.value)} placeholder="electronics-cam-01" pattern="[A-Za-z0-9._:-]+" /></label><label>Label<input required value={label} onChange={(event) => setLabel(event.target.value)} placeholder="Electronics bench camera" /></label><button className="primary">Enroll device</button></form>
    {keyOnce && <aside className="key-once"><p className="eyebrow">COPY ONCE / DEVICE CREDENTIAL</p><strong>{keyOnce.label}</strong><code>{keyOnce.device_key}</code><small>Store this on the device now. It cannot be retrieved later; rotate it if lost.</small><button onClick={() => setKeyOnce(null)}>I stored the key</button></aside>}
    {notice && <p className="error">{notice}</p>}
    <div className="device-grid"><div className="device-list">{devices.map((device) => <article className={selected?.id === device.id ? "device-card active" : "device-card"} key={device.id}><button onClick={() => setSelected(device)}><span>{device.status}</span><strong>{device.label}</strong><code>{device.device_identifier}</code></button><div>{device.status === "active" && <button onClick={() => void rotate(device)}>Rotate key</button>} {device.status === "active" && <button className="danger" onClick={() => void revoke(device)}>Revoke</button>}</div></article>)}{!devices.length && <p className="empty">No devices are enrolled in this workspace.</p>}</div>
      <aside className="assignment-panel">{selected ? <><p className="eyebrow">ASSIGNMENT HISTORY</p><h2>{selected.label}</h2><form onSubmit={assign}><label>Operator label<input value={operator} onChange={(event) => setOperator(event.target.value)} placeholder="Bench A" required /></label><button className="primary">Assign device</button></form><ol>{assignments.map((entry) => <li key={entry.id}><strong>{entry.operator_label}</strong><span>{new Date(entry.effective_from).toLocaleString()}</span><small>{entry.effective_to ? "ended" : "current"} · {entry.notice_version}</small></li>)}</ol></> : <><p className="eyebrow">ASSIGNMENT HISTORY</p><h2>Select a device</h2><p className="empty">Assignments are administrator-declared labels, never biometric identity.</p></>}</aside>
    </div>
  </section>;
}
