export const ControlPanelButton = ({ handleClick, disable, className, text }) => {
    const baseClasses = "flex items-center gap-3 py-2.5 px-4 rounded-lg font-semibold text-sm transition-colors shadow-sm w-full text-left focus:outline-none bg-mauve-700 hover:bg-mauve-500 text-gray-200";

    return (
        <button onClick={handleClick}
            disabled={disable}
            className={`${baseClasses} ${className}`}
        >
            <span>{text}</span>
        </button>
    )
}