import { useContext, useState, useEffect } from "react"
import { TopologyContext } from "../../../context/TopologyContext"
import { CgroupCard } from "./CgroupCard"

export const CgroupsPanel = ({ nodeInfo }) => {
    const { setCgroups, currentMode, setMode, MODES } = useContext(TopologyContext)

    const [cpuInput, setCpuInput] = useState("")
    const [ramInput, setRamInput] = useState("")

    useEffect(() => {
        setCpuInput(nodeInfo.cgroups?.cpu || "")
        setRamInput(nodeInfo.cgroups?.ram || "")
    }, [nodeInfo])

    const handleSave = async () => {
        const cpuVal = cpuInput !== "" ? parseInt(cpuInput, 10) : null
        const ramVal = ramInput !== "" ? parseInt(ramInput, 10) : null

        if (cpuVal !== null && (cpuVal < 1 || cpuVal > 100)) {
            alert("El límite de CPU debe estar entre 1% y 100%.")
            return
        }
        if (ramVal !== null && ramVal < 16) {
            alert("El contenedor requiere un mínimo de 16 MB de RAM para operar.")
            return
        }

        try {
            setMode(MODES.APPLYING_CGROUPS)
            await setCgroups(nodeInfo.name, { cpu: cpuVal, ram: ramVal })
        } catch (e) {
            alert(`Fallo al configurar los cgroups: ${e}`);
        } finally {
            setMode(MODES.IDLE)
        }
    }

    const toggleCpuLimit = (checked) => setCpuInput(checked ? "50" : "");
    const toggleRamLimit = (checked) => setRamInput(checked ? "512" : "");

    return (
        <div className="mt-4 p-3 bg-gray-50 rounded border border-gray-200 shadow-sm flex flex-col gap-4">

            <div className="flex justify-between items-center border-b border-gray-200 pb-2">
                <h5 className="font-bold text-gray-900 text-xs uppercase tracking-wider flex items-center gap-2">
                    <span>⚙️</span> Cgroups
                </h5>
                <button
                    onClick={handleSave}
                    disabled={currentMode !== MODES.IDLE}
                    className={`text-white px-3 py-1 rounded text-xs font-semibold transition-colors shadow-sm disabled:cursor-not-allowed disabled:opacity-50 ${currentMode === MODES.APPLYING_CGROUPS
                        ? 'bg-blue-300 cursor-wait!'
                        : 'bg-blue-600 hover:bg-blue-700'
                        }`}
                >
                    {currentMode === MODES.APPLYING_CGROUPS ? 'Aplicando...' : 'Aplicar'}
                </button>
            </div>

            <CgroupCard
                name="CPU Máxima"
                input={cpuInput}
                setInput={setCpuInput}
                toggleLimit={toggleCpuLimit}
            />

            <div className="border-t border-gray-200 pt-3">
                <CgroupCard
                    name="Memoria RAM"
                    input={ramInput}
                    setInput={setRamInput}
                    toggleLimit={toggleRamLimit}
                    min="16"
                    max="2048"
                    step="16"
                    unit="MB"
                />
            </div>
        </div>
    )
}