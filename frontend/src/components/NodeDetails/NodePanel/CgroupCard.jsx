export const CgroupCard = ({
    name,
    input,
    setInput,
    toggleLimit,
    min = "1",
    max = "100",
    step = "1",
    unit = "%",
    isSaving
}) => {
    return (
        <div className="flex flex-col gap-2">
            <div className="flex justify-between items-center">
                <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
                    {name}:
                </span>

                <label className="flex items-center gap-1.5 text-xs text-gray-600 cursor-pointer">
                    <input
                        type="checkbox"
                        checked={input !== ""}
                        onChange={(e) => toggleLimit(e.target.checked)}
                        disabled={isSaving}
                        className="rounded text-blue-600 focus:ring-blue-500 cursor-pointer disabled:opacity-50"
                    />
                    Limitar
                </label>
            </div>

            {input !== "" ? (
                <div className="flex items-center gap-3">
                    <input
                        type="range"
                        min={min} max={max} step={step} // 👈 Parámetros dinámicos
                        value={input}
                        disabled={isSaving}
                        onChange={(e) => setInput(e.target.value)}
                        className="w-full h-1.5 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600 disabled:opacity-50"
                    />
                    <div className="flex items-center gap-1 shrink-0">
                        <input
                            type="number" min={min} max={max}
                            value={input}
                            disabled={isSaving}
                            onChange={(e) => setInput(e.target.value)}
                            className="w-16 border border-gray-300 rounded px-1 py-1 text-xs text-center focus:outline-none focus:ring-1 focus:ring-blue-500 font-mono disabled:bg-gray-100"
                        />
                        <span className="text-xs font-mono text-gray-500">{unit}</span> {/* 👈 Unidad dinámica */}
                    </div>
                </div>
            ) : (
                <div className="text-xs text-gray-400 italic py-1">
                    Sin restricciones de {name.toLowerCase()} en el host.
                </div>
            )}
        </div>
    )
}