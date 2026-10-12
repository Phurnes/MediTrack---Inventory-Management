
import { test, expect } from "@playwright/test";

const API = "http://127.0.0.1:8000/api";

test("Medicine API responds successfully", async ({ request }) => {
  const response = await request.get(`${API}/medicines/`);

  expect(response.status()).toBe(200);

  const data = await response.json();
  expect(data).toBeTruthy();

  // Support either a plain list or a paginated DRF response.
  const medicines = Array.isArray(data) ? data : data.results;

  expect(Array.isArray(medicines)).toBe(true);

  console.log(`Medicine API returned ${medicines.length} records.`);
});

test("Stock Planner API returns its required fields", async ({ request }) => {
  const response = await request.get(`${API}/planner/`);

  expect(response.status()).toBe(200);

  const plan = await response.json();

  expect(plan).toHaveProperty("generated_on");
  expect(plan).toHaveProperty("total_medicines");
  expect(plan).toHaveProperty("medicines_to_reorder");
  expect(plan).toHaveProperty("total_suggested_units");
  expect(plan).toHaveProperty("items");

  expect(Array.isArray(plan.items)).toBe(true);
  expect(plan.total_medicines).toBe(plan.items.length);

  for (const item of plan.items) {
    expect(item).toHaveProperty("usable_stock");
    expect(item).toHaveProperty("expired_stock");
    expect(item).toHaveProperty("expiring_soon_stock");
    expect(item).toHaveProperty("suggested_order");
    expect(item).toHaveProperty("priority");

    expect(item.usable_stock).toBeGreaterThanOrEqual(0);
    expect(item.expired_stock).toBeGreaterThanOrEqual(0);
    expect(item.expiring_soon_stock).toBeGreaterThanOrEqual(0);
    expect(item.suggested_order).toBeGreaterThanOrEqual(0);
  }
});
