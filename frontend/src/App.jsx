import { useEffect, useState } from "react"

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  RadialBarChart,
  RadialBar,
  PolarAngleAxis
} from "recharts"

function App() {

  const API_BASE = `http://${window.location.hostname}:8000`

  const [systems, setSystems] = useState([])
  const [snapshots, setSnapshots] = useState([])
  const [selectedSnapshot, setSelectedSnapshot] = useState("")
  const [selectedSystem, setSelectedSystem] = useState("")
  const [history, setHistory] = useState([])
  const [gauges, setGauges] = useState([])
  const [loading, setLoading] = useState(true)
  const [trends, setTrends] = useState([])
  const [targetDates, setTargetDates] = useState({})

  useEffect(() => {

    fetch(`${API_BASE}/api/snapshots`)
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

    fetch(`${API_BASE}/api/gauges`)
      .then((res) => res.json())
      .then((data) => {

        setGauges(data)

      })
      .catch(console.error)

    fetch(`${API_BASE}/api/trends`)
      .then((res) => res.json())
      .then((data) => {

        setTrends(data)

      })
      .catch(console.error)


    fetch(`${API_BASE}/api/targets`)
      .then((res) => res.json())
      .then((data) => {

        const targetsMap = {}

        data.forEach((item) => {

          if (item.target_date) {

            targetsMap[item.sistema] = item.target_date

          }

        })

        setTargetDates(targetsMap)

      })
      .catch(console.error)

  }, [])

  useEffect(() => {

    if (!selectedSystem) {

      setHistory([])

      return
    }

    fetch(
      `${API_BASE}/api/history/${encodeURIComponent(selectedSystem)}`
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
      `${API_BASE}/api/systems?snapshot_date=${snapshotDate}`
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

  const selectedTrend = trends.find(
    t => t.sistema === selectedSystem
  )

  let chartData = [...history]

  if (
    selectedTrend &&
    selectedTrend.extinction_date &&
    history.length > 0
  ) {

    chartData = [

      ...history.map((point, index) => {

        const isLast =
          index === history.length - 1

        return {

          snapshot_date:
            point.snapshot_date,

          qty_nes:
            point.qty_nes,

          qty_projection:
            isLast
              ? point.qty_nes
              : null
        }

      }),

      {

        snapshot_date:
          selectedTrend.extinction_date,

        qty_nes:
          null,

        qty_projection:
          0

      }

    ]
  }

  return (

    <div style={{ padding: "20px" }}>

      <h1>InfraDash</h1>

      <h2>Estado actual de sistemas</h2>

      <div
        style={{
          display: "grid",
          gridTemplateColumns:
            "repeat(auto-fill, minmax(220px, 1fr))",
          gap: "16px",
          marginBottom: "30px"
        }}
      >

        {
          gauges.map((gauge) => (

            <div
              key={gauge.sistema}
              style={{
                border: "1px solid #ccc",
                borderRadius: "8px",
                padding: "10px",
                textAlign: "center"
              }}
            >

              <div
                style={{
                  fontWeight: "bold",
                  marginBottom: "10px",
                  fontSize: "14px"
                }}
              >
                {gauge.sistema}
              </div>

              <ResponsiveContainer
                width="100%"
                height={150}
              >

                <RadialBarChart
                  innerRadius="65%"
                  outerRadius="100%"
                  data={[
                    {
                      value: gauge.porcentaje
                    }
                  ]}
                  startAngle={180}
                  endAngle={0}
                >

                  <PolarAngleAxis
                    type="number"
                    domain={[0, 100]}
                    tick={false}
                  />

                  <RadialBar
                    dataKey="value"
                    background
                    cornerRadius={10}

           fill={
  gauge.porcentaje >= 100
    ? "#1565C0"
    : gauge.porcentaje >= 66
    ? "#D50000"
    : gauge.porcentaje >= 33
    ? "#FFD600"
    : "#00C853"
} 


                />

                </RadialBarChart>

              </ResponsiveContainer>

              <div>

                <b>
                  {gauge.actual}
                </b>

                <div>
                  Máx: {gauge.maximo}
                </div>

                <div>
                  {gauge.porcentaje}%
                </div>

                {
                  (() => {

                    const trend = trends.find(
                      t => t.sistema === gauge.sistema
                    )

                    if (!trend)
                      return null

                    let extinctionText = ""
                    let requiredTrendText = ""

                    if (
                      trend.direction === "down" &&
                      trend.trend < 0 &&
                      gauge.actual > 0
                    ) {

                      const monthsToZero =
                        gauge.actual / Math.abs(trend.trend)

                      const extinctionDate = new Date(
                        trend.last_snapshot_date
                      )

                      extinctionDate.setMonth(
                        extinctionDate.getMonth() +
                        Math.round(monthsToZero)
                      )

                      extinctionText =
                        extinctionDate.toISOString().slice(0, 10)
                    }

                    const targetDate = targetDates[gauge.sistema]

                    if (
                      targetDate &&
                      gauge.actual > 0
                    ) {

                      const target = new Date(targetDate)

                      const lastSnapshot = new Date(
                        trend.last_snapshot_date
                      )

                      const months =
                        (
                          target - lastSnapshot
                        ) /
                        (
                          1000 * 60 * 60 * 24 * 30.44
                        )

                      if (months > 0) {

                        const requiredTrend =
                          -(gauge.actual / months)

                        requiredTrendText =
                          requiredTrend.toFixed(1)
                      }
                    }

                    return (

                      <div>

                        <div
                          style={{
                            marginTop: "6px",
                            fontSize: "12px",
                            fontWeight: "bold"
                          }}
                        >

                          {
                            trend.direction === "up"
                              ? "⬆️ +" + trend.trend.toFixed(1) + " NE/mes"
                              : trend.direction === "down"
                              ? "⬇️ " + trend.trend.toFixed(1) + " NE/mes"
                              : "➡️ Estable"
                          }

                          {
                            extinctionText && (
                              <div
                                style={{
                                  marginTop: "4px",
                                  color: "#D50000"
                                }}
                              >
                                💀 Extinción estimada:
                                <br />
                                {extinctionText}
                              </div>
                            )
                          }

                        </div>

                        <div
                          style={{
                            marginTop: "8px",
                            fontSize: "11px"
                          }}
                        >

                          Fecha objetivo:

                          <br />

                          <input
                            type="date"
                            value={
                              targetDates[gauge.sistema] || ""
                            }

                            onChange={(e) => {

                              const newDate = e.target.value

                              setTargetDates({
                                ...targetDates,
                                [gauge.sistema]: newDate
                              })

                              fetch(`${API_BASE}/api/targets`, {
                                method: "POST",
                                headers: {
                                  "Content-Type": "application/json"
                                },
                                body: JSON.stringify({
                                  sistema: gauge.sistema,
                                  target_date: newDate || null
                                })
                              })
                                .then((res) => res.json())
                                .catch(console.error)

                            }}

                            />

                        </div>

                        {
                          requiredTrendText && (

                            <div
                              style={{
                                marginTop: "6px",
                                color: "#1565C0",
                                fontWeight: "bold"
                              }}
                            >
                              🎯 Tasa requerida:
                              <br />
                              {requiredTrendText} NE/mes
                            </div>

                          )
                        }

                      </div>

                    )

                  })()
                }

              </div>

            </div>

          ))
        }

      </div>

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

              <LineChart data={chartData}>

                <CartesianGrid strokeDasharray="3 3" />

                <XAxis dataKey="snapshot_date" />

                <YAxis />

                <Tooltip />

                <Line
                  type="monotone"
                  dataKey="qty_nes"
                  strokeWidth={2}
                  connectNulls={false}
                />

                <Line
                  type="linear"
                  dataKey="qty_projection"
                  strokeDasharray="8 4"
                  strokeWidth={2}
                  connectNulls={true}
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
