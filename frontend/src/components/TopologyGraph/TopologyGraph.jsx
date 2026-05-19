import { useEffect, useRef, useContext } from 'react';
import { TopologyContext } from '../../context/TopologyContext';
import { Network } from 'vis-network';
import { DataSet } from 'vis-data';

export function TopologyGraph({ onNodeSelect }) {
    const { nodes, links } = useContext(TopologyContext);

    const containerRef = useRef(null);
    const networkRef = useRef(null);

    const nodesDataSet = useRef(new DataSet([]));
    const linksDataSet = useRef(new DataSet([]));

    const onNodeSelectRef = useRef(onNodeSelect);

    useEffect(() => {
        onNodeSelectRef.current = onNodeSelect;
    }, [onNodeSelect]);

    useEffect(() => {
        if (!networkRef.current && containerRef.current) {
            const options = {
                physics: {
                    barnesHut: {
                        springLength: 150,         // Un poco más de aire entre nodos
                        centralGravity: 0.0,
                        gravitationalConstant: -2500, // Mayor repulsión para que no se pisen al crear varios
                        springConstant: 0.15,      // ⚖️ Tensión media: ni chicle ni acero.
                        damping: 0.4               // ⚖️ Amortiguación suave: permite un micro-rebote natural al soltar
                    },
                    solver: 'barnesHut',
                    maxVelocity: 40,               // ⚖️ Bajamos la velocidad máxima. Siguen al ratón bien, pero sin teletransportarse robóticamente
                    minVelocity: 0.75,
                    stabilization: {
                        enabled: true,
                        iterations: 1000,
                        updateInterval: 100
                    }
                },
                interaction: {
                    hover: true,
                    selectConnectedEdges: false,
                    multiselect: false
                }
            };

            networkRef.current = new Network(
                containerRef.current,
                { nodes: nodesDataSet.current, edges: linksDataSet.current },
                options
            );

            networkRef.current.on('click', (params) => {
                let clickedNode = null;
                let clickedEdgeId = null;

                if (params.nodes.length > 0) {
                    const nodeId = params.nodes[0];
                    clickedNode = nodesDataSet.current.get(nodeId)?.rawData || null;
                }
                else if (params.edges.length > 0) {
                    clickedEdgeId = params.edges[0];
                }

                onNodeSelectRef.current({
                    node: clickedNode,
                    edge: clickedEdgeId
                });
            });
        }

        // 🧹 REFACTOR: Cleanup para evitar memory leaks si el componente se desmonta
        return () => {
            if (networkRef.current) {
                networkRef.current.destroy();
                networkRef.current = null;
            }
        };
    }, []);

    useEffect(() => {
        const formattedNodes = nodes.map(node => ({
            id: node.name,
            label: `${node.name}\n(${node.type})`,
            shape: 'box',
            color: node.type.toLowerCase() === 'switch' ? '#FFC107' : '#2196F3',
            font: { color: 'white', face: 'monospace' },
            rawData: node
        }));

        const formattedLinks = links.map(link => ({
            id: link.id,
            from: link.source,
            to: link.target,
            label: `${link.source_iface} ↔ ${link.target_iface}`,
            font: { align: 'middle', size: 10, face: 'monospace' },
            color: { color: '#848484', hover: '#2196F3', highlight: '#F44336' }
        }));

        nodesDataSet.current.update(formattedNodes);
        linksDataSet.current.update(formattedLinks);

        const paintedNodeIds = nodesDataSet.current.getIds();
        paintedNodeIds.forEach(paintedId => {
            if (!nodes.some(backendNode => backendNode.name === paintedId)) {
                nodesDataSet.current.remove(paintedId);
            }
        });

        const paintedLinkIds = linksDataSet.current.getIds();
        paintedLinkIds.forEach(paintedId => {
            if (!links.some(backendLink => backendLink.id === paintedId)) {
                linksDataSet.current.remove(paintedId);
            }
        });

    }, [nodes, links]);

    return (
        <div ref={containerRef} className="w-full h-full outline-none bg-white"></div>
    );
}