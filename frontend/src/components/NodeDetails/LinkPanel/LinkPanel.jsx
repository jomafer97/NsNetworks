import { useContext, useState } from 'react';
import { TopologyContext } from '../../../context/TopologyContext';

export function LinkPanel() {
    // 🟢 Traemos también el array de 'nodes' para cruzar los datos
    const { nodes, links, deleteLink, selectedLink, setSelectedLink } = useContext(TopologyContext);
    const [isDeleting, setIsDeleting] = useState(false);

    const liveLinkData = selectedLink
        ? links.find(l => l.id === selectedLink)
        : null;

    if (!liveLinkData) return null;

    // 🟢 CROSS-REFERENCING: Buscamos los nodos completos en el estado global
    const sourceNode = nodes.find(n => n.name === liveLinkData.source);
    const targetNode = nodes.find(n => n.name === liveLinkData.target);

    // 🟢 Buscamos el objeto interfaz dentro de cada nodo para sacar su IP actual
    const sourceIfaceObj = sourceNode?.interfaces?.find(
        i => (typeof i === 'string' ? i : i.name) === liveLinkData.source_iface
    );
    const targetIfaceObj = targetNode?.interfaces?.find(
        i => (typeof i === 'string' ? i : i.name) === liveLinkData.target_iface
    );

    const sourceIp = typeof sourceIfaceObj === 'object' ? sourceIfaceObj?.ip : null;
    const targetIp = typeof targetIfaceObj === 'object' ? targetIfaceObj?.ip : null;

    const handleDelete = async () => {
        setIsDeleting(true);
        await deleteLink(liveLinkData.id);
        setSelectedLink(null);
        setIsDeleting(false);
    };

    return (
        <div className="flex flex-col flex-1 h-full">
            <div className="flex-1 overflow-y-auto space-y-4 text-sm text-gray-700 pr-1">
                <div>
                    <h4 className="text-red-600 font-bold uppercase text-sm tracking-wider mb-1">
                        Enlace Virtual (veth)
                    </h4>
                    <code className="bg-gray-100 text-gray-600 px-2 py-0.5 rounded font-mono text-xs block truncate">
                        ID: {liveLinkData.id}
                    </code>
                </div>

                {/* EXTREMO A */}
                <div className="p-3 bg-gray-50 rounded-lg border border-gray-200 shadow-sm">
                    <span className="text-xs font-bold text-gray-400 uppercase tracking-wider block mb-1">
                        Extremo A
                    </span>
                    <p className="font-semibold text-gray-900">
                        🖥️ Nodo: <span className="font-mono text-blue-600 font-bold">{liveLinkData.source}</span>
                    </p>
                    <p className="text-gray-600 mt-1 text-xs">
                        🔌 Interfaz: <code className="bg-white border border-gray-300 px-1.5 py-0.5 rounded font-mono text-gray-800 font-bold">{liveLinkData.source_iface}</code>
                    </p>
                    {/* 🟢 Renderizado dinámico de la IP del extremo A */}
                    <div className="mt-2 pt-1.5 border-t border-gray-200/60 flex items-center justify-between">
                        <span className="text-xs text-gray-400">Capa 3:</span>
                        {sourceIp ? (
                            <span className="bg-green-100 text-green-800 font-mono text-xs px-1.5 py-0.5 rounded border border-green-200">
                                {sourceIp}
                            </span>
                        ) : (
                            <span className="text-gray-400 italic text-xs">Sin IP asignada</span>
                        )}
                    </div>
                </div>

                <div className="flex justify-center text-gray-400 my-0.5">
                    <span className="text-lg font-bold">↕</span>
                </div>

                {/* EXTREMO B */}
                <div className="p-3 bg-gray-50 rounded-lg border border-gray-200 shadow-sm">
                    <span className="text-xs font-bold text-gray-400 uppercase tracking-wider block mb-1">
                        Extremo B
                    </span>
                    <p className="font-semibold text-gray-900">
                        🖥️ Nodo: <span className="font-mono text-blue-600 font-bold">{liveLinkData.target}</span>
                    </p>
                    <p className="text-gray-600 mt-1 text-xs">
                        🔌 Interfaz: <code className="bg-white border border-gray-300 px-1.5 py-0.5 rounded font-mono text-gray-800 font-bold">{liveLinkData.target_iface}</code>
                    </p>
                    {/* 🟢 Renderizado dinámico de la IP del extremo B */}
                    <div className="mt-2 pt-1.5 border-t border-gray-200/60 flex items-center justify-between">
                        <span className="text-xs text-gray-400">Capa 3:</span>
                        {targetIp ? (
                            <span className="bg-green-100 text-green-800 font-mono text-xs px-1.5 py-0.5 rounded border border-green-200">
                                {targetIp}
                            </span>
                        ) : (
                            <span className="text-gray-400 italic text-xs">Sin IP asignada</span>
                        )}
                    </div>
                </div>

                <div className="pt-2 border-t border-gray-100 space-y-1.5">
                    <p className="text-xs text-gray-500">
                        <span className="font-semibold text-gray-700">Tipo de Medio:</span> Virtual Ethernet Pair
                    </p>
                    <p className="text-xs text-gray-500">
                        <span className="font-semibold text-gray-700">Estado:</span>{' '}
                        <span className="text-green-600 font-bold uppercase tracking-wider">UP</span>
                    </p>
                </div>
            </div>

            <div className="mt-6 pt-4 border-t border-gray-100 shrink-0">
                <button
                    onClick={handleDelete}
                    disabled={isDeleting}
                    className={`w-full py-2 px-4 rounded text-white font-semibold text-sm transition-colors shadow-sm ${isDeleting ? 'bg-red-300 cursor-wait' : 'bg-red-600 hover:bg-red-700'
                        }`}
                >
                    {isDeleting ? 'Cortando cable...' : '✂️ Eliminar Enlace'}
                </button>
            </div>
        </div>
    );
}