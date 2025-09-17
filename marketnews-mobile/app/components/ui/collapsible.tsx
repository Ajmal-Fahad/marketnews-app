import React from "react";

/**
 * Minimal Collapsible placeholder used by the explore tab.
 */
export const Collapsible: React.FC<{ title?: string; children?: React.ReactNode }> = ({ children }) => {
  return <>{children}</>;
};
export default Collapsible;
