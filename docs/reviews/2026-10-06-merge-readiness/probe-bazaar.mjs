#!/usr/bin/env node
// All mutations use fresh audit fixtures; never edit or delete pre-existing data.
import { writeFileSync } from 'node:fs';
const BASE = process.env.BASE ?? 'http://127.0.0.1:3000';
const suffix = `audit-${Date.now()}`;
const observations = [];
async function call(path, { token, body, method = body ? 'POST' : 'GET' } = {}) {
  const response = await fetch(BASE + path, { method, headers: { ...(token ? { authorization: `Bearer ${token}` } : {}), ...(body ? { 'content-type': 'application/json' } : {}) }, body: body ? JSON.stringify(body) : undefined });
  return { status: response.status, body: await response.json() };
}
async function register(tenantName, role, key) {
  const result = await call('/auth/register', { body: { tenantName, role, email: `${key}-${suffix}@audit.invalid`, password: 'Audit-password-123' } });
  if (result.status !== 201) throw new Error(`audit register failed: ${result.status}`);
  return result.body;
}
const tenantName = `Private ${suffix}`;
const seller = await register(tenantName, 'seller', 'seller');
const buyer = await register(tenantName, 'buyer', 'buyer');
const created = await call('/auctions', { token: seller.token, body: { title: `Audit private lot ${suffix}`, reserveCents: 100, minIncrementCents: 10, closesAt: '2020-01-01T00:00:00Z' } });
if (created.status !== 201) throw new Error('audit listing failed');
const id = created.body.id;
const joining = await register(tenantName, 'admin', 'uninvited');
const visible = await call(`/auctions/${id}`, { token: joining.token });
observations.push({ check: 'uninvited tenant join and admin self-assignment', registrationRole: joining.role, sameTenant: joining.tenantId === seller.tenantId, privateListingStatus: visible.status, expected: 'unauthorized tenant membership/admin role must be refused' });

const ws = new WebSocket(`${BASE.replace('http', 'ws')}/ws?auctionId=${id}`);
const events = [];
ws.onmessage = event => events.push(JSON.parse(event.data));
await new Promise((resolve, reject) => { const timer = setTimeout(() => reject(new Error('ws timeout')), 3000); ws.onopen = () => { clearTimeout(timer); resolve(); }; ws.onerror = reject; });
const comment = await call(`/auctions/${id}/comments`, { token: seller.token, body: { body: 'Audit private comment' } });
await new Promise(resolve => setTimeout(resolve, 350));
observations.push({ check: 'anonymous websocket tenant data', commentStatus: comment.status, receivedPrivateCommentWithoutAuth: events.some(event => event.type === 'comment.posted' && event.body === 'Audit private comment'), expected: 'unauthenticated socket must not subscribe to tenant-private auction rooms' });
ws.close();
await call('/me/deposit', { token: buyer.token, body: { amountCents: 1000 } });
const bid = await call(`/auctions/${id}/bids`, { token: buyer.token, body: { amountCents: 200 } });
observations.push({ check: 'bid after closesAt', closesAt: created.body.closesAt, status: bid.status, expected: 'expired auction rejects bid' });
const settle = await call(`/auctions/${id}/settle`, { token: joining.token, method: 'POST' });
observations.push({ check: 'self-assigned admin settles another seller auction', status: settle.status, expected: 'uninvited user must not acquire settlement authority' });
const output = { target: BASE, fixtureTag: suffix, observations };
if (process.env.AUDIT_OUT) writeFileSync(process.env.AUDIT_OUT, JSON.stringify(output, null, 2) + '\n');
console.log(JSON.stringify(output, null, 2));
