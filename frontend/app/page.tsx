"use client";

import { useEffect, useState } from "react";

export default function Home() {
  const [data, setData] = useState<any>(null);
  const [name, setName] = useState("");
  const [wattage, setWattage] = useState("");
  const [priority, setPriority] = useState("");
  const [message, setMessage] = useState("");

  const getStatus = async () => {
    const response = await fetch("http://127.0.0.1:8000/status");
    const result = await response.json();
    setData(result);
  };

  useEffect(() => {
    getStatus();
  }, []);

  const addLoad = async () => {
    const response = await fetch("http://127.0.0.1:8000/loads", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        name: name,
        wattage: Number(wattage),
        priority: Number(priority),
      }),
    });

    const result = await response.json();

    if (response.ok) {
      setMessage(result.message);
      setName("");
      setWattage("");
      setPriority("");
      getStatus();
    } else {
      setMessage(result.detail || "Unable to add appliance");
    }
  };

  const changeStatus = async (id: number, status: string) => {
    const response = await fetch(
      `http://127.0.0.1:8000/loads/${id}/status`,
      {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ status: status }),
      }
    );

    const result = await response.json();

    if (response.ok) {
      setMessage(result.message);
    } else {
      setMessage(result.detail);
    }

    getStatus();
  };

  const deleteLoad = async (id: number) => {
    const response = await fetch(
      `http://127.0.0.1:8000/loads/${id}`,
      {
        method: "DELETE",
      }
    );

    const result = await response.json();
    setMessage(result.message);

    getStatus();
  };

  if (!data) {
    return <p>Loading...</p>;
  }

  return (
    <main className="container">

      <h1>Inverter Load Manager</h1>

      <div className="capacity">
        <h2>
          {data.current_load}W / {data.capacity}W
        </h2>

        <p>Available: {data.remaining_capacity}W</p>

        <div className="bar">
          <div
            className="used"
            style={{
              width: `${(data.current_load / data.capacity) * 100}%`,
            }}
          ></div>
        </div>
      </div>

      {message && (
        <div className="message">
          {message}
        </div>
      )}

      <div className="form">
        <h2>Add Appliance</h2>

        <input
          type="text"
          placeholder="Appliance name"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />

        <input
          type="number"
          placeholder="Wattage"
          value={wattage}
          onChange={(e) => setWattage(e.target.value)}
        />

        <input
          type="number"
          placeholder="Priority"
          value={priority}
          onChange={(e) => setPriority(e.target.value)}
        />

        <button onClick={addLoad}>
          Add
        </button>
      </div>

      <h2>Appliances</h2>

      {data.loads.map((load: any) => (
        <div className="appliance" key={load.Id}>

          <div>
            <h3>{load.Name}</h3>

            <p>
              {load.Wattage}W | Priority {load.Priority}
            </p>

            <p>
              Status:{" "}
              <strong className={load.Status}>
                {load.Status}
              </strong>
            </p>
          </div>

          <div className="buttons">
            {load.Status === "off" ? (
              <button
                onClick={() => changeStatus(load.Id, "on")}
              >
                Turn On
              </button>
            ) : (
              <button
                onClick={() => changeStatus(load.Id, "off")}
              >
                Turn Off
              </button>
            )}

            <button
              className="delete"
              onClick={() => deleteLoad(load.Id)}
            >
              Delete
            </button>
          </div>

        </div>
      ))}

    </main>
  );
}