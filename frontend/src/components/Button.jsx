import React from "react";

export const Button = ({
  children,
  type = "button",
  onClick,
  className,
  small = false,
  destructive = false,
  variant = "contained",
}) => {
  const containedStyle = `${destructive ? "bg-red-700" : "bg-[#646cff]"}`;
  const outlinedStyle = `border border-[#646cff]`;
  const smallStyle = "px-2 py-1 text-sm rounded-md";

  return (
    <button
      type={type}
      onClick={onClick}
      className={`${className} ${
        variant === "outlined" ? outlinedStyle : containedStyle
      } ${
        small ? smallStyle : "p-4 rounded-lg "
      } text-white hover:bg-opacity-90 transition cursor-pointer`}
    >
      {children}
    </button>
  );
};
