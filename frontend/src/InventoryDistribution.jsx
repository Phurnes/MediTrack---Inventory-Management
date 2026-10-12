
import React, { useMemo } from "react";

const CATEGORY_INFO = {
  TABLET: { label: "Tablets", color: "#2563eb" },
  CAPSULE: { label: "Capsules", color: "#14b8a6" },
  SYRUP: { label: "Syrups", color: "#22c55e" },
  INJECTION: { label: "Injections", color: "#f59e0b" },
  OINTMENT: { label: "Ointments", color: "#8b5cf6" },
  DROPS: { label: "Drops", color: "#ec4899" },
  OTHER: { label: "Other", color: "#64748b" },
};

export default function InventoryDistribution({ medicines = [] }) {
  const categories = useMemo(() => {
    const totals = {};

    for (const medicine of medicines) {
      const category = String(medicine.category || "OTHER").toUpperCase();
      const quantity = Math.max(0, Number(medicine.quantity) || 0);

      totals[category] = (totals[category] || 0) + quantity;
    }

    return Object.entries(totals)
      .map(([key, quantity]) => ({
        key,
        label: CATEGORY_INFO[key]?.label || key,
        color: CATEGORY_INFO[key]?.color || CATEGORY_INFO.OTHER.color,
        quantity,
      }))
      .filter((item) => item.quantity > 0)
      .sort((a, b) => b.quantity - a.quantity);
  }, [medicines]);

  const totalStock = categories.reduce(
    (sum, category) => sum + category.quantity,
    0
  );

  let cumulativePercent = 0;

  const gradient = categories.map((category) => {
    const percent =
      totalStock > 0 ? (category.quantity / totalStock) * 100 : 0;

    const start = cumulativePercent;
    cumulativePercent += percent;

    return `${category.color} ${start}% ${cumulativePercent}%`;
  });

  return (
    <section className="distribution-card">
      <div className="distribution-heading">
        <div>
          <h3>Inventory Distribution</h3>
          <p>Stock breakdown by category</p>
        </div>

        <span className="distribution-icon" aria-hidden="true">
          ◉
        </span>
      </div>

      <div className="distribution-chart-area">
        <div
          className="distribution-donut"
          role="img"
          aria-label={`Inventory distribution. Total stock: ${totalStock} units.`}
          style={{
            background:
              totalStock > 0
                ? `conic-gradient(${gradient.join(", ")})`
                : "#e7eef2",
          }}
        >
          <div className="distribution-donut-hole">
            <span>Total Stock</span>
            <strong>{totalStock.toLocaleString()}</strong>
            <small>units</small>
          </div>
        </div>
      </div>

      {categories.length > 0 ? (
        <div className="distribution-legend">
          {categories.map((category) => {
            const percent =
              totalStock > 0
                ? (category.quantity / totalStock) * 100
                : 0;

            return (
              <div className="distribution-row" key={category.key}>
                <span
                  className="distribution-dot"
                  style={{ backgroundColor: category.color }}
                />

                <span className="distribution-category">
                  {category.label}
                </span>

                <span className="distribution-quantity">
                  {category.quantity.toLocaleString()}
                </span>

                <span className="distribution-percent">
                  {percent.toFixed(1)}%
                </span>
              </div>
            );
          })}
        </div>
      ) : (
        <p className="distribution-empty">
          No stock quantities available to display yet.
        </p>
      )}
    </section>
  );
}
