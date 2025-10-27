// src/setupProxy.js
const { createProxyMiddleware } = require('http-proxy-middleware');
const { parse } = require('url');

const BACKEND_HOST = 'http://10.0.1.88:8000'; // máquina backend
const AGENTS_PROXY = 'http://10.0.1.69:80';   // máquina deploy (nginx-proxy)

function ensureAgentId(req, res, next) {
  const { query } = parse(req.url, true);
  const id = (query.agentID || '').toString();
  // Acepta solo letras, números, guion y guion_bajo para evitar inyección en Host
  if (!id || !/^[-_a-zA-Z0-9]+$/.test(id)) {
    res.statusCode = 400;
    return res.end('Missing or invalid agentID');
  }
  req.agentId = id;
  next();
}

module.exports = function (app) {
  // --- API normal ---
  app.use(
    '/api',
    createProxyMiddleware({
      target: BACKEND_HOST,
      changeOrigin: true,
      xfwd: true,
      pathRewrite: { '^/api': '' },
      timeout: 600000,
      proxyTimeout: 600000,
    })
  );

  // --- /agent?agentID=<uuid> ---
  app.use(
    '/agent',
    ensureAgentId, // valida y guarda req.agentId
    createProxyMiddleware({
      target: AGENTS_PROXY,
      changeOrigin: true,
      xfwd: true,
      // timeouts largos: los agentes pueden demorar (LLM)
      timeout: 600000,
      proxyTimeout: 600000,
      // Si usas HTTPS en deploy y cert self-signed: secure:false (no parece tu caso)
      // secure: false,

      // Reescribe SIEMPRE a /ask, conservando el resto de la query excepto agentID
      pathRewrite: (path, req) => {
        const { query } = parse(req.url, true);
        const qs = new URLSearchParams(query);
        qs.delete('agentID'); // no se lo pasamos al agente
        const rest = qs.toString();
        return `/ask${rest ? `?${rest}` : ''}`;
      },

      // Fuerza cabeceras que usa jwilder/nginx-proxy para elegir el contenedor
      onProxyReq: (proxyReq, req) => {
        const vhost = `agent_${req.agentId}`;
        // Host/authority para nginx
        proxyReq.setHeader('Host', vhost);           // mayúscula
        proxyReq.setHeader('host', vhost);           // y minúscula (seguro)
        // Adelanta trazabilidad
        proxyReq.setHeader('X-Forwarded-Host', vhost);
        proxyReq.setHeader('X-Original-Host', vhost);
        // Opcional: quita Origin si te causa CORS raros
        // proxyReq.removeHeader('origin');
      },

      // Útil para ver a dónde está apuntando realmente
      logLevel: 'warn',
    })
  );
};
