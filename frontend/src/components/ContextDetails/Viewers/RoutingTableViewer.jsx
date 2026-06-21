export const RoutingTableViewer = ({ data }) => {
    if (!data || typeof data !== 'object') {
        return <p className="text-gray-500 italic p-4">No hay datos de enrutamiento disponibles.</p>;
    }

    if (Object.keys(data).length === 0) {
        return <p className="text-gray-500 italic p-4 text-center font-semibold">La tabla de rutas está vacía. Esperando convergencia OSPF...</p>;
    }

    return (
        <div className="overflow-x-auto rounded-lg border border-gray-200 shadow-sm">
            <table className="min-w-full divide-y divide-gray-200 text-sm text-left">
                <thead className="bg-gray-50">
                    <tr>
                        <th className="px-4 py-3 font-semibold text-gray-700 uppercase tracking-wider text-xs">Red Destino</th>
                        <th className="px-4 py-3 font-semibold text-gray-700 uppercase tracking-wider text-xs">Protocolo</th>
                        <th className="px-4 py-3 font-semibold text-gray-700 uppercase tracking-wider text-xs">AD/Métrica</th>
                        <th className="px-4 py-3 font-semibold text-gray-700 uppercase tracking-wider text-xs">Siguiente Salto</th>
                    </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-100">
                    {Object.entries(data).map(([prefix, routes]) => (
                        routes.map((route, idx) => (
                            <tr key={`${prefix}-${idx}`} className="hover:bg-gray-50 transition-colors">
                                <td className="px-4 py-3 font-mono font-bold text-gray-900">
                                    {prefix}
                                </td>
                                <td className="px-4 py-3">
                                    <span className={`px-2 py-1 rounded text-xs font-bold uppercase tracking-wider
                                        ${route.protocol === 'ospf' ? 'bg-blue-100 text-blue-800 border border-blue-200' :
                                            route.protocol === 'connected' ? 'bg-green-100 text-green-800 border border-green-200' :
                                                'bg-gray-100 text-gray-800 border border-gray-200'}`}
                                    >
                                        {route.protocol}
                                    </span>
                                </td>
                                <td className="px-4 py-3 font-mono text-gray-600">
                                    [{route.distance}/{route.metric}]
                                </td>
                                <td className="px-4 py-3 text-gray-700">
                                    {route.nexthops?.map((nh, i) => (
                                        <div key={i} className="flex items-center gap-2">
                                            {nh.ip && <span className="font-mono bg-gray-100 px-1.5 py-0.5 rounded">{nh.ip}</span>}
                                            {nh.interfaceName && <span className="text-blue-600 font-semibold">{nh.interfaceName}</span>}
                                        </div>
                                    ))}
                                </td>
                            </tr>
                        ))
                    ))}
                </tbody>
            </table>
        </div>
    );
};