import { useContext } from "react";
import { TopologyContext } from "../../context/TopologyContext";

export const ControlPanel = () => {
    const { createNode } = useContext(TopologyContext)

    return <button onClick={() => createNode("router")}>
        Crear Router
    </button>
}