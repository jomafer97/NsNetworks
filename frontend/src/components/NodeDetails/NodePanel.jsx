import { useContext, useState } from 'react';
import { TopologyContext } from '../../context/TopologyContext';
import { DetailsPanel } from './DetailsPanel';

export function NodePanel() {
    const { nodes, startNode, deleteNode, selectedNode, setSelectedNode } = useContext(TopologyContext);

    const [isStarting, setIsStarting] = useState(false);
    const [isDeleting, setIsDeleting] = useState(false);

    const liveNodeData = selectedNode
        ? nodes.find(n => n.name === selectedNode.name)
        : null;

    const handleStart = async () => {
        setIsStarting(true);
        await startNode(liveNodeData.name);
        setIsStarting(false);
    };

    const handleDelete = async () => {
        setIsDeleting(true);
        await deleteNode(liveNodeData.name);
        setSelectedNode(null);
        setIsDeleting(false);
    };

    const isBusy = isStarting || isDeleting;

    return (
        <div className="p-4 bg-white rounded-lg border border-gray-200 h-full shadow-sm flex flex-col">
            <h3 className="text-lg font-semibold border-b border-gray-100 pb-2 mb-4 text-gray-800">
                Gestión y Monitorización
            </h3>

            {/* 2. REEMPLAZAMOS TODOS LOS 'nodeInfo' POR 'liveNodeData' */}
            {liveNodeData ? (
                <div className="flex flex-col flex-1">

                    <div className="flex-1">
                        {/* Le inyectamos los datos frescos al panel visual */}
                        <DetailsPanel nodeInfo={liveNodeData} />
                    </div>

                    <div className="mt-6 pt-4 border-t border-gray-100 flex gap-2">
                        {/* Como liveNodeData se actualiza en tiempo real, esto desaparecerá al instante */}
                        {liveNodeData.status === 'stopped' && (
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
            ) : (
                <p className="text-gray-500 text-sm text-center mt-8">
                    Haz clic sobre un recurso en el mapa topológico para inspeccionarlo y controlarlo.
                </p>
            )}
        </div>
    );
}