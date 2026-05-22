export function LinkCard({ name, node, iface, Ip }) {
    return (
        <div className="p-3 bg-gray-50 rounded-lg border border-gray-200 shadow-sm">
            <span className="text-xs font-bold text-gray-400 uppercase tracking-wider block mb-1">
                {name}
            </span>
            <p className="font-semibold text-gray-900">
                🖥️ Nodo: <span className="font-mono text-blue-600 font-bold">{node}</span>
            </p>
            <p className="text-gray-600 mt-1 text-xs">
                🔌 Interfaz: <code className="bg-white border border-gray-300 px-1.5 py-0.5 rounded font-mono text-gray-800 font-bold">{iface}</code>
            </p>
            <div className="mt-2 pt-1.5 border-t border-gray-200/60 flex items-center justify-between">
                <span className="text-xs text-gray-400">IP:</span>
                {Ip ? (
                    <span className="bg-green-100 text-green-800 font-mono text-xs px-1.5 py-0.5 rounded border border-green-200">
                        {Ip}
                    </span>
                ) : (
                    <span className="text-gray-400 italic text-xs">Sin IP asignada</span>
                )}
            </div>
        </div>
    )
}