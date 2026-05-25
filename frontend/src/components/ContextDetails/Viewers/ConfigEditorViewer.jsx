import { useState, useContext } from "react";
import { TopologyContext } from "../../../context/TopologyContext";

export const ConfigEditorViewer = ({ data, nodeName }) => {
    const [configText, setConfigText] = useState(data);
    const [isSaving, setIsSaving] = useState(false);
    const { setRunningConfig } = useContext(TopologyContext);

    const handleSave = async () => {
        setIsSaving(true);
        try {
            await setRunningConfig(nodeName, configText);
            alert("Configuración aplicada y recargada en FRRouting.");
        } catch (error) {
            alert("Error al aplicar la configuración. Revisa la consola.");
        } finally {
            setIsSaving(false);
        }
    };

    if (!data) return <p className="text-gray-500 italic">No hay configuración disponible.</p>;

    return (
        <div className="flex flex-col h-full gap-4">
            <textarea
                value={configText}
                onChange={(e) => setConfigText(e.target.value)}
                disabled={isSaving}
                className="w-full h-96 bg-gray-900 text-green-400 p-4 rounded-md font-mono text-sm shadow-inner focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
                spellCheck="false"
            />
            <div className="flex justify-end">
                <button
                    onClick={handleSave}
                    disabled={isSaving || configText === data}
                    className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded font-bold shadow-sm transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    {isSaving ? 'Aplicando...' : 'Guardar y Recargar'}
                </button>
            </div>
        </div>
    );
};