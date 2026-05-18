import { useState, useContext } from 'react';
import { TopologyGraph } from './components/TopologyGraph/TopologyGraph';
import { NodePanel } from './components/NodeDetails/NodePanel';
import { TopologyContext } from './context/TopologyContext'; // Ajusta la ruta
import { ControlPanel } from './components/ControlPanel/ControlPanel';

function App() {
  const { createLink } = useContext(TopologyContext);

  const [selectedNode, setSelectedNode] = useState(null);

  const [isLinkingMode, setIsLinkingMode] = useState(false);
  const [linkSource, setLinkSource] = useState(null);

  const handleGraphClick = async (nodeData) => {
    if (!isLinkingMode) {
      setSelectedNode(nodeData);
      return;
    }

    if (!nodeData) {
      setIsLinkingMode(false);
      setLinkSource(null);
      return;
    }

    if (!linkSource) {
      setLinkSource(nodeData.name);
    }
    else {
      if (linkSource !== nodeData.name) {
        await createLink(linkSource, nodeData.name);
      }

      setLinkSource(null);
      setIsLinkingMode(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 p-6 font-sans flex flex-col">

      {/* HEADER PRINCIPAL Y CONTROLES */}
      <div className="max-w-7xl mx-auto w-full flex justify-between items-center mb-6">
        <h2 className="text-3xl font-bold text-amber-50">
          Controlador SDN
        </h2>

        {/* BOTÓN PARA ACTIVAR EL MODO CABLEADO */}
        <button
          onClick={() => {
            setIsLinkingMode(!isLinkingMode);
            setLinkSource(null);
          }}
          className={`px-4 py-2 rounded font-semibold transition-colors shadow-sm ${isLinkingMode
            ? 'bg-gray-600 text-white hover:bg-gray-700'
            : 'bg-blue-600 text-white hover:bg-blue-700'
            }`}
        >
          {isLinkingMode ? '✕ Cancelar Cableado' : '🔌 Conectar Nodos'}
        </button>
      </div>

      {/* BANNER DINÁMICO DE FEEDBACK (Solo se ve si el modo está activo) */}
      {isLinkingMode && (
        <div className="max-w-7xl mx-auto w-full mb-4 bg-blue-100 border-l-4 border-blue-500 text-blue-700 p-4 rounded shadow-sm animate-pulse">
          <p className="font-semibold">
            Modo Conexión Activo: {' '}
            {!linkSource
              ? 'Haz clic en el nodo ORIGEN.'
              : `Has seleccionado '${linkSource}'. Ahora haz clic en el nodo DESTINO.`}
          </p>
        </div>
      )}

      {/* CONTENEDOR DE LA TOPOLOGÍA */}
      <div className="flex gap-6 max-w-7xl mx-auto w-full h-150">

        {/* Grafo: Fíjate que ahora le pasamos nuestra función interceptora */}
        <div className={`flex-3 bg-white rounded-lg border shadow-sm overflow-hidden relative ${isLinkingMode ? 'border-blue-400 ring-2 ring-blue-100 cursor-crosshair' : 'border-gray-200'
          }`}>
          <TopologyGraph onNodeSelect={handleGraphClick} />
        </div>

        {/* Panel Lateral */}
        <div className="flex-1">
          <NodePanel
            nodeInfo={selectedNode}
            clearSelection={() => setSelectedNode(null)}
          />
          <ControlPanel />
        </div>

      </div>
    </div>
  );
}

export default App;