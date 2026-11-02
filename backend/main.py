from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Load(BaseModel):
    name: str
    wattage: int
    priority: int

class StatusUpdate(BaseModel):
    status: str

def get_db_connection():
    conn = sqlite3.connect("load_manager.db")
    conn.row_factory = sqlite3.Row
    return conn

@app.get("/")
def read():
    return {"message": "Welcome to the Load Manager API"}

@app.get("/status")
def get_status():
    conn = get_db_connection()

    loads = conn.execute(
        "SELECT * FROM loads"
    ).fetchall()

    current_load = conn.execute("""
        SELECT COALESCE(SUM(Wattage), 0) AS total
        FROM loads
        WHERE Status = 'on'
    """).fetchone()["total"]

    conn.close()

    return {
        "capacity": 800,
        "current_load": current_load,
        "remaining_capacity": 800 - current_load,
        "loads": [dict(load) for load in loads]
    }

@app.post("/loads")
def add_load(load: Load):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO loads (Name, Wattage, Priority, Status)
    VALUES (?, ?, ?, ?)
    """, (load.name, load.wattage, load.priority, "off"))
    conn.commit()
    conn.close()
    return {"message": "Load added successfully"}


@app.delete("/loads/{id}")
def delete_load(id: int):
    conn = get_db_connection()

    load = conn.execute(
        "SELECT * FROM loads WHERE Id = ?",
        (id,)
    ).fetchone()

    if load is None:
        conn.close()
        raise HTTPException(
            status_code=404,
            detail="Appliance not found"
        )

    conn.execute(
        "DELETE FROM loads WHERE Id = ?",
        (id,)
    )

    restored = auto_restore(conn)

    conn.commit()
    conn.close()

    return {
        "message": f"{load['Name']} deleted successfully",
        "restored": restored
    }

@app.put("/loads/{id}/status")
def update_status(id: int, data: StatusUpdate):
    requested_status = data.status.lower()

    if requested_status not in ["on", "off"]:
        raise HTTPException(
            status_code=400,
            detail="Status must be on or off"
        )

    conn = get_db_connection()

    load = conn.execute(
        "SELECT * FROM loads WHERE Id = ?",
        (id,)
    ).fetchone()

    if load is None:
        conn.close()
        raise HTTPException(
            status_code=404,
            detail="Appliance not found"
        )

    if requested_status == "off":
        conn.execute(
            "UPDATE loads SET Status = 'off' WHERE Id = ?",
            (id,)
        )

        restored = auto_restore(conn)

        conn.commit()
        conn.close()

        return {
            "message": f"{load['Name']} turned off",
            "restored": restored
        }

    if load["Status"] == "on":
        conn.close()

        return {
            "message": f"{load['Name']} is already on"
        }

    current_load = conn.execute("""
        SELECT COALESCE(SUM(Wattage), 0) AS total
        FROM loads
        WHERE Status = 'on'
    """).fetchone()["total"]

    if current_load + load["Wattage"] <= 800:
        conn.execute(
            "UPDATE loads SET Status = 'on' WHERE Id = ?",
            (id,)
        )

        conn.commit()
        conn.close()

        return {
            "message": f"{load['Name']} turned on",
            "shed": []
        }

    watts_needed = current_load + load["Wattage"] - 800

    candidates = conn.execute("""
        SELECT * FROM loads
        WHERE Status = 'on'
        AND Priority > ?
        ORDER BY Priority DESC, Id ASC
    """, (load["Priority"],)).fetchall()

    watts_available = sum(
        candidate["Wattage"] for candidate in candidates
    )

    if watts_available < watts_needed:
        conn.close()

        raise HTTPException(
            status_code=409,
            detail=(
                f"Cannot turn on {load['Name']}. "
                f"It needs {watts_needed}W more, but only "
                f"{watts_available}W can be freed from "
                f"lower-priority appliances."
            )
        )

    shed_names = []
    watts_freed = 0

    for candidate in candidates:
        conn.execute(
            "UPDATE loads SET Status = 'shed' WHERE Id = ?",
            (candidate["Id"],)
        )

        shed_names.append(candidate["Name"])
        watts_freed += candidate["Wattage"]

        if watts_freed >= watts_needed:
            break

    conn.execute(
        "UPDATE loads SET Status = 'on' WHERE Id = ?",
        (id,)
    )

    conn.commit()
    conn.close()

    return {
        "message": f"{load['Name']} turned on",
        "shed": shed_names
    }


def auto_restore(conn):
    restored = []

    current_load = conn.execute("""
        SELECT COALESCE(SUM(Wattage), 0) AS total
        FROM loads
        WHERE Status = 'on'
    """).fetchone()["total"]

    shed_loads = conn.execute("""
        SELECT * FROM loads
        WHERE Status = 'shed'
        ORDER BY Priority ASC, Id ASC
    """).fetchall()

    for load in shed_loads:
        if current_load + load["Wattage"] <= 800:
            conn.execute(
                "UPDATE loads SET Status = 'on' WHERE Id = ?",
                (load["Id"],)
            )

            current_load += load["Wattage"]
            restored.append(load["Name"])

    return restored