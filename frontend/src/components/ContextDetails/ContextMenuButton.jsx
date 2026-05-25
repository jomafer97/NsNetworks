export const ContextMenuButton = ({ handleAction, name, className }) => {
    return (
        <button
            onClick={handleAction}
            className={className}
        >
            {name}
        </button>
    )
}