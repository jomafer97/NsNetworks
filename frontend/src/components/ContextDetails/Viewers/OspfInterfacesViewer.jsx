export const OspfInterfacesViewer = ({ data }) => {
    if (!data || typeof data !== 'object' || Object.keys(data).length === 0) {
        return <p className="text-gray-500 italic p-4 text-center font-semibold">No hay interfaces OSPF activas.</p>;
    }

    const interfacesData = data.interfaces || data;

    return (
        <div className="overflow-x-auto rounded-lg border border-gray-200 shadow-sm">
            <table className="min-w-full divide-y divide-gray-200 text-sm text-left">
                <thead className="bg-gray-50">
                    <tr>
                        <th className="px-4 py-3 font-semibold text-gray-700 uppercase tracking-wider text-xs">Interfaz</th>
                        <th className="px-4 py-3 font-semibold text-gray-700 uppercase tracking-wider text-xs">Estado</th>
                        <th className="px-4 py-3 font-semibold text-gray-700 uppercase tracking-wider text-xs">Área OSPF</th>
                        <th className="px-4 py-3 font-semibold text-gray-700 uppercase tracking-wider text-xs">IP / Máscara</th>
                        <th className="px-4 py-3 font-semibold text-gray-700 uppercase tracking-wider text-xs">Coste</th>
                    </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-100">
                    {Object.entries(interfacesData).map(([ifaceName, info], idx) => {
                        const state = info.state || 'Down';
                        const isDR = state === 'DR';
                        const isBDR = state === 'BDR';
                        const isUp = state !== 'Down';

                        return (
                            <tr key={idx} className="hover:bg-gray-50 transition-colors">
                                <td className="px-4 py-3 text-blue-600 font-bold">{ifaceName}</td>
                                <td className="px-4 py-3">
                                    <span className={`px-2 py-1 rounded text-xs font-bold uppercase tracking-wider
                                        ${isDR ? 'bg-purple-100 text-purple-800 border border-purple-200' :
                                            isBDR ? 'bg-indigo-100 text-indigo-800 border border-indigo-200' :
                                                isUp ? 'bg-green-100 text-green-800 border border-green-200' :
                                                    'bg-red-100 text-red-800 border border-red-200'}`}
                                    >
                                        {state}
                                    </span>
                                </td>
                                <td className="px-4 py-3 font-mono text-gray-700">{info.area || 'N/A'}</td>
                                <td className="px-4 py-3 font-mono text-gray-600">
                                    {info.ipAddress ? `${info.ipAddress}/${info.ipAddressPrefixlen}` : 'Unnumbered'}
                                </td>
                                <td className="px-4 py-3 font-mono font-bold text-gray-900">{info.cost || '-'}</td>
                            </tr>
                        );
                    })}
                </tbody>
            </table>
        </div>
    );
};