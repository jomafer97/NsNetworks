import { useContext } from 'react';
import { TopologyGraph } from './components/TopologyGraph/TopologyGraph';
import { NodePanel } from './components/NodeDetails/NodePanel';
import { TopologyContext } from './context/TopologyContext';
import { ControlPanel } from './components/ControlPanel/ControlPanel';

function App() {
  // Extraemos TODO el estado global desde nuestro Contexto
  const {
    isLinkingMode, setIsLinkingMode,
    isDeletingLinkMode, setIsDeletingLinkMode,
    linkSource, setLinkSource,
    setSelectedNode,
    createLink, deleteLink
  } = useContext(TopologyContext);

  // La función maestra que procesa los clics del lienzo
  const handleGraphClick = async ({ node, edge }) => {

    // 1. MODO NORMAL (Inspección)
    if (!isLinkingMode && !isDeletingLinkMode) {
      setSelectedNode(node);
      return;
    }

    // 2. MODO BORRAR CABLE
    if (isDeletingLinkMode) {
      if (edge) {
        await deleteLink(edge); // Mandamos el ID del cable rojo al backend
        setIsDeletingLinkMode(false); // Apagamos el modo tijeras
      } else if (!node) {
        setIsDeletingLinkMode(false); // Clic al fondo blanco = cancelar
      }
      return;
    }

    // 3. MODO CREAR CABLE
    if (isLinkingMode) {
      if (!node) {
        setIsLinkingMode(false);
        setLinkSource(null);
        return;
      }

      if (!linkSource) {
        setLinkSource(node.name);
      } else {
        if (linkSource !== node.name) {
          await createLink(linkSource, node.name);
        }
        setLinkSource(null);
        setIsLinkingMode(false);
      }
    }
  };

  return (
    <div className="flex flex-col h-screen w-full bg-[#111827] overflow-hidden">

      {/* HEADER LIMPIO */}
      <div className="w-full flex justify-between items-center mb-6 px-6 pt-6 shrink-0">
        <h2 className="text-3xl font-bold text-amber-50">
          Controlador SDN
        </h2>
      </div>

      {/* BANNER DE AVISO: MODO CONEXIÓN */}
      {isLinkingMode && (
        <div className="w-full mb-4 px-6 shrink-0">
          <div className="bg-blue-100 border-l-4 border-blue-500 text-blue-700 p-4 rounded shadow-sm animate-pulse">
            <p className="font-semibold">
              Modo Conexión Activo: {' '}
              {!linkSource
                ? 'Haz clic en el nodo ORIGEN.'
                : `Has seleccionado '${linkSource}'. Ahora haz clic en el nodo DESTINO.`}
            </p>
          </div>
        </div>
      )}

      {/* BANNER DE AVISO: MODO BORRAR */}
      {isDeletingLinkMode && (
        <div className="w-full mb-4 px-6 shrink-0">
          <div className="bg-red-100 border-l-4 border-red-500 text-red-700 p-4 rounded shadow-sm animate-pulse">
            <p className="font-semibold">
              Modo Borrado Activo: Haz clic sobre un cable en el mapa para destruirlo.
            </p>
          </div>
        </div>
      )}

      {/* CONTENEDOR PRINCIPAL: 3 COLUMNAS */}
      <div className="flex flex-1 gap-6 w-full px-6 pb-6 min-h-0 min-w-0">

        {/* 1. PANEL LATERAL IZQUIERDO (Herramientas) */}
        <div className="w-64 shrink-0 bg-white shadow-lg border border-gray-200 rounded-lg h-full overflow-y-auto p-4 relative z-10">
          <ControlPanel />
        </div>

        {/* 2. LIENZO DE TOPOLOGÍA (Centro) */}
        <div className={`flex-1 bg-white rounded-lg border shadow-sm relative min-h-0 min-w-0 ${isLinkingMode ? 'border-blue-400 ring-2 ring-blue-100 cursor-crosshair' :
            isDeletingLinkMode ? 'border-red-400 ring-2 ring-red-100 cursor-crosshair' : 'border-gray-200'
          }`}>
          <div className="absolute inset-0 overflow-hidden rounded-lg">
            <TopologyGraph onNodeSelect={handleGraphClick} />
          </div>
        </div>

        {/* 3. PANEL LATERAL DERECHO (Monitorización) */}
        <div className="w-80 shrink-0 bg-white shadow-lg border border-gray-200 rounded-lg h-full overflow-y-auto relative z-10">
          <NodePanel />
        </div>

      </div>
    </div>
  );
}

export default App;