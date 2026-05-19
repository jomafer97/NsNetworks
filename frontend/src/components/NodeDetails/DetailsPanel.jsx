import { IfaceCard } from "./IfaceCard";

export function DetailsPanel({ nodeInfo }) {
    return (
        <div className="space-y-3 text-sm text-gray-700">
            <h4 className="text-blue-600 font-bold uppercase text-base">
                {nodeInfo.name}
            </h4>

            <p>
                <span className="font-semibold text-gray-900">Tipo:</span> {nodeInfo.type}
            </p>

            <p>
                <span className="font-semibold text-gray-900">Estado:</span>{' '}
                <span className={`font-bold ${nodeInfo.status === 'running' || nodeInfo.status === 'up' ? 'text-green-600' : 'text-red-600'}`}>
                    {nodeInfo.status.toUpperCase()}
                </span>
            </p>

            {nodeInfo.type?.toLowerCase() === 'router' && (
                <p>
                    <span className="font-semibold text-gray-900">PID en el host:</span>{' '}
                    {nodeInfo.pid !== null ? (
                        <code className="bg-gray-100 text-gray-800 px-2 py-1 rounded font-mono text-xs">
                            {nodeInfo.pid}
                        </code>
                    ) : (
                        <span className="text-gray-400 italic">No inicializado</span>
                    )}
                </p>
            )}

            <div>
                <p className="font-semibold text-gray-900 mb-2">Interfaces virtuales:</p>
                {nodeInfo.interfaces && nodeInfo.interfaces.length > 0 ? (
                    <ul className="space-y-2 max-h-60 overflow-y-auto pr-1">
                        {nodeInfo.interfaces.map((iface, index) => {
                            const ifaceName = typeof iface === 'string' ? iface : iface.name;
                            const ifaceIp = typeof iface === 'string' ? null : iface.ip;

                            return (
                                <li key={`${nodeInfo.name}-${ifaceName}`} className="flex flex-col gap-1 p-2 bg-gray-50 rounded border border-gray-200">
                                    <IfaceCard
                                        key={iface.name}
                                        nodeName={nodeInfo.name}
                                        nodeType={nodeInfo.type}
                                        ifaceName={iface.name}
                                        ifaceIp={iface.ip}
                                    />
                                </li>
                            );
                        })}
                    </ul>
                ) : (
                    <p className="text-gray-400 italic text-xs">Sin cables conectados.</p>
                )}
            </div>
        </div>
    );
}