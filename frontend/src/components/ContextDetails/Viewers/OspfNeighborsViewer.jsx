export const OspfNeighborsViewer = ({ data }) => {
    if (!data || typeof data !== 'object' || Object.keys(data).length === 0) {
        return <p className="text-gray-500 italic p-4 text-center font-semibold">No hay vecinos OSPF detectados.</p>;
    }

    const neighborsData = data.neighbors || data;

    const neighborsList = [];
    Object.entries(neighborsData).forEach(([routerId, nList]) => {
        if (Array.isArray(nList)) {
            nList.forEach(n => neighborsList.push({ routerId, ...n }));
        }
    });

    if (neighborsList.length === 0) {
        return <p className="text-gray-500 italic p-4 text-center font-semibold">La base de datos de vecinos está vacía.</p>;
    }

    return (
        <div className="overflow-x-auto rounded-lg border border-gray-200 shadow-sm">
            <table className="min-w-full divide-y divide-gray-200 text-sm text-left">
                <thead className="bg-gray-50">
                    <tr>
                        <th className="px-4 py-3 font-semibold text-gray-700 uppercase tracking-wider text-xs">Router ID</th>
                        <th className="px-4 py-3 font-semibold text-gray-700 uppercase tracking-wider text-xs">Estado</th>
                        <th className="px-4 py-3 font-semibold text-gray-700 uppercase tracking-wider text-xs">IP Vecino</th>
                        <th className="px-4 py-3 font-semibold text-gray-700 uppercase tracking-wider text-xs">Interfaz</th>
                        <th className="px-4 py-3 font-semibold text-gray-700 uppercase tracking-wider text-xs">Dead Time</th>
                    </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-100">
                    {neighborsList.map((neighbor, idx) => {
                        // 🟢 Cambiado a nbrState
                        const state = neighbor.nbrState || 'N/A';
                        const isFull = state.toLowerCase().includes('full');

                        return (
                            <tr key={idx} className="hover:bg-gray-50 transition-colors">
                                <td className="px-4 py-3 font-mono font-bold text-gray-900">{neighbor.routerId}</td>
                                <td className="px-4 py-3">
                                    <span className={`px-2 py-1 rounded text-xs font-bold uppercase tracking-wider
                                        ${isFull ? 'bg-green-100 text-green-800 border border-green-200' : 'bg-yellow-100 text-yellow-800 border border-yellow-200'}`}
                                    >
                                        {state}
                                    </span>
                                </td>
                                {/* 🟢 Usamos ifaceAddress */}
                                <td className="px-4 py-3 font-mono text-gray-600">{neighbor.ifaceAddress || 'N/A'}</td>
                                {/* 🟢 Usamos ifaceName */}
                                <td className="px-4 py-3 text-blue-600 font-semibold">{neighbor.ifaceName || 'N/A'}</td>
                                {/* 🟢 Usamos el string formateado deadTime directo del JSON */}
                                <td className="px-4 py-3 font-mono text-gray-500">{neighbor.deadTime || 'N/A'}</td>
                            </tr>
                        );
                    })}
                </tbody>
            </table>
        </div>
    );
};