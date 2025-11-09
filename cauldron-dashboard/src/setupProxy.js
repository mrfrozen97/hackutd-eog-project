// src/setupProxy.js

const { createProxyMiddleware } = require('http-proxy-middleware');

module.exports = function(app) {
  app.use(
    '/api', // This is the path we want to proxy
    createProxyMiddleware({
      target: 'https://hackutd2025.eog.systems', // The real API server
      changeOrigin: true, // Needed for the target server to accept the request
    })
  );
};