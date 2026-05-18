import { useEffect, useRef, useContext } from 'react';
import { TopologyContext } from '../../context/TopologyContext';
import { Network } from 'vis-network';
import { DataSet } from 'vis-data';

export function TopologyGraph({ onNodeSelect }) {
    const { nodes, links } = useContext(TopologyContext)

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
                        springLength: 150,
                        centralGravity: 0.2,
                        gravitationalConstant: -2500,
                        springConstant: 0.03,
                        damping: 0.09
                    },
                    solver: 'barnesHut',
                    maxVelocity: 25,
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
                if (params.nodes.length > 0) {
                    const clickedNodeId = params.nodes[0];
                    const nodeData = nodesDataSet.current.get(clickedNodeId);
                    onNodeSelectRef.current(nodeData?.rawData || null);
                } else {
                    onNodeSelectRef.current(null);
                }
            });
        }
    }, []);

    useEffect(() => {
        // 1. Traducimos al formato gráfico
        const formattedNodes = nodes.map(node => ({
            id: node.name,
            label: `${node.name}\n(${node.type})`,
            shape: 'box',
            color: node.type.toLowerCase() === 'switch' ? '#FFC107' : '#2196F3', // ¡Añadido el toLowerCase por seguridad!
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
        <div
            ref={containerRef}
            className='w-full h-150'
        />
    );
}