import { createContext, useRef, useState, useEffect, useCallback } from 'react'
import { TfgService } from '../services/api';

export const TopologyContext = createContext()

export function TopologyContextProvider({ children }) {
    const [nodes, setNodes] = useState([]);
    const [links, setLinks] = useState([]);
    const [isLinkingMode, setIsLinkingMode] = useState(false);
    const [isDeletingLinkMode, setIsDeletingLinkMode] = useState(false);
    const [selectedNode, setSelectedNode] = useState(null);
    const [linkSource, setLinkSource] = useState(null);
    const nextRouterId = useRef(0)
    const nextSwitchId = useRef(0)

    const fetchTopology = useCallback(async () => {
        try {
            const data = await TfgService.getNetwork();
            setNodes(data.nodes);
            setLinks(data.links);

            let maxRouter = -1;
            let maxSwitch = -1;

            data.nodes.forEach(node => {
                if (node.type.toLowerCase() === 'router') {
                    const num = parseInt(node.name.replace('r', ''));
                    if (!isNaN(num) && num > maxRouter) maxRouter = num;
                }
                else if (node.type.toLowerCase() === 'switch') {
                    const num = parseInt(node.name.replace('s', ''));
                    if (!isNaN(num) && num > maxSwitch) maxSwitch = num;
                }
            });

            nextRouterId.current = maxRouter + 1;
            nextSwitchId.current = maxSwitch + 1;
        } catch (error) {
            console.error("Error de conexión con el controlador:", error);
        }
    }, []);

    const createNode = async (type) => {
        let name = ""

        switch (type) {
            case "router":
                name = `r${nextRouterId.current}`
                break
            case "switch":
                name = `s${nextSwitchId.current}`
                break
            default:
                console.error("Tipo de nodo no reconocido")
                return
        }

        try {
            await TfgService.createNode(name, type)
            await fetchTopology()
        } catch (error) {
            console.error("Error al crear el nodo:", error)
        }
    }

    const startNode = async (name) => {
        try {
            await TfgService.startNode(name)
            await fetchTopology()
        } catch (error) {
            console.error("Error al iniciar el nodo:", error)
        }
    }

    const deleteNode = async (name) => {
        try {
            await TfgService.deleteNode(name)
            await fetchTopology()
        } catch (error) {
            console.error("Error al eliminar el nodo:", error)
        }
    }

    const createLink = async (source, target) => {
        try {
            await TfgService.createLink(source, target)
            await fetchTopology()
        } catch (error) {
            console.error("Error al crear el link:", error)
        }
    }

    const deleteLink = async (id) => {
        try {
            await TfgService.deleteLink(id)
            await fetchTopology()
        } catch (error) {
            console.error("Error al eliminar el link:", error)
        }
    }

    const configureInterfaceIp = async (nodeName, ifaceName, addr, mask) => {
        try {
            await TfgService.setAddr(nodeName, ifaceName, addr, mask);
            await fetchTopology();
        } catch (error) {
            console.error("Fallo al sincronizar la IP con el controlador:", error);
        }
    }

    const toggleLinkingMode = () => {
        setIsDeletingLinkMode(false)
        setIsLinkingMode(!isLinkingMode);
        setLinkSource(null);
    };

    const toggleDeletingLinkMode = () => {
        setIsLinkingMode(false)
        setIsDeletingLinkMode(!isDeletingLinkMode);
        setLinkSource(null);
    };

    useEffect(() => {
        fetchTopology();
    }, [fetchTopology]);

    return (
        <TopologyContext.Provider value={{
            nodes, setNodes,
            links, setLinks,

            isLinkingMode, setIsLinkingMode, toggleLinkingMode,
            isDeletingLinkMode, setIsDeletingLinkMode, toggleDeletingLinkMode,
            selectedNode, setSelectedNode,
            linkSource, setLinkSource,

            createNode,
            startNode,
            deleteNode,
            createLink,
            deleteLink,
            configureInterfaceIp,
            fetchTopology
        }}>
            {children}
        </TopologyContext.Provider>
    )
}