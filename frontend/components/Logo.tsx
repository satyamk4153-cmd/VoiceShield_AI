import React from "react";

interface LogoProps {
  className?: string;
  size?: "sm" | "md" | "lg";
  showText?: boolean;
  showTagline?: boolean;
}

export const Logo: React.FC<LogoProps> = ({
  className = "",
  size = "md",
  showText = true,
  showTagline = false,
}) => {
  const sizeMap = {
    sm: { icon: 24, font: "text-base", sub: "text-[11px]" },
    md: { icon: 32, font: "text-lg", sub: "text-xs" },
    lg: { icon: 44, font: "text-2xl", sub: "text-sm" },
  };

  const { icon, font, sub } = sizeMap[size];

  return (
    <div className={`inline-flex items-center gap-2.5 ${className}`}>
      {/* Clean Shield with Waveform */}
      <svg
        width={icon}
        height={icon}
        viewBox="0 0 32 32"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="flex-shrink-0 text-blue-600"
      >
        {/* Shield outline / fill */}
        <path
          d="M16 3L5 7.5V14.5C5 21.6 9.8 28.2 16 29.8C22.2 28.2 27 21.6 27 14.5V7.5L16 3Z"
          fill="#2563EB"
        />
        {/* Subtle interior audio waveform bars */}
        <line x1="10" y1="14" x2="10" y2="18" stroke="#FFFFFF" strokeWidth="2" strokeLinecap="round" />
        <line x1="13" y1="11" x2="13" y2="21" stroke="#FFFFFF" strokeWidth="2" strokeLinecap="round" />
        <line x1="16" y1="9"  x2="16" y2="23" stroke="#FFFFFF" strokeWidth="2" strokeLinecap="round" />
        <line x1="19" y1="11" x2="19" y2="21" stroke="#FFFFFF" strokeWidth="2" strokeLinecap="round" />
        <line x1="22" y1="14" x2="22" y2="18" stroke="#FFFFFF" strokeWidth="2" strokeLinecap="round" />
      </svg>

      {showText && (
        <div className="flex flex-col leading-tight">
          <div className="flex items-center gap-1.5">
            <span className={`font-semibold tracking-tight text-slate-900 ${font}`}>
              VoiceShield
            </span>
            <span className={`font-semibold text-blue-600 ${font}`}>
              AI
            </span>
          </div>
          {showTagline && (
            <span className={`text-slate-500 font-normal ${sub}`}>
              Protect every voice.
            </span>
          )}
        </div>
      )}
    </div>
  );
};
