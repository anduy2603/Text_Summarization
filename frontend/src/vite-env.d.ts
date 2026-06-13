/// <reference types="vite/client" />

declare module "@fontsource-variable/plus-jakarta-sans";
declare module "material-symbols/outlined.css";

interface ImportMetaEnv {
  readonly VITE_API_BASE?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
