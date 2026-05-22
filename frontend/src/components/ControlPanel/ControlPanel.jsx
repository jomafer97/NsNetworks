import { useContext } from "react";
import { TopologyContext } from "../../context/TopologyContext";
import { CreateRouterButton } from "./CreateRouterButton";
import { CreateSwitchButton } from "./CreateSwitchButton";
import { CreateLinkButton } from "./CreateLinkButton";
import { DeleteLinkButton } from "./DeleteLinkButton";

export const ControlPanel = () => {
    return (
        <div className="flex flex-col h-full">
            <h3 className="font-bold text-lg mb-6 text-white border-b pb-2">
                Panel de Control
            </h3>

            <div className="mb-6">
                <h4 className="text-xs font-bold text-white uppercase tracking-wider mb-3">
                    Paleta de Dispositivos
                </h4>

                <div className="flex flex-col gap-2">
                    <CreateRouterButton />
                    <CreateSwitchButton />
                </div>
            </div>

            <div>
                <h4 className="text-xs font-bold text-white uppercase tracking-wider mb-3">
                    Gestión de Enlaces
                </h4>

                <div className="flex flex-col gap-2">
                    <CreateLinkButton />
                    <DeleteLinkButton />
                </div>
            </div>

            <div className="mt-auto pt-4 border-t border-gray-100 text-center">
                <span className="text-xs text-gray-400 font-mono">SDN Controller v1.0</span>
            </div>
        </div>
    )
}