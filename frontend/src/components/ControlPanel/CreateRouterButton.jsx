import { useContext } from "react"
import { TopologyContext } from "../../context/TopologyContext"
import routerIcon from '../../assets/router.svg'

export const CreateRouterButton = () => {
    const { createNode } = useContext(TopologyContext)

    return (
        <button
            onClick={() => createNode("router")}
            className="flex items-center gap-3 py-2.5 px-4 bg-slate-800 hover:bg-slate-900 text-white rounded-lg font-semibold text-sm transition-colors shadow-sm w-full text-left"
        >
            <span className="shrink-0">
                <img
                    src={routerIcon}
                    alt="Icono Router"
                    className="h-6 w-6 invert brightness-0"
                />
            </span>
            <span>Añadir Router</span>
        </button>
    )
}