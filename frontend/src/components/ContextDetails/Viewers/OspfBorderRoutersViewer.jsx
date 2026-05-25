export const OspfBorderRoutersViewer = ({ data }) => {
    if (!data || typeof data !== 'object' || Object.keys(data).length === 0) {
        return <p className="text-gray-500 italic p-4 text-center font-semibold">No se conocen Routers Frontera (ABR/ASBR).</p>;
    }

    // 🟢 FRRouting anida los routers bajo la clave "routers"
    const routersData = data.routers || data;

    const routersList = [];
    Object.entries(routersData).forEach(([routerId, routerInfo]) => {
        // 🟢 Ahora no intentamos iterar sobre un array, pasamos el objeto directamente
        routersList.push({ routerId, ...routerInfo });
    });

    if (routersList.length === 0) {
        return <p className="text-gray-500 italic p-4 text-center font-semibold">No hay rutas hacia routers frontera.</p>;
    }

    return (
        <div className="overflow-x-auto rounded-lg border border-gray-200 shadow-sm">
            <table className="min-w-full divide-y divide-gray-200 text-sm text-left">
                <thead className="bg-gray-50">
                    <tr>
                        <th className="px-4 py-3 font-semibold text-gray-700 uppercase tracking-wider text-xs">Router Destino</th>
                        <th className="px-4 py-3 font-semibold text-gray-700 uppercase tracking-wider text-xs">Rol</th>
                        <th className="px-4 py-3 font-semibold text-gray-700 uppercase tracking-wider text-xs">Tipo de Ruta</th>
                        <th className="px-4 py-3 font-semibold text-gray-700 uppercase tracking-wider text-xs">Siguiente Salto</th>
                        <th className="px-4 py-3 font-semibold text-gray-700 uppercase tracking-wider text-xs">Coste</th>
                    </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-100">
                    {routersList.map((router, idx) => {
                        const isASBR = router.routerType?.toLowerCase().includes('asbr');
                        return (
                            <tr key={idx} className="hover:bg-gray-50 transition-colors">
                                <td className="px-4 py-3 font-mono font-bold text-gray-900">{router.routerId}</td>
                                <td className="px-4 py-3">
                                    <span className={`px-2 py-1 rounded text-xs font-bold uppercase tracking-wider
                                        ${isASBR ? 'bg-orange-100 text-orange-800 border border-orange-200' : 'bg-blue-100 text-blue-800 border border-blue-200'}`}
                                    >
                                        {router.routerType || 'ABR'}
                                    </span>
                                </td>
                                <td className="px-4 py-3 font-mono text-gray-600">{router.routeType || 'N/A'}</td>
                                <td className="px-4 py-3">
                                    {router.nexthops?.map((nh, i) => (
                                        <div key={i} className="flex items-center gap-2">
                                            {/* 🟢 Mostramos IP y la interfaz local (nh.via) */}
                                            {nh.ip && <span className="font-mono bg-gray-100 px-1.5 py-0.5 rounded">{nh.ip}</span>}
                                            {nh.via && <span className="text-blue-600 font-semibold">{nh.via}</span>}
                                        </div>
                                    ))}
                                </td>
                                <td className="px-4 py-3 font-mono font-bold text-gray-900">{router.cost || '-'}</td>
                            </tr>
                        );
                    })}
                </tbody>
            </table>
        </div>
    );
};