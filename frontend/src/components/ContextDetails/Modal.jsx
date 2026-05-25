import { useRef } from 'react';
import Draggable from 'react-draggable';
import { RoutingTableViewer } from './Viewers/RoutingTableViewer';
import { OspfBorderRoutersViewer } from './Viewers/OspfBorderRoutersViewer'
import { OspfInterfacesViewer } from './Viewers/OspfInterfacesViewer'
import { OspfNeighborsViewer } from './Viewers/OspfNeighborsViewer'
import { ConfigEditorViewer } from './Viewers/ConfigEditorViewer';

export const Modal = ({ modalState, setModalState }) => {
    const nodeRef = useRef(null);

    const renderContent = () => {
        if (modalState.isLoading) {
            return (
                <div className="flex justify-center items-center h-32 text-gray-500 animate-pulse">
                    Conectando con el router...
                </div>
            );
        }

        if (!modalState.content) return <p className="text-gray-500">Sin datos</p>;

        switch (modalState.actionType) {
            case 'routing_table':
                return <RoutingTableViewer data={modalState.content} />;

            case 'ospf_neighbors':
                return <OspfNeighborsViewer data={modalState.content} />;

            case 'ospf_interfaces':
                return <OspfInterfacesViewer data={modalState.content} />;

            case 'ospf_border_routers':
                return <OspfBorderRoutersViewer data={modalState.content} />;

            case 'config':
                return <ConfigEditorViewer data={modalState.content} nodeName={modalState.title.split(': ')[1]} />;

            default:
                return <p className="text-red-500 font-bold p-4">{JSON.stringify(modalState.content)}</p>;
        }
    };

    return (
        <Draggable handle=".drag-header" nodeRef={nodeRef}>
            <div ref={nodeRef} className="fixed top-24 left-1/4 bg-white rounded-lg shadow-2xl w-full max-w-3xl max-h-[70vh] flex flex-col z-50 border border-gray-300">
                <div className="drag-header cursor-move flex justify-between items-center px-4 py-3 bg-gray-100 border-b rounded-t-lg select-none">
                    <h3 className="font-bold text-sm text-gray-800">{modalState.title}</h3>
                    <button
                        onMouseDown={(e) => e.stopPropagation()}
                        onClick={() => setModalState({ ...modalState, isOpen: false })}
                        className="text-gray-500 hover:text-red-500 font-bold text-xl leading-none"
                    >
                        &times;
                    </button>
                </div>

                <div className="p-4 overflow-auto grow bg-white rounded-b-lg">
                    {renderContent()}
                </div>
            </div>
        </Draggable>
    );
};