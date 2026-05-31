import { useEffect, useRef, useContext, useState } from 'react';
import { TopologyContext } from '../../context/TopologyContext';
import { Network } from 'vis-network';
import { DataSet } from 'vis-data';
import { ContextMenu } from '../ContextDetails/ContextMenu';
import { Modal } from '../ContextDetails/Modal';

export function TopologyGraph({ onNodeSelect }) {
    const { nodes, links } = useContext(TopologyContext);

    const containerRef = useRef(null);
    const networkRef = useRef(null);

    const nodesDataSet = useRef(new DataSet([]));
    const linksDataSet = useRef(new DataSet([]));

    const onNodeSelectRef = useRef(onNodeSelect);

    const [contextMenu, setContextMenu] = useState({
        show: false,
        x: 0,
        y: 0,
        node: null
    });

    const [modalState, setModalState] = useState({
        isOpen: false,
        title: '',
        content: null,
        isLoading: false
    });

    useEffect(() => {
        onNodeSelectRef.current = onNodeSelect;
    }, [onNodeSelect]);

    useEffect(() => {
        if (!networkRef.current && containerRef.current) {
            const options = {
                physics: {
                    barnesHut: {
                        springLength: 200,
                        centralGravity: 0.0,
                        gravitationalConstant: -2500,
                        springConstant: 0.15,
                        damping: 0.4
                    },
                    solver: 'barnesHut',
                    maxVelocity: 40,
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
                setContextMenu(prev => ({ ...prev, show: false }));

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

            networkRef.current.on('oncontext', (params) => {
                params.event.preventDefault();

                const nodeId = networkRef.current.getNodeAt(params.pointer.DOM);

                if (nodeId) {
                    const clickedNode = nodesDataSet.current.get(nodeId)?.rawData;

                    if (clickedNode) {
                        setContextMenu({
                            show: true,
                            x: params.event.clientX,
                            y: params.event.clientY,
                            node: clickedNode
                        });
                    }
                } else {
                    setContextMenu(prev => ({ ...prev, show: false }));
                }
            });

            networkRef.current.on('dragStart', () => {
                setContextMenu(prev => ({ ...prev, show: false }));
            });

            return () => {
                if (networkRef.current) {
                    networkRef.current.destroy();
                    networkRef.current = null;
                }
            };
        }
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

        const backendNodeIds = new Set(nodes.map(node => node.name));
        const paintedNodeIds = nodesDataSet.current.getIds();

        paintedNodeIds.forEach(paintedId => {
            if (!backendNodeIds.has(paintedId)) {
                nodesDataSet.current.remove(paintedId);
            }
        });

        const backendLinkIds = new Set(links.map(link => link.id));
        const paintedLinkIds = linksDataSet.current.getIds();

        paintedLinkIds.forEach(paintedId => {
            if (!backendLinkIds.has(paintedId)) {
                linksDataSet.current.remove(paintedId);
            }
        });

    }, [nodes, links]);

    return (
        <div
            ref={containerRef}
            className="w-full h-full bg-mauve-400 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
            tabIndex={0}
        >
            {contextMenu.show && contextMenu.node && (
                <ContextMenu contextMenu={contextMenu} setContextMenu={setContextMenu} setModalState={setModalState} />
            )}
            {modalState.isOpen && (
                <Modal modalState={modalState} setModalState={setModalState} />
            )}
        </div>
    );
}