import { useContext } from "react"
import { TopologyContext } from "../../context/TopologyContext"

export const CreateLinkButton = () => {
    const { createNode, toggleLinkingMode, isLinkingMode } = useContext(TopologyContext)

    return (
        <button
            onClick={toggleLinkingMode}
            className={`flex items-center gap-3 py-2.5 px-4 rounded-lg font-semibold text-sm transition-colors shadow-sm w-full text-left ${isLinkingMode
                ? 'bg-gray-200 text-gray-800 hover:bg-gray-300 ring-2 ring-gray-400'
                : 'bg-blue-600 text-white hover:bg-blue-700'
                }`}
        >
            <span className="text-lg w-6 text-center">{isLinkingMode ? '✕' : '🔌'}</span>
            <span>{isLinkingMode ? 'Cancelar Cable' : 'Crear Enlace'}</span>
        </button>
    )
}