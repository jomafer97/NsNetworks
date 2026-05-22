import { IfaceCard } from "./IfaceCard";
import { CgroupsPanel } from "./CgroupsPanel";

export function DetailsPanel({ nodeInfo }) {
    return (
        <div className="space-y-4 text-sm text-gray-700">
            <div className="bg-white p-4 rounded-md shadow-sm space-y-2">
                <h4 className="text-blue-600 font-bold uppercase text-base mb-2">
                    {nodeInfo.name}
                </h4>

                <p>
                    <span className="font-semibold text-gray-900">Tipo:</span> {nodeInfo.type}
                </p>

                <p>
                    <span className="font-semibold text-gray-900">Estado:</span>{' '}
                    <span className={`font-bold ${nodeInfo.status === 'UP' ? 'text-green-600' : 'text-red-600'}`}>
                        {nodeInfo.status.toUpperCase()}
                    </span>
                </p>

                {nodeInfo.type?.toLowerCase() === 'router' && (
                    <p className="flex items-center gap-2 mt-1">
                        <span className="font-semibold text-gray-900">PID en el host:</span>{' '}
                        {nodeInfo.pid !== null ? (
                            <code className="bg-gray-100 text-gray-800 px-2 py-0.5 border border-gray-200 rounded font-mono text-xs">
                                {nodeInfo.pid}
                            </code>
                        ) : (
                            <span className="text-gray-400 italic">No inicializado</span>
                        )}
                    </p>
                )}
            </div>

            <div className="bg-white p-4 rounded-md shadow-sm">
                <p className="font-semibold text-gray-900 mb-3">Interfaces virtuales:</p>

                {nodeInfo.interfaces && nodeInfo.interfaces.length > 0 ? (
                    <ul className="space-y-2 max-h-60 overflow-y-auto pr-1">
                        {nodeInfo.interfaces.map((iface) => {
                            const ifaceName = typeof iface === 'string' ? iface : iface.name;
                            const ifaceIp = typeof iface === 'string' ? null : iface.ip;

                            return (
                                <li
                                    key={`${nodeInfo.name}-${ifaceName}`}
                                    className="p-2 bg-gray-50 rounded border border-gray-200"
                                >
                                    <IfaceCard
                                        key={ifaceName}
                                        nodeName={nodeInfo.name}
                                        nodeType={nodeInfo.type}
                                        ifaceName={ifaceName}
                                        ifaceIp={ifaceIp}
                                    />
                                </li>
                            );
                        })}
                    </ul>
                ) : (
                    <p className="text-gray-400 italic text-xs">Sin cables conectados.</p>
                )}
            </div>

            {nodeInfo.type?.toLowerCase() === 'router' && (
                <CgroupsPanel nodeInfo={nodeInfo} />
            )}
        </div>
    );
}