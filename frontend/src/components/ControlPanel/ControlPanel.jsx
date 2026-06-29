import { useContext } from "react";
import { TopologyContext } from "../../context/TopologyContext";
import { ControlPanelButton } from "./ControlPanelButton";

export const ControlPanel = () => {
    const {
        createNode,
        startAll,
        deleteAll,
        currentMode,
        setMode,
        MODES
    } = useContext(TopologyContext)

    return (
        <div className="flex flex-col h-full">
            <h3 className="font-bold text-lg mb-6 text-white border-b border-mauve-500 pb-2">
                Panel de Control
            </h3>

            <div className="mb-6">
                <h4 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-3">
                    Controles generales
                </h4>

                <div className="flex flex-col gap-2">
                    <ControlPanelButton handleClick={async () => {
                        try {
                            setMode(MODES.STARTING_NETWORK)
                            await startAll()
                        } catch (e) {
                            alert(`Fallo al inicializar los nodos de la red: ${e}`);
                        } finally {
                            setMode(MODES.IDLE)
                        }
                    }} disable={currentMode !== MODES.IDLE}
                        className={`bg-green-600! hover:bg-green-500! text-white ${currentMode !== MODES.IDLE ? 'opacity-50 cursor-not-allowed' : ''}`}
                        text={currentMode === MODES.STARTING_NETWORK ? 'Iniciando...' : 'Inicializar Todo'}
                    />

                    <ControlPanelButton handleClick={async () => {
                        try {
                            setMode(MODES.DELETING_NETWORK)
                            await deleteAll()
                        } catch (e) {
                            alert(`Fallo al eliminar la red: ${e}`);
                        } finally {
                            setMode(MODES.IDLE)
                        }
                    }} disable={currentMode !== MODES.IDLE}
                        className={`bg-red-600! hover:bg-red-500! text-white ${currentMode !== MODES.IDLE ? 'opacity-50 cursor-not-allowed' : ''}`}
                        text={currentMode === MODES.DELETING_NETWORK ? 'Eliminando...' : 'Eliminar Topología Actual'}
                    />
                </div>
            </div>

            <div className="mb-6">
                <h4 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-3">
                    Paleta de Dispositivos
                </h4>

                <div className="flex flex-col gap-2">
                    <ControlPanelButton handleClick={async () => {
                        try {
                            setMode(MODES.CREATING_NODE)
                            await createNode("router")
                        } catch (e) {
                            alert(`Fallo al crear el router: ${e}`);
                        } finally {
                            setMode(MODES.IDLE)
                        }
                    }}
                        disable={currentMode !== MODES.IDLE}
                        className={`${currentMode !== MODES.IDLE ? 'opacity-50 cursor-not-allowed' : ''}`}
                        text="Añadir Router"
                    />
                    <ControlPanelButton handleClick={async () => {
                        try {
                            setMode(MODES.CREATING_NODE)
                            await createNode("switch")
                        } catch (e) {
                            alert(`Fallo al crear el switch: ${e}`);
                        } finally {
                            setMode(MODES.IDLE)
                        }
                    }}
                        disable={currentMode !== MODES.IDLE}
                        className={`${currentMode !== MODES.IDLE ? 'opacity-50 cursor-not-allowed' : ''}`}
                        text="Añadir Switch"
                    />
                </div>
            </div>

            <div>
                <h4 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-3">
                    Gestión de Enlaces
                </h4>

                <div className="flex flex-col gap-2">
                    <ControlPanelButton
                        handleClick={() => {
                            currentMode === MODES.LINKING ? setMode(MODES.IDLE) : setMode(MODES.LINKING)
                        }}
                        disable={currentMode !== MODES.IDLE && currentMode !== MODES.LINKING}
                        className={`${currentMode !== MODES.IDLE && currentMode !== MODES.LINKING ? 'opacity-50 cursor-not-allowed' : ''} ${currentMode === MODES.LINKING ? 'bg-blue-600 hover:bg-blue-500 text-white font-bold' : ''}`}
                        text={currentMode === MODES.LINKING ? 'Cancelar Crear Enlaces' : 'Crear Enlaces'}
                    />

                    <ControlPanelButton
                        handleClick={() => {
                            currentMode === MODES.DELETING_LINK ? setMode(MODES.IDLE) : setMode(MODES.DELETING_LINK)
                        }}
                        disable={currentMode !== MODES.IDLE && currentMode !== MODES.DELETING_LINK}
                        className={`${currentMode !== MODES.IDLE && currentMode !== MODES.DELETING_LINK ? 'opacity-50 cursor-not-allowed' : ''} ${currentMode === MODES.DELETING_LINK ? 'bg-red-600 hover:bg-red-500 text-white font-bold' : ''}`}
                        text={currentMode === MODES.DELETING_LINK ? 'Cancelar Eliminar Enlaces' : 'Eliminar Enlaces'}
                    />
                </div>
            </div>

            <div className="mt-auto pt-4 border-t border-mauve-500 text-center">
                <span className="text-xs text-gray-400 font-mono">NsNetworks v1.0</span>
            </div>
        </div>
    )
}