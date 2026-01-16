from __future__ import annotations

from datetime import date, timedelta
from calendar import monthrange
from collections import defaultdict

# =================================================
# Helpers
# =================================================
def _to_iso(d):
    return d.isoformat() if hasattr(d, "isoformat") else d


# =================================================
# DISPONIBILIDAD
# =================================================
def chofer_en_franco(conn, chofer_id: int, fecha: date) -> bool:
    cur = conn.cursor()
    cur.execute(
        """
        SELECT 1
        FROM eventos
        WHERE tipo = 'FRANCO'
          AND recurso_tipo = 'CHOFER'
          AND recurso_id = ?
          AND date(?) BETWEEN date(fecha_inicio) AND date(fecha_fin)
        LIMIT 1
        """,
        (chofer_id, _to_iso(fecha)),
    )
    return cur.fetchone() is not None


def tractor_en_taller(conn, tractor_id: int, fecha: date) -> bool:
    cur = conn.cursor()
    cur.execute(
        """
        SELECT 1
        FROM eventos
        WHERE tipo IN ('MANTENIMIENTO', 'TALLER', 'MANTENIMIENTO_CORRECTIVO')
          AND recurso_tipo = 'TRACTOR'
          AND recurso_id = ?
          AND date(?) BETWEEN date(fecha_inicio) AND date(fecha_fin)
        LIMIT 1
        """,
        (tractor_id, _to_iso(fecha)),
    )
    return cur.fetchone() is not None


# =================================================
# FRANCOS
# =================================================
def iniciar_franco(
    conn,
    chofer_id: int,
    fecha_inicio: date,
    fecha_fin: date,
    usuario: str,
    observacion: str | None = None,
):
    cur = conn.cursor()

    # 1️⃣ Crear evento FRANCO del chofer
    cur.execute(
        """
        INSERT INTO eventos (
            tipo,
            recurso_tipo,
            recurso_id,
            fecha_inicio,
            fecha_fin,
            observacion,
            creado_por
        ) VALUES (
            'FRANCO',
            'CHOFER',
            ?,
            ?,
            ?,
            ?,
            ?
        )
        """,
        (
            chofer_id,
            _to_iso(fecha_inicio),
            _to_iso(fecha_fin),
            observacion,
            usuario,
        ),
    )

    # 2️⃣ Buscar tractor asociado al chofer (si existe)
    cur.execute(
        """
        SELECT id_tractor
        FROM choferes
        WHERE id_chofer = ?
          AND id_tractor IS NOT NULL
        """,
        (chofer_id,),
    )
    row = cur.fetchone()

    if row:
        tractor_id = row["id_tractor"]

        # 3️⃣ Liberar tractor
        cur.execute(
            """
            UPDATE choferes
            SET id_tractor = NULL
            WHERE id_chofer = ?
            """,
            (chofer_id,),
        )

        cur.execute(
        """
        UPDATE tractores
        SET estado = 'OPERATIVO'
        WHERE id_tractor = ?
        """,
        (tractor_id,),
    )


    conn.commit()

def finalizar_franco(
    conn,
    evento_id: int,
    fecha_fin: date | None = None,
):
    """
    Finaliza un evento de FRANCO.
    """
    cur = conn.cursor()
    ff = fecha_fin or date.today()

    cur.execute(
        """
        UPDATE eventos
        SET fecha_fin = ?
        WHERE id = ?
          AND tipo = 'FRANCO'
        """,
        (_to_iso(ff), evento_id),
    )

    conn.commit()

# =================================================
# CONSULTAS
# =================================================
def listar_francos_mes(conn, year: int, month: int):
    inicio = date(year, month, 1)
    fin = date(year, month, monthrange(year, month)[1])

    cur = conn.cursor()
    cur.execute(
        """
        SELECT *
        FROM eventos
        WHERE tipo = 'FRANCO'
          AND fecha_inicio <= ?
          AND fecha_fin >= ?
        ORDER BY fecha_inicio
        """,
        (_to_iso(fin), _to_iso(inicio)),
    )
    return [dict(r) for r in cur.fetchall()]


def contadores_franco_por_chofer_mes(conn, year: int, month: int):
    inicio_mes = date(year, month, 1)
    fin_mes = date(year, month, monthrange(year, month)[1])

    cur = conn.cursor()
    cur.execute(
        """
        SELECT recurso_id, fecha_inicio, fecha_fin
        FROM eventos
        WHERE tipo = 'FRANCO'
          AND recurso_tipo = 'CHOFER'
          AND fecha_inicio <= ?
          AND fecha_fin >= ?
        """,
        (_to_iso(fin_mes), _to_iso(inicio_mes)),
    )

    dias_por_chofer = defaultdict(set)

    for r in cur.fetchall():
        cid = r["recurso_id"]
        fi = date.fromisoformat(r["fecha_inicio"])
        ff = date.fromisoformat(r["fecha_fin"])

        fi = max(fi, inicio_mes)
        ff = min(ff, fin_mes)

        d = fi
        while d <= ff:
            dias_por_chofer[cid].add(d)
            d += timedelta(days=1)

    return {cid: len(dias) for cid, dias in dias_por_chofer.items()}
