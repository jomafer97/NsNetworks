import { useContext, useState, useEffect } from "react"
import { TopologyContext } from "../../../context/TopologyContext"
import { CgroupCard } from "./CgroupCard"

export const CgroupsPanel = ({ nodeInfo }) => {
    const { setCgroups } = useContext(TopologyContext)

    const [cpuInput, setCpuInput] = useState("")
    const [ramInput, setRamInput] = useState("")

    const [isSaving, setIsSaving] = useState(false)

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

        setIsSaving(true)
        await setCgroups(nodeInfo.name, { cpu: cpuVal, ram: ramVal })
        setIsSaving(false)
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
                    disabled={isSaving}
                    className={`text-white px-3 py-1 rounded text-xs font-semibold transition-colors shadow-sm ${isSaving ? 'bg-blue-300 cursor-wait' : 'bg-blue-600 hover:bg-blue-700'
                        }`}
                >
                    {isSaving ? 'Aplicando...' : 'Aplicar'}
                </button>
            </div>

            <CgroupCard
                name="CPU Máxima"
                input={cpuInput}
                setInput={setCpuInput}
                toggleLimit={toggleCpuLimit}
                isSaving={isSaving}
            />

            <div className="border-t border-gray-200 pt-3">
                <CgroupCard
                    name="Memoria RAM"
                    input={ramInput}
                    setInput={setRamInput}
                    toggleLimit={toggleRamLimit}
                    isSaving={isSaving}
                    min="16"
                    max="2048"
                    step="16"
                    unit="MB"
                />
            </div>
        </div>
    )
}