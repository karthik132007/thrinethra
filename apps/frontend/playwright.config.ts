import { defineConfig } from "@playwright/test";
// Isolate acceptance tests from operator-controlled cameras and the normal app.
export default defineConfig({
  testDir:"./tests",testMatch:process.env.E2E_SYNTHETIC==="1"?"**/operations.spec.ts":"**/real-recordings.spec.ts",
  fullyParallel:false,workers:1,timeout:180000,
  use:{baseURL:"http://127.0.0.1:3001",viewport:{width:1440,height:1000},trace:"retain-on-failure"},
  reporter:[["list"],["json",{outputFile:"../../evaluations/playwright-results.json"}]],
  webServer:[
    {command:"../../.venv/bin/python ../../scripts/run_backend.py",url:"http://127.0.0.1:8001/api/v1/health",reuseExistingServer:false,timeout:120000,
      env:{API_PORT:"8001",DATABASE_URL:process.env.E2E_SYNTHETIC==="1"?"sqlite:///runtime/e2e-synthetic.db":"sqlite:///runtime/e2e-real.db",
        DEMO_MODE:"true",OPERATOR_TOKEN:"",SYNTHETIC_MODE:process.env.E2E_SYNTHETIC==="1"?"true":"false",CORS_ORIGINS:"http://127.0.0.1:3001",
        LLM_PROVIDER:process.env.CI?"none":"ollama"}},
    {command:"npm run dev -- --port 3001",url:"http://127.0.0.1:3001",reuseExistingServer:false,timeout:120000,
      env:{NEXT_DIST_DIR:".next-e2e",BACKEND_URL:"http://127.0.0.1:8001",NEXT_PUBLIC_WS_URL:"ws://127.0.0.1:8001/ws/live"}}
  ]
});
