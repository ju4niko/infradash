import { useEffect, useState } from "react"

function App() {

  const [systems, setSystems] = useState([])

  const [loading, setLoading] = useState(true)

  useEffect(() => {

    fetch("http://localhost:8000/api/systems")

      .then((res) => res.json())

      .then((data) => {

        setSystems(data)

        setLoading(false)
      })

      .catch((err) => {

        console.error(err)

        setLoading(false)
      })

  }, [])

  return (

    <div style={{ padding: "20px" }}>

      <h1>InfraDash</h1>

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
