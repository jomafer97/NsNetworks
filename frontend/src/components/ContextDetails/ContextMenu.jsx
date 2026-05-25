import { useContext } from "react";
import { TopologyContext } from "../../context/TopologyContext";
import { ContextMenuButton } from "./ContextMenuButton";

export const ContextMenu = ({ contextMenu, setContextMenu, setModalState }) => {
    const { getRunningConfig, getRoutingTable, getOspfInterfaces, getOspfNeighbors, getOspfBorderRouters } = useContext(TopologyContext)
    const actions = [
        ['routing_table', '📜 Ver tabla de enrutamiento'],
        ['config', '⚙️ Ver configuración'],
        ['ospf_neighbors', '🌐 Ver vecinos OSPF'],
        ['ospf_interfaces', '📡 Ver interfaces OSPF'],
        ['ospf_border_routers', '🚧 Ver routers frontera OSPF']
    ];

    const handleAction = async (nodeName, actionType) => {
        setContextMenu(prev => ({ ...prev, show: false }));

        setModalState({ isOpen: true, title: `Cargando ${actionType}...`, content: null, actionType, isLoading: true });

        try {
            let data = null;
            let title = "";
            let res;

            switch (actionType) {
                case 'routing_table':
                    title = `Tabla de enrutamiento: ${nodeName}`;
                    data = await getRoutingTable(nodeName);
                    break;
                case 'config':
                    title = `Running Config: ${nodeName}`;
                    res = await getRunningConfig(nodeName);
                    data = res.config;
                    break;
                case 'ospf_neighbors':
                    title = `Vecinos OSPF: ${nodeName}`;
                    data = await getOspfNeighbors(nodeName);
                    break;
                case 'ospf_interfaces':
                    title = `Interfaces OSPF: ${nodeName}`;
                    data = await getOspfInterfaces(nodeName);
                    break;
                case 'ospf_border_routers':
                    title = `Routers Frontera OSPF: ${nodeName}`;
                    data = await getOspfBorderRouters(nodeName);
                    break;
            }

            setModalState({ isOpen: true, title, content: data, actionType, isLoading: false });
        } catch (error) {
            console.error("Error al obtener datos:", error);
            setModalState({ isOpen: true, title: "Error", content: "No se pudo obtener la información.", isLoading: false });
        }
    };

    return (
        <div
            className="fixed bg-white border border-gray-200 shadow-xl rounded-lg py-1 w-56 z-50 text-sm overflow-hidden"
            style={{ top: contextMenu.y, left: contextMenu.x }}
            onMouseLeave={() => setContextMenu(prev => ({ ...prev, show: false }))}
        >
            <div className="px-4 py-2 font-bold border-b text-gray-800 bg-gray-50 uppercase text-xs tracking-wider">
                {contextMenu.node.name} <span className="font-normal text-gray-500 text-transform: capitalize">({contextMenu.node.type})</span>
            </div>

            {contextMenu.node.type.toLowerCase() === 'router' &&
                actions.map((action) => {
                    return (
                        <ContextMenuButton
                            key={action[0]} className="w-full text-left px-4 py-2 hover:bg-blue-50 text-gray-700 transition-colors"
                            name={action[1]} handleAction={() => handleAction(contextMenu.node.name, action[0])}
                        />
                    )
                })}
        </div>
    )
}