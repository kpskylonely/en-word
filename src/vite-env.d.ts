/// <reference types="vite/client" />

interface PyWebViewApi {
  set_stealth_mode: (
    enabled: boolean,
    alwaysOnTop?: boolean,
  ) => Promise<{ ok: boolean; supported: boolean }>;
}

declare global {
  interface Window {
    pywebview?: {
      api: PyWebViewApi;
    };
  }
}

declare module "*.vue" {
  import type { DefineComponent } from "vue";
  const component: DefineComponent<{}, {}, any>;
  export default component;
}

export {};
