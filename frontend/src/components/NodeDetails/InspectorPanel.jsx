import { useContext } from "react"
import { TopologyContext } from "../../context/TopologyContext"
import { NodePanel } from "./NodePanel/NodePanel"
import { LinkPanel } from "./LinkPanel/LinkPanel" // Asumo que lo vas a crear ahora

export const InspectorPanel = () => {
    const { selectedNode, selectedLink } = useContext(TopologyContext)

    const Wrapper = ({ children }) => (
        <div className="p-4 rounded-lg border border-gray-200 h-full shadow-sm flex flex-col">
            <h3 className="text-lg font-semibold border-b border-gray-100 pb-2 mb-4 text-white">
                Gestión y Monitorización
            </h3>
            {children}
        </div>
    )

    if (selectedNode) {
        return <Wrapper><NodePanel /></Wrapper>
    }

    if (selectedLink) {
        return <Wrapper><LinkPanel /></Wrapper>
    }

    return (
        <Wrapper>
            <p className="text-white text-sm text-center mt-8">
                Haz clic sobre un recurso en el mapa topológico para inspeccionarlo y controlarlo.
            </p>
        </Wrapper >
    )
}