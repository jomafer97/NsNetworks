import { useContext, useState } from 'react';
import { TopologyContext } from '../../../context/TopologyContext';
import { DetailsPanel } from './DetailsPanel';

export function NodePanel() {
    const { nodes, startNode, deleteNode, selectedNode, setSelectedNode, setMode, MODES } = useContext(TopologyContext);

    const [isStarting, setIsStarting] = useState(false);
    const [isDeleting, setIsDeleting] = useState(false);

    const liveNodeData = selectedNode
        ? nodes.find(n => n.name === selectedNode.name)
        : null;

    if (!liveNodeData) return null;

    const handleStart = async () => {
        try {
            setMode(MODES.STARTING_NODE)
            setIsStarting(true)
            await startNode(liveNodeData.name);
        } catch (e) {
            alert(`Fallo al inicializar el nodo: ${e}`);
        } finally {
            setMode(MODES.IDLE)
            setIsStarting(false)
        }
    };

    const handleDelete = async () => {
        try {
            setMode(MODES.DELETING_NODE)
            setIsDeleting(true)
            await deleteNode(liveNodeData.name);
        } catch (e) {
            alert(`Fallo al eliminar el nodo: ${e}`);
        } finally {
            setMode(MODES.IDLE)
            setIsDeleting(false)
            setSelectedNode(null)
        }
    };

    const isBusy = isStarting || isDeleting;

    return (
        <div className="flex flex-col flex-1 h-full">

            <div className="flex-1 overflow-y-auto">
                <DetailsPanel nodeInfo={liveNodeData} />
            </div>

            <div className="mt-6 pt-4 border-t border-gray-100 flex gap-2 shrink-0">
                {liveNodeData.status === 'DOWN' && (
                    <button
                        onClick={handleStart}
                        disabled={isBusy}
                        className={`flex-1 py-2 px-4 rounded text-white font-semibold text-sm transition-colors ${isStarting ? 'bg-green-300 cursor-wait' : 'bg-green-600 hover:bg-green-700'
                            }`}
                    >
                        {isStarting ? 'Iniciando...' : '▶ Iniciar'}
                    </button>
                )}

                <button
                    onClick={handleDelete}
                    disabled={isBusy}
                    className={`flex-1 py-2 px-4 rounded text-white font-semibold text-sm transition-colors ${isDeleting ? 'bg-red-300 cursor-wait' : 'bg-red-600 hover:bg-red-700'
                        }`}
                >
                    {isDeleting ? 'Destruyendo...' : '🗑 Eliminar Nodo'}
                </button>
            </div>
        </div>
    );
}