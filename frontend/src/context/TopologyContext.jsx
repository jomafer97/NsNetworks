import { createContext, useRef, useState, useEffect, useCallback } from 'react'
import { TfgService } from '../services/api';

export const TopologyContext = createContext()

export function TopologyContextProvider({ children }) {
    const MODES = {
        IDLE: 'IDLE',
        DELETING_NETWORK: 'DELETING_NETWORK',
        STARTING_NETWORK: 'STARTING_NETWORK',
        CREATING_NODE: 'CREATING_NODE',
        STARTING_NODE: 'STARTING_NODE',
        DELETING_NODE: 'DELETING_NODE',
        LINKING: 'LINKING',
        DELETING_LINK: 'DELETING_LINK',
        APPLYING_IP: 'APPLYING_IP',
        APPLYING_CGROUPS: 'APPLYING_CGROUPS'
    }

    const [currentMode, setCurrentMode] = useState(MODES.IDLE);

    const setMode = (newMode) => {
        setCurrentMode(newMode);
    };

    const [nodes, setNodes] = useState([]);
    const [links, setLinks] = useState([]);
    const [selectedNode, setSelectedNode] = useState(null);
    const [selectedLink, setSelectedLink] = useState(null);
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

    const deleteAll = async () => {
        try {
            await TfgService.deleteAll()
            await fetchTopology()
        } catch (error) {
            console.error("Error al eliminar la red:", error)
            throw error;
        }
    };

    const startAll = async () => {
        try {
            await TfgService.startAll()
            await fetchTopology()
        } catch (error) {
            console.error("Error al inicializar la red:", error)
            throw error;
        }
    };

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
            throw error;
        }
    }

    const startNode = async (name) => {
        try {
            await TfgService.startNode(name)
            await fetchTopology()
        } catch (error) {
            console.error("Error al iniciar el nodo:", error)
            throw error;
        }
    }

    const deleteNode = async (name) => {
        try {
            await TfgService.deleteNode(name)
            await fetchTopology()
        } catch (error) {
            console.error("Error al eliminar el nodo:", error)
            throw error;
        }
    }

    const createLink = async (source, target) => {
        try {
            await TfgService.createLink(source, target)
            await fetchTopology()
        } catch (error) {
            console.error("Error al crear el link:", error)
            throw error;
        }
    }

    const deleteLink = async (id) => {
        try {
            await TfgService.deleteLink(id)
            await fetchTopology()
        } catch (error) {
            console.error("Error al eliminar el link:", error)
            throw error;
        }
    }

    const configureInterfaceIp = async (nodeName, ifaceName, addr, mask) => {
        try {
            await TfgService.setAddr(nodeName, ifaceName, addr, mask);
            await fetchTopology();
        } catch (error) {
            console.error("Fallo al sincronizar la IP con el controlador:", error);
            throw error;
        }
    }

    const setCgroups = async (nodeName, cgroupsData) => {
        try {
            await TfgService.setCgroups(nodeName, cgroupsData);
            await fetchTopology();
        } catch (error) {
            console.error("Fallo al establecer los cgroups:", error);
            throw error;
        }
    }

    const setRunningConfig = async (nodeName, config) => {
        try {
            return await TfgService.setRunningConfig(nodeName, config);
        } catch (error) {
            console.error("Fallo al establecer la configuración:", error);
            throw error;
        }
    }

    const getRunningConfig = async (name) => {
        try {
            return await TfgService.getRunningConfig(name);
        } catch (error) {
            console.error("Fallo al obtener la configuración del nodo:", error);
            throw error;
        }
    }

    const getRoutingTable = async (name) => {
        try {
            return await TfgService.getRoutingTable(name);
        } catch (error) {
            console.error("Fallo al obtener la tabla de enrutamiento del nodo:", error);
            throw error;
        }
    }

    const getOspfInterfaces = async (name) => {
        try {
            return await TfgService.getOspfInterfaces(name);
        } catch (error) {
            console.error("Fallo al obtener las interfaces OSPF del nodo:", error);
            throw error;
        }
    }

    const getOspfNeighbors = async (name) => {
        try {
            return await TfgService.getOspfNeighbors(name);
        } catch (error) {
            console.error("Fallo al obtener los vecinos OSPF del nodo:", error);
            throw error;
        }
    }

    const getOspfBorderRouters = async (name) => {
        try {
            return await TfgService.getOspfBorderRouters(name);
        } catch (error) {
            console.error("Fallo al obtener los routers frontera OSPF del nodo:", error);
            throw error;
        }
    }

    useEffect(() => {
        fetchTopology();
    }, [fetchTopology]);

    return (
        <TopologyContext.Provider value={{
            nodes, setNodes,
            links, setLinks,

            currentMode, setMode, MODES,
            selectedNode, setSelectedNode,
            selectedLink, setSelectedLink,
            linkSource, setLinkSource,

            createNode,
            startNode,
            deleteNode,
            createLink,
            deleteLink,
            configureInterfaceIp,
            setCgroups,
            deleteAll,
            startAll,
            setRunningConfig,
            fetchTopology,

            getRunningConfig,
            getRoutingTable,
            getOspfInterfaces,
            getOspfNeighbors,
            getOspfBorderRouters
        }}>
            {children}
        </TopologyContext.Provider>
    )
}