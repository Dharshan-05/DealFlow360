// ==============================================================================
// DealFlow360 — PM2 Ecosystem Configuration
// Phase 468: Alternative Enterprise Process Management
// Run via: pm2 start deploy/pm2/ecosystem.config.js
// ==============================================================================

module.exports = {
  apps: [
    {
      name: "dealflow360-backend",
      cwd: "/opt/dealflow360/backend",
      script: "/opt/dealflow360/backend/.venv/bin/uvicorn",
      args: "app.main:app --host 127.0.0.1 --port 8000 --workers 4",
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: "1G",
      kill_timeout: 10000,
      env: {
        ENVIRONMENT: "production",
        DEBUG: "false",
      },
    },
    {
      name: "dealflow360-frontend",
      cwd: "/opt/dealflow360/frontend",
      script: "node_modules/.bin/next",
      args: "start -p 3000",
      instances: "max",
      exec_mode: "cluster",
      autorestart: true,
      watch: false,
      max_memory_restart: "1G",
      kill_timeout: 5000,
      env: {
        NODE_ENV: "production",
        PORT: 3000,
      },
    },
  ],
};
