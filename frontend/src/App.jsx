import { useEffect, useState } from "react"

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer
} from "recharts"

function App() {

  const [systems, setSystems] = useState([])
  const [snapshots, setSnapshots] = useState([])
  const [selectedSnapshot, setSelectedSnapshot] = useState("")
  const [selectedSystem, setSelectedSystem] = useState("")
  const [history, setHistory] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {

    fetch("http://localhost:8000/api/snapshots")
      .then((res) => res.json())
      .then((data) => {

        setSnapshots(data)

        if (data.length > 0) {

          const latest = data[0].snapshot_date

          setSelectedSnapshot(latest)

          loadSystems(latest)
        }
      })
      .catch(console.error)

  }, [])

  useEffect(() => {

    if (!selectedSystem) {

      setHistory([])

      return
    }

    fetch(
      `http://localhost:8000/api/history/${encodeURIComponent(selectedSystem)}`
    )
      .then((res) => res.json())
      .then((data) => {

        setHistory(data)
      })
      .catch(console.error)

  }, [selectedSystem])

  function loadSystems(snapshotDate) {

    setLoading(true)

    fetch(
      `http://localhost:8000/api/systems?snapshot_date=${snapshotDate}`
    )
      .then((res) => res.json())
      .then((data) => {

        setSystems(data)

        setLoading(false)
      })
      .catch((err) => {

        console.error(err)

        setLoading(false)
      })
  }

  function handleSnapshotChange(event) {

    const snapshotDate = event.target.value

    setSelectedSnapshot(snapshotDate)

    loadSystems(snapshotDate)
  }

  return (

    <div style={{ padding: "20px" }}>

      <h1>InfraDash</h1>

      <div style={{ marginBottom: "20px" }}>

        <label>

          Snapshot:&nbsp;

          <select
            value={selectedSnapshot}
            onChange={handleSnapshotChange}
          >

            {
              snapshots.map((snapshot) => (

                <option
                  key={snapshot.id}
                  value={snapshot.snapshot_date}
                >
                  {snapshot.snapshot_date}
                </option>

              ))
            }

          </select>

        </label>

      </div>

      <div style={{ marginBottom: "20px" }}>

        <label>

          Sistema:&nbsp;

          <select
            value={selectedSystem}
            onChange={(e) => setSelectedSystem(e.target.value)}
          >

            <option value="">
              Seleccionar sistema
            </option>

            {
              [...new Set(
                systems.map(
                  s => s.sistemas
                )
              )]
                .sort()
                .map(system => (

                  <option
                    key={system}
                    value={system}
                  >
                    {system}
                  </option>

                ))
            }

          </select>

        </label>

      </div>

      {
        history.length > 0 && (

          <div
            style={{
              width: "100%",
              height: 400,
              marginBottom: "30px"
            }}
          >

            <h3>
              Evolución histórica de NEs
            </h3>

            <ResponsiveContainer>

              <LineChart data={history}>

                <CartesianGrid strokeDasharray="3 3" />

                <XAxis dataKey="snapshot_date" />

                <YAxis />

                <Tooltip />

                <Line
                  type="monotone"
                  dataKey="qty_nes"
                />

              </LineChart>

            </ResponsiveContainer>

          </div>

        )
      }

      <p>
        Sistemas cargados: <b>{systems.length}</b>
      </p>

      {
        loading
          ? <p>Cargando...</p>
          : (
            <table
              border="1"
              cellPadding="8"
              style={{
                borderCollapse: "collapse",
                width: "100%"
              }}
            >

              <thead>

                <tr>
                  <th>ID</th>
                  <th>Sistema</th>
                  <th>Vendor</th>
                  <th>Tecnología</th>
                  <th>NEs</th>
                  <th>Infra</th>
                  <th>Soporte</th>
                </tr>

              </thead>

              <tbody>

                {
                  systems.map((system) => (

                    <tr key={system.id}>

                      <td>{system.id}</td>
                      <td>{system.sistemas}</td>
                      <td>{system.vendor}</td>
                      <td>{system.tecnologia}</td>
                      <td>{system.qty_nes_numeric}</td>
                      <td>{system.infra}</td>
                      <td>{system.soporte}</td>

                    </tr>
                  ))
                }

              </tbody>

            </table>
          )
      }

    </div>
  )
}

export default App
