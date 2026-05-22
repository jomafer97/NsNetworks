import { useContext, useState } from 'react';
import { TopologyContext } from '../../../context/TopologyContext';
import { LinkCard } from './LinkCard';

export function LinkPanel() {
    // 🟢 Traemos también el array de 'nodes' para cruzar los datos
    const { nodes, links, deleteLink, selectedLink, setSelectedLink } = useContext(TopologyContext);
    const [isDeleting, setIsDeleting] = useState(false);

    const liveLinkData = selectedLink
        ? links.find(l => l.id === selectedLink)
        : null;

    if (!liveLinkData) return null;

    const sourceNode = nodes.find(n => n.name === liveLinkData.source);
    const targetNode = nodes.find(n => n.name === liveLinkData.target);

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
                    <h4 className="text-white font-bold uppercase text-sm tracking-wider mb-1">
                        Enlace Virtual (veth)
                    </h4>
                    <code className="bg-gray-100 text-gray-600 px-2 py-0.5 rounded font-mono text-xs block truncate">
                        ID: {liveLinkData.id}
                    </code>
                </div>

                <LinkCard name="Extremo A" node={liveLinkData.source} iface={liveLinkData.source_iface} Ip={sourceIp} />
                <LinkCard name="Extremo B" node={liveLinkData.target} iface={liveLinkData.target_iface} Ip={targetIp} />
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