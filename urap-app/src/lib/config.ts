const isLocalhost = typeof window !== 'undefined' && window.location.hostname === 'localhost';

export const ENGINE = import.meta.env.VITE_ENGINE_URL || (isLocalhost ? 'http://localhost:8080' : 'https://urap-engine-93588831679.us-central1.run.app');
export const TENANT = import.meta.env.VITE_TENANT_ID ?? 'dev-tenant';
