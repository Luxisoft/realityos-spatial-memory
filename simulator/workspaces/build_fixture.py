"""Build synthetic manifests and clearly-labelled MP4 fixtures, never write a database."""

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
GROUPS = [
    (
        "security",
        "Pacific Ridge Police Department",
        ["alex-rivera", "maya-johnson", "daniel-kim"],
        "evidence-desk",
    ),
    (
        "hospital",
        "California Valley Medical Center",
        ["elena-marquez", "mateo-rios", "sarah-chen"],
        "medicine-cart",
    ),
    (
        "memory",
        "Sonoran Neurological Institute",
        ["noah-brooks", "lucia-vega", "owen-patel"],
        "memory-desk",
    ),
]
PATIENTS = {
    "hospital": [
        ("ana", "Ana Solis"),
        ("robert", "Robert Lane"),
        ("fatima", "Fatima Nasser"),
    ],
    "memory": [
        ("luis", "Luis Moreno"),
        ("grace", "Grace Wilson"),
        ("hiro", "Hiro Tanaka"),
    ],
}


def entry(external_id, kind, title, data, related=(), hour=9, biometric=False):
    row = {
        "external_id": external_id,
        "kind": kind,
        "title": title,
        "data": data,
        "related_ids": list(related),
        "version": 1,
        "status": "active",
        "authorized": True,
        "simulated": True,
        "occurred_at": f"2026-11-02T{hour:02}:00:00-05:00",
    }
    if biometric:
        row["biometric_authorized"] = True
        row["biometric_basis"] = "jury-test-consent"
    return row


def main():
    for slug, name, workers, scene in GROUPS:
        records = []
        attachments = []
        for i in range(3):
            case = f"{slug}-case-{i + 1}"
            records.append(
                entry(
                    case,
                    "case",
                    f"{name} — Caso de prueba {i + 1}",
                    {
                        "description": "Expediente ficticio para evaluación del software.",
                        "reference": case,
                        "status": "open",
                    },
                )
            )
            event = f"{slug}-event-{i + 1}"
            records.append(
                entry(
                    event,
                    "event",
                    f"Observación de turno {i + 1}",
                    {
                        "note": {
                            "security": "Linterna amarilla y destornillador rojo vistos en mesa de evidencias.",
                            "hospital": "Carro de preparación revisado; envase de prueba y hoja de verificación.",
                            "memory": "Documentos rojos y llaves vistos sobre el escritorio.",
                        }[slug],
                        "last_seen_location": scene,
                    },
                    [case],
                    hour=9 + i,
                )
            )
            records.append(
                entry(
                    f"{slug}-object-{i + 1}",
                    "object",
                    {
                        "security": [
                            "Linterna amarilla",
                            "Destornillador rojo",
                            "Carpeta negra",
                        ],
                        "hospital": [
                            "Carro de medicación",
                            "Bolígrafo azul",
                            "Guantes desechables",
                        ],
                        "memory": [
                            "Carpeta roja de documentos",
                            "Llaves de latón",
                            "Cuaderno azul",
                        ],
                    }[slug][i],
                    {"last_seen_location": scene},
                    [event],
                    hour=9 + i,
                )
            )
            attachments.append(
                {
                    "record": event,
                    "path": f"assets/{scene}.png",
                    "external_id": f"photo-{i + 1}",
                    "publish": True,
                    "author": workers[i],
                }
            )
        for view in (2, 3):
            attachments.append(
                {
                    "record": f"{slug}-event-{view}",
                    "path": f"assets/{scene}-view-{view}.png",
                    "external_id": f"photo-view-{view}",
                    "publish": True,
                    "author": workers[view - 1],
                }
            )
        for i, (key, person_name) in enumerate(PATIENTS.get(slug, [])):
            person = f"{slug}-person-{i + 1}"
            records.append(
                entry(
                    person,
                    "person",
                    person_name,
                    {
                        "identifier": f"TEST-{slug.upper()}-{i + 1:03}",
                        "birth_date": f"{1960 + i * 9}-03-14",
                        "description": "Persona ficticia, no cuenta de acceso.",
                        "allergies_reviewed_at": "2026-11-02T08:00:00-05:00",
                    },
                    [f"{slug}-case-{i + 1}"],
                    biometric=True,
                )
            )
            attachments.append(
                {
                    "record": person,
                    "path": f"assets/patient-{key}.png",
                    "external_id": "portrait",
                    "publish": False,
                    "author": workers[i],
                }
            )
            records.append(
                entry(
                    f"{slug}-encounter-{i + 1}",
                    "encounter",
                    f"Atención de {person_name}",
                    {
                        "note": "Sesión de prueba de revisión contextual y seguimiento, sin decisiones clínicas reales."
                    },
                    [person, f"{slug}-case-{i + 1}"],
                )
            )
            if slug == "hospital":
                rx = f"{slug}-rx-{i + 1}"
                records.append(
                    entry(
                        rx,
                        "prescription",
                        f"Prescripción ficticia {i + 1}",
                        {
                            "ingredient": "DEMO MEDICINE",
                            "concentration": "10 mg",
                            "state": "active",
                            "valid_from": "2026-11-01T00:00:00Z",
                            "valid_until": "2026-11-30T23:59:59Z",
                            "warning": "NO ES UNA PRESCRIPCIÓN REAL",
                        },
                        [person],
                    )
                )
                if i == 1:
                    records.append(
                        entry(
                            "hospital-allergy-2",
                            "allergy",
                            "Alerta ficticia de alergia",
                            {"substance": "DEMO MEDICINE"},
                            [person],
                        )
                    )
                if i == 2:
                    records.append(
                        entry(
                            "hospital-admin-3",
                            "administration",
                            "Administración ficticia previamente registrada",
                            {"ingredient": "DEMO MEDICINE", "concentration": "10 mg"},
                            [person, rx],
                            hour=10,
                        )
                    )
            else:
                records.append(
                    entry(
                        f"memory-recall-{i + 1}",
                        "event",
                        f"Recordatorio de {person_name}",
                        {
                            "note": "Última observación: documentos sobre el escritorio. No hay evidencia de movimientos posteriores."
                        },
                        [person, "memory-object-1"],
                        hour=11 + i,
                    )
                )
        for i in range(2):
            video = ROOT / f"assets/{scene}-{i + 1}.mp4"
            if not video.exists():
                subprocess.run(
                    [
                        "ffmpeg",
                        "-hide_banner",
                        "-loglevel",
                        "error",
                        "-loop",
                        "1",
                        "-i",
                        str(ROOT / f"assets/{scene}.png"),
                        "-vf",
                        "scale=960:-2,drawtext=text='SIMULATED - STILL SCENE':fontcolor=white:fontsize=24:box=1:boxcolor=black@0.7:x=15:y=15",
                        "-t",
                        "5",
                        "-r",
                        "12",
                        "-c:v",
                        "libx264",
                        "-preset",
                        "fast",
                        "-pix_fmt",
                        "yuv420p",
                        "-movflags",
                        "+faststart",
                        str(video),
                    ],
                    check=True,
                )
            attachments.append(
                {
                    "record": f"{slug}-event-{i + 1}",
                    "path": f"assets/{video.name}",
                    "external_id": f"video-{i + 1}",
                    "publish": True,
                    "author": workers[i],
                }
            )
        manifest = {
            "workspace_name": name,
            "workers": workers,
            "batch": {"request_key": f"jury-{slug}-v1", "records": records},
            "attachments": attachments,
        }
        (ROOT / f"{slug}.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
        )
        print(slug, len(records), len(attachments))


if __name__ == "__main__":
    main()
