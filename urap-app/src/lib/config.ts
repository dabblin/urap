const isLocalhost = typeof window !== 'undefined' && window.location.hostname === 'localhost';

export const ENGINE = import.meta.env.VITE_ENGINE_URL || (isLocalhost ? 'http://localhost:8080' : 'https://urap-engine.run.app');
export const TENANT = import.meta.env.VITE_TENANT_ID ?? 'dev-tenant';
