import { useContext, useState } from "react"
import { TopologyContext } from "../../../context/TopologyContext"

export const IfaceCard = ({ nodeName, nodeType, ifaceName, ifaceIp }) => {
    const { configureInterfaceIp, currentMode, setMode, MODES } = useContext(TopologyContext)

    const [inputValue, setInputValue] = useState("");
    const [isChanging, setIsChanging] = useState(false)

    if (nodeType?.toLowerCase() === 'switch') {
        return (
            <div className="flex items-center justify-between w-full">
                <code className="text-blue-950 font-mono text-sm font-bold min-w-15">
                    {ifaceName}
                </code>
                <span className="text-xs text-gray-500 font-semibold uppercase tracking-wider bg-gray-100 px-2 py-1 rounded border border-gray-200 shadow-sm cursor-not-allowed" title="Los puertos de Switch operan en Capa 2 y no requieren IP">
                    Puerto L2
                </span>
            </div>
        )
    }

    async function handleSave() {
        if (!inputValue.trim()) return;

        const regex = /^([0-9.]+)\/([0-9]+)$/;
        const match = inputValue.match(regex);

        if (!match) {
            alert("Formato inválido. Usa la notación CIDR. Ejemplo: 10.0.0.1/24");
            return;
        }

        const [_, addr, mask] = match;

        try {
            setMode(MODES.APPLYING_IP);
            await configureInterfaceIp(nodeName, ifaceName, addr, parseInt(mask, 10));
        } catch (e) {
            alert(`Fallo al configurar la interfaz: ${e}`);
        } finally {
            setMode(MODES.IDLE);
            setIsChanging(false);
        }

    }

    return (
        <div className="flex items-center justify-between w-full">
            <code className="text-blue-950 font-mono text-sm font-bold min-w-15">
                {ifaceName}
            </code>

            {(ifaceIp && !isChanging) ? (
                <div className="flex items-center gap-2">
                    <span className="bg-green-100 text-green-800 text-xs font-mono px-2 py-1 rounded border border-green-200 shadow-sm">
                        {ifaceIp}
                    </span>
                    <button
                        onClick={() => setIsChanging(true)}
                        disabled={currentMode !== MODES.IDLE}
                        className="bg-white hover:bg-gray-100 text-gray-600 border border-gray-300 px-2 py-1 rounded text-xs font-semibold transition-colors shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        Cambiar
                    </button>
                </div>
            ) : (
                <div className="flex items-center gap-2 flex-1 ml-2">
                    <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider whitespace-nowrap">
                        IP/CIDR:
                    </span>
                    <input
                        type="text"
                        placeholder="Ej: 10.0.0.1/24"
                        value={inputValue}
                        disabled={currentMode !== MODES.IDLE}
                        className="flex-1 border border-gray-300 rounded px-2 py-1 text-xs focus:outline-none focus:ring-1 focus:ring-blue-500 font-mono disabled:bg-gray-100 disabled:cursor-not-allowed disabled:opacity-50"
                        onChange={(e) => setInputValue(e.target.value)}
                    />
                    <button
                        onClick={handleSave}
                        disabled={currentMode !== MODES.IDLE}
                        className={`text-white px-3 py-1 rounded text-xs font-semibold transition-colors shadow-sm disabled:cursor-not-allowed disabled:opacity-50 ${currentMode === MODES.APPLYING_IP ? 'bg-blue-300 cursor-wait!' : 'bg-blue-600 hover:bg-blue-700'
                            }`}
                    >
                        {currentMode === MODES.APPLYING_IP ? '...' : 'Guardar'}
                    </button>
                </div>
            )}
        </div>
    )
}