import { useState, useContext } from "react";
import { TopologyContext } from "../../../context/TopologyContext";

export const ConfigEditorViewer = ({ data, nodeName }) => {
    const [configText, setConfigText] = useState(data);
    const [isSaving, setIsSaving] = useState(false);
    const { setRunningConfig } = useContext(TopologyContext);
    const [saveStatus, setSaveStatus] = useState({ type: '', message: '' });

    const handleSave = async () => {
        setIsSaving(true);
        setSaveStatus({ type: '', message: '' });

        try {
            const response = await setRunningConfig(nodeName, configText);

            if (response && response.status) {
                setSaveStatus({
                    type: response.status,
                    message: response.message
                });
            } else {
                setSaveStatus({
                    type: 'success',
                    message: 'Configuración enviada.'
                });
            }

        } catch (error) {
            console.error("Error al aplicar la configuración:", error);
            setSaveStatus({
                type: 'error',
                message: 'Fallo de comunicación con el orquestador. Revisa la consola.'
            });
        } finally {
            setIsSaving(false);

            setTimeout(() => {
                setSaveStatus(prev => prev.type === 'success' ? { type: '', message: '' } : prev);
            }, 5000);
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

            <div className="flex justify-between items-center min-h-[48px]">

                <div className="flex-1 mr-4">
                    {saveStatus.message && (
                        <div className={`p-3 rounded text-sm font-medium transition-all duration-300 ${saveStatus.type === 'success'
                            ? 'bg-green-100 text-green-800 border border-green-200'
                            : 'bg-red-100 text-red-800 border border-red-200'
                            }`}>
                            {saveStatus.message.split('\n').map((line, i) => (
                                <span key={i}>
                                    {line}
                                    <br />
                                </span>
                            ))}
                        </div>
                    )}
                </div>

                <button
                    onClick={handleSave}
                    disabled={isSaving || configText === data}
                    className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded font-bold shadow-sm transition-colors disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap"
                >
                    {isSaving ? 'Aplicando...' : 'Guardar y Recargar'}
                </button>
            </div>
        </div>
    );
};