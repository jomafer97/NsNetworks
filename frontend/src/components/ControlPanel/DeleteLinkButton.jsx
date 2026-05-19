import { useContext } from "react"
import { TopologyContext } from "../../context/TopologyContext"

export const DeleteLinkButton = () => {
    const { createNode, toggleDeletingLinkMode, isDeletingLinkMode } = useContext(TopologyContext)

    return (
        <button
            onClick={toggleDeletingLinkMode}
            className={`flex items-center gap-3 py-2.5 px-4 rounded-lg font-semibold text-sm transition-colors shadow-sm w-full text-left ${isDeletingLinkMode
                ? 'bg-gray-200 text-gray-800 hover:bg-gray-300 ring-2 ring-gray-400'
                : 'bg-white border border-red-200 hover:bg-red-50 text-red-600 ring-2 ring-gray-400'
                }`}
        >
            <span className="text-lg w-6 text-center">{isDeletingLinkMode ? '✕' : '✂️'}</span>
            <span>{isDeletingLinkMode ? 'Cancelar Borrado' : 'Borrar Enlace'}</span>
        </button>
    )
}