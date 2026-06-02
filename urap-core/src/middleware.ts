import type { Request, Response, NextFunction, Router } from 'express';
import type { UrapConfig } from './types.js';

export function urapMiddleware(config: UrapConfig): Router {
  // eslint-disable-next-line @typescript-eslint/no-require-imports
  const { Router } = require('express');
  const router: Router = Router();

  const engineUrl = config.engineUrl ?? 'http://localhost:8080';

  function engineHeaders(extra: Record<string, string> = {}): Record<string, string> {
    return {
      'Content-Type': 'application/json',
      'x-tenant-id': config.tenantId,
      'x-api-key': config.apiKey,
      ...extra,
    };
  }

  async function proxy(
    enginePath: string,
    method: string,
    req: Request,
    res: Response,
    next: NextFunction,
    body?: unknown,
  ): Promise<void> {
    try {
      const init: RequestInit = {
        method,
        headers: engineHeaders(),
      };
      if (body !== undefined) {
        init.body = JSON.stringify(body);
      }
      const response = await fetch(`${engineUrl}${enginePath}`, init);
      const data = await response.json();
      res.status(response.status).json(data);
    } catch (err) {
      next(err);
    }
  }

  // ── Status ──────────────────────────────────────────────────────────────────

  router.get('/status', (_req: Request, res: Response) => {
    res.json({ status: 'ok', tenantId: config.tenantId, version: '0.1.0' });
  });

  // ── Lead capture & ping-post distribution ───────────────────────────────────

  router.post('/leads/capture', (req: Request, res: Response, next: NextFunction) => {
    proxy('/leads/capture', 'POST', req, res, next, req.body);
  });

  router.get('/leads/preview/:preview_id', (req: Request, res: Response, next: NextFunction) => {
    proxy(`/leads/preview/${req.params.preview_id}`, 'GET', req, res, next);
  });

  router.post('/leads/claim', (req: Request, res: Response, next: NextFunction) => {
    proxy('/leads/claim', 'POST', req, res, next, req.body);
  });

  router.get('/leads/recent', (req: Request, res: Response, next: NextFunction) => {
    proxy('/leads/recent', 'GET', req, res, next);
  });

  // ── Outreach channel events (webhook callbacks from SMTP2GO, Twilio, etc.) ──

  router.post('/webhooks/:module', (req: Request, res: Response, next: NextFunction) => {
    proxy(`/webhook/${req.params.module}`, 'POST', req, res, next, req.body);
  });

  router.post('/outreach/event', (req: Request, res: Response, next: NextFunction) => {
    proxy('/outreach/channel/event', 'POST', req, res, next, req.body);
  });

  // ── Consent recording (public — no key required on engine side) ────────────

  router.post('/consent', (req: Request, res: Response, next: NextFunction) => {
    proxy('/consent/record', 'POST', req, res, next, {
      ...req.body,
      tenant_id: config.tenantId,
    });
  });

  // ── Embed snippet ──────────────────────────────────────────────────────────

  router.get('/embed.js', (_req: Request, res: Response) => {
    const { generateEmbedSnippet } = require('./embed.js');
    const snippet: string = generateEmbedSnippet({
      captureUrl: `/urap/leads/capture`,
      consentUrl: `/urap/consent`,
      tenantId: config.tenantId,
    });
    res.setHeader('Content-Type', 'application/javascript');
    res.send(snippet);
  });

  return router;
}
