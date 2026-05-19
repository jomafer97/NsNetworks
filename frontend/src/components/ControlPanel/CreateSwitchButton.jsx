import { useContext } from "react"
import { TopologyContext } from "../../context/TopologyContext"
import switchIcon from '../../assets/switch.svg'

export const CreateSwitchButton = () => {
    const { createNode } = useContext(TopologyContext)

    return (
        <button
            onClick={() => createNode("switch")}
            className="flex items-center gap-3 py-2.5 px-4 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-semibold text-sm transition-colors shadow-sm w-full text-left"
        >
            <span className="shrink-0">
                <img
                    src={switchIcon}
                    alt="Icono Switch"
                    className="h-6 w-6 invert brightness-0"
                />
            </span>
            <span>Añadir Switch</span>
        </button>
    )
}